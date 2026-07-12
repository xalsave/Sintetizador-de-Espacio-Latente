// SintetizadorEspacioLatente.cpp
// -----------------------------------------------------------------------------
// Sesion 7 (MVP end-to-end): el Daisy recibe wavetables por SPI y las reproduce.
//
// Cambio respecto a S5: la fuente de tablas ya NO es el timer con ondas de
// prueba (seno/sierra/cuadrada); ahora cada wavetable llega por SPI desde el
// ESP32-S3 (una por cada toque tactil, ya interpolada en el S3). El MOTOR de
// wavetables con doble buffer + crossfade de 20 ms (clase Wavetable) es EL MISMO
// de S5, sin tocar: solo cambia quien llama a LoadNext().
//
// Enlace SPI (docs/spi.md seccion 2): S3 maestro, Daisy esclavo SPI_1 con
// DMA, 10 MHz, modo 0, MSB first. Trama de 2054 bytes:
//   byte 0..1     : header 0xDE 0xAD
//   byte 2..3     : seq_id  uint16 little-endian
//   byte 4..2051  : payload 1024 muestras int16 little-endian (Q15)
//   byte 2052..53 : CRC16/CCITT-FALSE sobre el payload, little-endian
// -----------------------------------------------------------------------------

#include "daisy_seed.h"
#include <cmath>
#include <cstring>   // memcpy

using namespace daisy;

DaisySeed hw;

// Poner a 1 para volcar por USB serie las 1024 muestras de cada tabla recibida
// (WAVE_BEGIN..WAVE_END), para la validacion cruzada con 7_validate_spi.py.
// Poner a 0 para el uso normal del instrumento (solo suena).
#define SPI_DEBUG_DUMP 1

// --------------------------------------------------------------------------- //
// Configuracion
// --------------------------------------------------------------------------- //
static const int   TABLE_LEN   = 1024;     // muestras por ciclo (igual que el grid)
static const float SAMPLE_RATE = 48000.f;  // Hz, codec del Daisy
static const float NOTE_HZ     = 220.f;    // tono de prueba (La3). Grave-ish para
                                           // oir bien el cambio de timbre.
static const float XFADE_MS    = 20.f;     // duracion del crossfade. PROBAR 5/10/20.
static const float OUT_GAIN    = 0.4f;     // ganancia de salida (sin envolvente aun)


// --------------------------------------------------------------------------- //
// Motor wavetable: doble buffer + acumulador de fase + crossfade
// --------------------------------------------------------------------------- //
// (IDENTICO a la sesion 5: cerrado y validado por el oido. No se toca. La unica
//  diferencia en S7 es que LoadNext() se llama al recibir una tabla por SPI en
//  vez de con un timer de prueba.)
// Las tablas se guardan en Q15 (int16), igual que el grid exportado por
// 4_bake_grid.py (decision 13). Asi este motor consume exactamente el formato
// que recibira por SPI sin conversiones extra.
class Wavetable
{
  public:
    void Init(float sample_rate)
    {
        sample_rate_ = sample_rate;
        phase_       = 0.f;
        phase_inc_   = 0.f;
        xfade_pos_   = 1.f;   // 1.0 = solo tabla activa (sin crossfade en curso)
        // Incremento del crossfade por muestra: recorre 0 -> 1 en XFADE_MS.
        xfade_inc_   = 1.f / (sample_rate_ * (XFADE_MS / 1000.f));
        // Arranca con silencio en ambos buffers por si NextSample corre antes
        // de cargar nada.
        std::memset(table_active_, 0, sizeof(table_active_));
        std::memset(table_next_,   0, sizeof(table_next_));
    }

    // Frecuencia de reproduccion (Hz). phase_inc_ en "muestras de tabla / muestra".
    void SetFreq(float hz) { phase_inc_ = hz * TABLE_LEN / sample_rate_; }

    // Carga la primera tabla SIN crossfade (para el arranque).
    void SetActiveNow(const int16_t* src)
    {
        std::memcpy(table_active_, src, sizeof(table_active_));
        xfade_pos_ = 1.f;  // nada que mezclar
    }

    // Pide cambiar de tabla: copia la nueva al buffer "next" y arranca el
    // crossfade. Se llama SIEMPRE desde fuera del callback (loop principal o,
    // mas adelante, al recibir una tabla por SPI). El orden importa: primero se
    // copia entera la tabla y SOLO al final se pone xfade_pos_ = 0, que es la
    // unica condicion que hace que el callback empiece a leer table_next_.
    // Asi no se lee un buffer a medio escribir.
    void LoadNext(const int16_t* src)
    {
        std::memcpy(table_next_, src, sizeof(table_next_));
        xfade_pos_ = 0.f;  // dispara el crossfade (poner esto el ULTIMO)
    }

    // Genera la siguiente muestra. Real-time safe: solo aritmetica y lecturas.
    float NextSample()
    {
        // --- Interpolacion lineal entre muestras (suaviza el aliasing de pitch)
        uint32_t idx0 = (uint32_t)phase_;
        uint32_t idx1 = (idx0 + 1) & (TABLE_LEN - 1);
        float    frac = phase_ - (float)idx0;

        float s_active = (table_active_[idx0] * (1.f - frac)
                        + table_active_[idx1] * frac) / 32768.f;

        float out;
        if(xfade_pos_ < 1.f)
        {
            // Crossfade en curso: misma fase en ambas tablas, se mezclan.
            float s_next = (table_next_[idx0] * (1.f - frac)
                          + table_next_[idx1] * frac) / 32768.f;
            out = s_active * (1.f - xfade_pos_) + s_next * xfade_pos_;

            // Avanzar el crossfade
            xfade_pos_ += xfade_inc_;
            if(xfade_pos_ >= 1.f)
            {
                // Crossfade terminado: la tabla "next" pasa a ser la activa.
                std::memcpy(table_active_, table_next_, sizeof(table_active_));
                xfade_pos_ = 1.f;
            }
        }
        else
        {
            out = s_active;
        }

        // --- Avance del acumulador de fase
        phase_ += phase_inc_;
        if(phase_ >= (float)TABLE_LEN) phase_ -= (float)TABLE_LEN;

        return out;
    }

  private:
    float   sample_rate_;
    int16_t table_active_[TABLE_LEN];
    int16_t table_next_[TABLE_LEN];
    float   phase_;
    float   phase_inc_;
    float   xfade_pos_;   // 1.0 = solo activa; durante el crossfade va 0 -> 1
    float   xfade_inc_;
};

Wavetable osc;


// --------------------------------------------------------------------------- //
// Recepcion SPI (S7): esclavo SPI_1 + DMA
// --------------------------------------------------------------------------- //
static const int SPI_SAMPLES   = 1024;
static const int SPI_PAYLOAD   = SPI_SAMPLES * 2;   // 2048 bytes
static const int SPI_FRAME_LEN = SPI_PAYLOAD + 6;   // 2054 bytes (header+seq+crc)

SpiHandle spi;

// El buffer de recepcion DMA debe vivir en RAM accesible por el DMA (SRAM1).
static uint8_t DMA_BUFFER_MEM_SECTION spi_rx_buffer[SPI_FRAME_LEN];
// Payload ya desempaquetado a int16, listo para LoadNext().
static int16_t spi_wave[SPI_SAMPLES];

static volatile bool     spi_dma_done = false;  // lo pone la ISR de fin de DMA
static volatile uint32_t spi_frames   = 0;      // tramas validas totales (debug)

// Prototipo (la ISR re-arma la recepcion en caso de error).
void OnSpiComplete(void* context, SpiHandle::Result result);

// CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF). Identico al del S3
// (spi_sender.cpp) y a 7_validate_spi.py, para poder comparar el CRC bit a bit.
static uint16_t crc16_ccitt(const uint8_t* data, int len)
{
    uint16_t crc = 0xFFFF;
    for(int i = 0; i < len; ++i) {
        crc ^= (uint16_t)data[i] << 8;
        for(int b = 0; b < 8; ++b)
            crc = (crc & 0x8000) ? (uint16_t)((crc << 1) ^ 0x1021)
                                 : (uint16_t)(crc << 1);
    }
    return crc;
}

// Callback de fin de DMA (se ejecuta en interrupcion). Se mantiene minimo: solo
// señaliza que hay una trama en spi_rx_buffer. La validacion (header+CRC) y la
// copia de 2 KB se hacen en el loop principal, y solo despues se re-arma el DMA;
// asi no se sobrescribe el buffer antes de leerlo ni se recarga la ISR.
void OnSpiComplete(void* context, SpiHandle::Result result)
{
    (void)context;
    if(result == SpiHandle::Result::OK)
        spi_dma_done = true;
    else
        // Error de DMA: re-armar sin perturbar el audio.
        spi.DmaReceive(spi_rx_buffer, SPI_FRAME_LEN, nullptr, OnSpiComplete, nullptr);
}

static void spi_slave_init()
{
    SpiHandle::Config c;
    c.periph         = SpiHandle::Config::Peripheral::SPI_1;
    c.mode           = SpiHandle::Config::Mode::SLAVE;
    c.direction      = SpiHandle::Config::Direction::TWO_LINES_RX_ONLY;
    c.datasize       = 8;
    c.clock_polarity = SpiHandle::Config::ClockPolarity::LOW;   // CPOL=0
    c.clock_phase    = SpiHandle::Config::ClockPhase::ONE_EDGE; // CPHA=0 -> modo 0
    c.nss            = SpiHandle::Config::NSS::HARD_INPUT;      // CS por hardware (D7)
    c.pin_config.sclk = {DSY_GPIOG, 11};  // D8
    c.pin_config.miso = {DSY_GPIOB, 4};   // D9  (sin uso en RX_ONLY)
    c.pin_config.mosi = {DSY_GPIOB, 5};   // D10
    c.pin_config.nss  = {DSY_GPIOG, 10};  // D7
    spi.Init(c);

    // Primera recepcion armada; a partir de aqui el ciclo lo mantiene el loop.
    spi.DmaReceive(spi_rx_buffer, SPI_FRAME_LEN, nullptr, OnSpiComplete, nullptr);
}

#if SPI_DEBUG_DUMP
// Volcado compatible con el parser de 6_validate_s3.py / 7_validate_spi.py.
static void dump_wave(const int16_t* w)
{
    hw.PrintLine("WAVE_BEGIN");
    for(int n = 0; n < SPI_SAMPLES; ++n)
        hw.PrintLine("%d", (int)w[n]);
    hw.PrintLine("WAVE_END");
}
#endif

// Procesa una trama recibida (llamado desde el loop principal, fuera de la ISR).
// Valida header + CRC; si es correcta, desempaqueta el payload y dispara el
// crossfade con LoadNext(). Luego re-arma la recepcion DMA.
static void spi_process_frame()
{
    bool     ok  = (spi_rx_buffer[0] == 0xDE && spi_rx_buffer[1] == 0xAD);
    uint16_t seq = (uint16_t)(spi_rx_buffer[2] | (spi_rx_buffer[3] << 8));

    if(ok)
    {
        uint16_t crc_rx   = (uint16_t)(spi_rx_buffer[4 + SPI_PAYLOAD]
                                    | (spi_rx_buffer[4 + SPI_PAYLOAD + 1] << 8));
        uint16_t crc_calc = crc16_ccitt(spi_rx_buffer + 4, SPI_PAYLOAD);
        ok = (crc_rx == crc_calc);
        if(ok)
        {
            // Payload int16 LE -> int16 nativo (STM32 tambien es LE: copia directa).
            std::memcpy(spi_wave, spi_rx_buffer + 4, SPI_PAYLOAD);
            osc.LoadNext(spi_wave);   // mismo crossfade de S5
            spi_frames++;
        }
    }

    // Re-armar la recepcion ANTES de imprimir (el volcado es lento y no debe
    // frenar la siguiente trama mas de lo imprescindible).
    spi_dma_done = false;
    spi.DmaReceive(spi_rx_buffer, SPI_FRAME_LEN, nullptr, OnSpiComplete, nullptr);

    if(ok)
    {
        hw.SetLed(true);   // parpadeo: trama valida aplicada
        // Resumen barato (una linea) para casar seq con el lado del S3.
        int16_t vmin = 32767, vmax = -32768;
        for(int n = 0; n < SPI_SAMPLES; ++n) {
            if(spi_wave[n] < vmin) vmin = spi_wave[n];
            if(spi_wave[n] > vmax) vmax = spi_wave[n];
        }
        hw.PrintLine("# SPI ok seq=%u frames=%u min=%d max=%d s0=%d s512=%d",
                     seq, (unsigned)spi_frames, (int)vmin, (int)vmax,
                     (int)spi_wave[0], (int)spi_wave[512]);
#if SPI_DEBUG_DUMP
        dump_wave(spi_wave);   // 1024 lineas: solo durante validacion (1 coord fija)
#endif
    }
    else
    {
        hw.PrintLine("# SPI DESCARTADA seq=%u (header/CRC)", seq);
    }
}


// --------------------------------------------------------------------------- //
// Callback de audio (regla critica: nada de malloc/printf/bloqueos)
// --------------------------------------------------------------------------- //
void AudioCallback(AudioHandle::InterleavingInputBuffer  in,
                   AudioHandle::InterleavingOutputBuffer out,
                   size_t size)
{
    for(size_t i = 0; i < size; i += 2)
    {
        float s = osc.NextSample() * OUT_GAIN;
        out[i]     = s;  // L
        out[i + 1] = s;  // R
    }
}

// --------------------------------------------------------------------------- //
// main
// --------------------------------------------------------------------------- //
int main(void)
{
    hw.Init();
    hw.SetAudioBlockSize(48);
    hw.StartLog(false);   // USB serie para depurar (no espera al PC)

    osc.Init(hw.AudioSampleRate());
    osc.SetFreq(NOTE_HZ);
    // Sin tabla inicial: ambos buffers a silencio (Init los pone a 0). El primer
    // frame SPI hara un fundido de entrada de 20 ms desde el silencio.

    spi_slave_init();
    hw.StartAudio(AudioCallback);

    uint32_t last_blink = System::GetNow();

    while(true)
    {
        // Una trama SPI lista -> validar y (si procede) cargar con crossfade.
        if(spi_dma_done)
            spi_process_frame();

        // Apagar el LED 100 ms despues del ultimo parpadeo de trama valida.
        if(System::GetNow() - last_blink >= 100)
        {
            hw.SetLed(false);
            last_blink = System::GetNow();
        }

        System::Delay(1);
    }
}
