// SintetizadorEspacioLatente.cpp
// -----------------------------------------------------------------------------
// BLOQUE B (20 ago 2026): panel de control analogico sobre lo ya validado.
//
//   - 6 potenciometros por ADC: A, D, S, R del envolvente (sustituyen a las
//     constantes fijas de S8) + cutoff y resonancia de un filtro daisysp::Svf.
//   - Selector ON-OFF-ON de tipo de filtro (LPF / BPF / HPF) leido por ADC.
//   - OLED SSD1306 por I2C (pines fisicos 12 y 13) mostrando en grande el
//     parametro que se esta tocando y, fijo abajo, el tipo de filtro.
//
// La cadena de audio pasa de  osc -> ADSR  a  osc -> Svf -> ADSR  (orden clasico
// de sintesis sustractiva: VCO -> VCF -> VCA).
//
// Los pines NO se han elegido aqui: vienen fijados por docs/veroboard.md
// seccion 2, que es la especificacion de la placa definitiva. Este firmware se
// construye CONTRA ese pinout, no al reves.
//
// Correspondencia pin fisico del Daisy -> argumento de hw.GetPin() (numeracion
// "D" de libDaisy). NO coinciden, y confundirlos es cablear otro pin:
//
//   fisico 22 (PC0)  A0  = D15  Attack       fisico 32 (PA0)  A10 = D25  Cutoff
//   fisico 23 (PA3)  A1  = D16  Decay        fisico 27 (PC1)  A5  = D20  Q
//   fisico 30 (PA4)  A8  = D23  Sustain      fisico 29 (PA5)  A7  = D22  Selector
//   fisico 31 (PA1)  A9  = D24  Release      fisico 21        3V3A (alimenta potes)
//   fisico 12 (PB8)  SCL = D11  OLED         fisico 13 (PB9)  SDA = D12  OLED
//
// REMAPEO DEL 27 AGO 2026: el trazado de la veroboard se calco en espejo y los
// cortes ya taladrados impedian llevar cuatro cursores a sus pines originales,
// asi que se adapto el firmware a la placa en vez de rehacerla. Cambian S, R,
// cutoff y selector (24/25/26/28 -> 30/31/32/29); attack, decay y Q se quedan.
// Q volvio a la tira 26 (pin 27, A5) porque los pines 33 y 34 son los UNICOS
// del bloque 29-35 sin canal de ADC. Los pines 29 y 30 son ademas DAC OUT 2 y
// DAC OUT 1, pero ConfigureDac() de libDaisy esta comentado entero, asi que
// seed.Init() no los reclama y quedan libres para el ADC. Verificado tambien
// que PA5/PA4/PA1/PA0 estan en adcpins[] de libDaisy/src/per/adc.cpp
// (canales 19, 18, 17 y 16). Los pines 24, 25, 28, 29 y 30 son solo tolerantes
// a 3,3 V: los potes cuelgan de 3V3A, asi que no hay conflicto.
//
// (En la columna derecha del conector, fisico = D + 7. Verificado contra la
//  tabla seedgpio[] de libDaisy/src/daisy_seed.cpp.)
//
// NO se ha tocado: el receptor SPI (S7), el motor Wavetable con crossfade (S5),
// la voz monofonica MIDI ni la pila de notas (S8).
// -----------------------------------------------------------------------------
// Sesion 8 (MIDI): el Keystep MK2 controla la NOTA (pitch/gate) del Daisy por
// MIDI DIN -> Shield 6N138 -> USART1 (D13 Tx / D14 Rx). El TIMBRE lo sigue
// controlando el toque en la CYD via SPI (MVP de S7, sin tocar).
//
// Dos fuentes de control independientes que conviven sin pisarse:
//   - MIDI  -> osc.SetFreq()   (frecuencia de reproduccion, una voz monofonica)
//   - CYD/SPI -> osc.LoadNext() (contenido de la wavetable, crossfade de S5)
//
// Voz monofonica con prioridad "ultima nota" y pila de notas pulsadas: al soltar
// una tecla se vuelve a la anterior que siga pulsada. Envolvente ADSR completa
// (daisysp::Adsr): Note On dispara el ataque, Note Off el release.
//
// NO se ha tocado nada del receptor SPI (S7, DMA + CRC, validado a 0 LSB) ni del
// motor Wavetable con doble buffer + crossfade de 20 ms (S5). Solo se anade la
// lectura MIDI en paralelo y la envolvente en el callback de audio.
//
// Enlace SPI (docs/spi.md seccion 2): S3 maestro, Daisy esclavo SPI_1 con
// DMA, 10 MHz, modo 0, MSB first. Trama de 2054 bytes:
//   byte 0..1     : header 0xDE 0xAD
//   byte 2..3     : seq_id  uint16 little-endian
//   byte 4..2051  : payload 1024 muestras int16 little-endian (Q15)
//   byte 2052..53 : CRC16/CCITT-FALSE sobre el payload, little-endian
// -----------------------------------------------------------------------------

#include "daisy_seed.h"
#include "daisysp.h"   // daisysp::Adsr, daisysp::Svf (DaisySP enlazada, -ldaisysp)
#include <cmath>       // powf, fabsf
#include <cstring>     // memcpy
#include <cstdio>      // snprintf (solo para las lineas del OLED)

using namespace daisy;

DaisySeed hw;

// Poner a 1 para volcar por USB serie las 1024 muestras de cada tabla recibida
// (WAVE_BEGIN..WAVE_END), para la validacion cruzada con 7_validate_spi.py.
// En S8 se deja a 0: el uso normal es tocar MIDI mientras se mueve el timbre, y
// el volcado de 1024 lineas por trama ahogaria los logs MIDI del serie.
#define SPI_DEBUG_DUMP 0

// Volcado por serie de la tabla nota->Hz->phase_inc al arrancar (y cada 3 s),
// para 8_validate_midi.py. Poner a 0 para el uso normal del instrumento.
#define MIDI_SELFTEST 0

// Log por serie de cada Note On / Note Off en vivo (nota, Hz, phase_inc, notas
// pulsadas). Util para ver con el Keystep que la conversion es correcta.
#define MIDI_DEBUG 1

// Traza de arranque (una linea por fase de init) + latido cada 2 s con los
// contadores. Sin esto, un firmware colgado a mitad de main() y un firmware vivo
// sin entrada son INDISTINGUIBLES por el serie: los dos callan. La traza dice
// hasta donde llego el arranque; el latido distingue "vivo esperando" de "muerto".
#define HEARTBEAT 1

// Direccion I2C del OLED. Casi todos los SSD1306 de 0.96" son 0x3C; algunos
// clones vienen a 0x3D (suele ir serigrafiado o depender de un puente).
#define OLED_ADDR 0x3C

// --------------------------------------------------------------------------- //
// Configuracion
// --------------------------------------------------------------------------- //
static const int   TABLE_LEN   = 1024;     // muestras por ciclo (igual que el grid)
static const float SAMPLE_RATE = 48000.f;  // Hz, codec del Daisy (nominal)
static const float NOTE_HZ     = 220.f;    // tono por defecto antes del primer MIDI
static const float XFADE_MS    = 20.f;     // duracion del crossfade (S5)
// Ganancia de salida global. 0.8 (antes 0.4) para no tener que compensar con el
// previo de la interfaz: subir la ganancia aguas abajo amplifica senal Y ruido por
// igual, subirla aqui solo amplifica la senal. Sin riesgo de recorte: el crossfade
// es una media ponderada y no anade ganancia, asi que el pico maximo es 0.8.
static const float OUT_GAIN    = 0.8f;

// Envolvente ADSR (segundos / nivel 0..1). Desde el bloque B son solo los valores
// de ARRANQUE: el ADSR queda gobernado por los cuatro potes en cuanto llega la
// primera lectura del ADC, unos milisegundos despues.
static const float ADSR_ATTACK  = 0.005f;  // 5 ms
static const float ADSR_DECAY   = 0.10f;   // 100 ms
static const float ADSR_SUSTAIN = 0.70f;   // 70 %
static const float ADSR_RELEASE = 0.20f;   // 200 ms

// Pila de notas pulsadas para la prioridad "ultima nota".
static const int MAX_HELD = 16;

// Suavizado de la ganancia de velocity, coeficiente de un polo por muestra
// (~5 ms a 48 kHz). Sin el, tocar una nota nueva mientras suena otra provoca un
// salto de ganancia sobre una senal que no esta en cero (el reataque es "soft",
// el ADSR no baja a 0) y eso se oye como un click.
static const float VEL_SMOOTH = 0.004f;


// --------------------------------------------------------------------------- //
// Motor wavetable: doble buffer + acumulador de fase + crossfade
// --------------------------------------------------------------------------- //
// (IDENTICO a la sesion 5/7: cerrado y validado. No se toca. En S8 sigue igual:
//  MIDI solo llama a SetFreq(); LoadNext() lo sigue llamando el SPI.)
class Wavetable
{
  public:
    void Init(float sample_rate)
    {
        sample_rate_ = sample_rate;
        phase_       = 0.f;
        phase_inc_   = 0.f;
        xfade_pos_   = 1.f;   // 1.0 = solo tabla activa (sin crossfade en curso)
        xfade_inc_   = 1.f / (sample_rate_ * (XFADE_MS / 1000.f));
        std::memset(table_active_, 0, sizeof(table_active_));
        std::memset(table_next_,   0, sizeof(table_next_));
    }

    // Frecuencia de reproduccion (Hz). phase_inc_ en "muestras de tabla / muestra".
    void SetFreq(float hz) { phase_inc_ = hz * TABLE_LEN / sample_rate_; }

    void SetActiveNow(const int16_t* src)
    {
        std::memcpy(table_active_, src, sizeof(table_active_));
        xfade_pos_ = 1.f;
    }

    void LoadNext(const int16_t* src)
    {
        std::memcpy(table_next_, src, sizeof(table_next_));
        xfade_pos_ = 0.f;  // dispara el crossfade (poner esto el ULTIMO)
    }

    float NextSample()
    {
        uint32_t idx0 = (uint32_t)phase_;
        uint32_t idx1 = (idx0 + 1) & (TABLE_LEN - 1);
        float    frac = phase_ - (float)idx0;

        float s_active = (table_active_[idx0] * (1.f - frac)
                        + table_active_[idx1] * frac) / 32768.f;

        float out;
        if(xfade_pos_ < 1.f)
        {
            float s_next = (table_next_[idx0] * (1.f - frac)
                          + table_next_[idx1] * frac) / 32768.f;
            out = s_active * (1.f - xfade_pos_) + s_next * xfade_pos_;

            xfade_pos_ += xfade_inc_;
            if(xfade_pos_ >= 1.f)
            {
                std::memcpy(table_active_, table_next_, sizeof(table_active_));
                xfade_pos_ = 1.f;
            }
        }
        else
        {
            out = s_active;
        }

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
    float   xfade_pos_;
    float   xfade_inc_;
};

Wavetable osc;


// Tabla senoidal de arranque. Sin esto las dos tablas quedan a cero tras Init() y
// el Daisy es MUDO hasta que llega la primera trama SPI valida del S3, aunque el
// MIDI funcione: un falso negativo caro de diagnosticar. Con ella, el Daisy es un
// instrumento autonomo (nota por MIDI, timbre senoidal) y el SPI solo *sustituye*
// el timbre. Permite validar MIDI+audio aislado del SPI, y no toca ni el receptor
// SPI (S7) ni el crossfade (S5): solo carga el buffer activo antes de StartAudio.
static int16_t boot_wave[TABLE_LEN];

static void make_boot_wave()
{
    for(int n = 0; n < TABLE_LEN; ++n)
    {
        float ph      = 2.f * (float)M_PI * (float)n / (float)TABLE_LEN;
        boot_wave[n]  = (int16_t)(32767.f * sinf(ph));
    }
}


// --------------------------------------------------------------------------- //
// MIDI (S8): USART1 -> voz monofonica last-note + ADSR
// --------------------------------------------------------------------------- //
MidiUartHandler midi;
daisysp::Adsr   env;

// Estado compartido loop <-> callback de audio. La escritura es de una sola
// palabra (bool / float dentro de SetFreq) y el callback solo lee: una carrera
// deja el cambio como mucho un bloque tarde (~1 ms), inaudible. El reataque del
// ADSR se aplaza a un flag para que TODA mutacion de env ocurra en el hilo de
// audio (Retrigger no es re-entrante con Process).
static volatile bool midi_gate          = false;  // true mientras haya tecla pulsada
static volatile bool midi_retrigger_req = false;  // pedir reataque del ADSR

// Ganancia pedida por la velocity de la nota que suena (0..1). La aplica el
// callback de audio a traves de un suavizado; ver VEL_SMOOTH.
static volatile float midi_vel_gain = 1.f;

// Pila de notas pulsadas (indice 0 = mas antigua, held_count-1 = cima = sonando).
// held_vels guarda la velocity de cada una EN PARALELO: al soltar una tecla y
// volver a la anterior hay que recuperar tambien su dinamica, no solo su tono.
static uint8_t held_notes[MAX_HELD];
static uint8_t held_vels[MAX_HELD];
static int     held_count = 0;

// Velocity MIDI (1..127) -> ganancia (0..1), curva cuadratica. Lineal repartiria
// casi todo el rango util en la mitad alta del recorrido de la tecla; al elevar al
// cuadrado, la dinamica se reparte de forma mas parecida a como se percibe la
// sonoridad. Para respuesta lineal, devolver v en vez de v*v.
static inline float vel_to_gain(uint8_t vel)
{
    float v = (float)vel / 127.f;
    return v * v;
}

// Contador de eventos MIDI de CUALQUIER tipo (incluidos los que se ignoran, como
// CC o reloj). Sirve para distinguir "no llega nada por el cable" de "llega pero
// no son notas": si esto sube al mover la rueda del Keystep, la cadena electrica
// funciona y el problema estaria en el tratamiento de las notas.
static volatile uint32_t midi_events = 0;

// Conversion nota MIDI -> Hz. Identica a daisysp::mtof (2^((m-69)/12)*440).
// UNICA fuente de verdad: la usan tanto el runtime como el volcado de MIDI_SELFTEST,
// asi que la tabla que valida 8_validate_midi.py es exactamente la del sonido real.
static inline float note_to_hz(int note)
{
    return 440.0f * powf(2.0f, ((float)note - 69.0f) / 12.0f);
}

// Quita una nota de la pila (si esta), compactando el hueco.
static void stack_remove(uint8_t note)
{
    for(int i = 0; i < held_count; ++i)
    {
        if(held_notes[i] == note)
        {
            for(int j = i; j < held_count - 1; ++j)
            {
                held_notes[j] = held_notes[j + 1];
                held_vels[j]  = held_vels[j + 1];
            }
            held_count--;
            return;
        }
    }
}

static void handle_note_off(uint8_t note);

static void handle_note_on(uint8_t note, uint8_t vel)
{
    if(vel == 0)  // Note On con velocity 0 = Note Off (running status)
    {
        handle_note_off(note);
        return;
    }

    stack_remove(note);                          // evita duplicados en la pila
    if(held_count < MAX_HELD)                    // nueva cima
    {
        held_notes[held_count] = note;
        held_vels[held_count]  = vel;
        held_count++;
    }

    float hz = note_to_hz(note);
    osc.SetFreq(hz);
    midi_vel_gain      = vel_to_gain(vel);
    midi_gate          = true;
    midi_retrigger_req = true;                    // reataque en CADA Note On nuevo

#if MIDI_DEBUG
    float pinc = hz * TABLE_LEN / SAMPLE_RATE;
    hw.PrintLine("# NOTE_ON  note=%d vel=%d hz_milli=%d pinc_micro=%d gain_milli=%d held=%d",
                 (int)note, (int)vel, (int)(hz * 1000.f + 0.5f),
                 (int)(pinc * 1e6f + 0.5f),
                 (int)(midi_vel_gain * 1000.f + 0.5f), held_count);
#endif
}

static void handle_note_off(uint8_t note)
{
    stack_remove(note);

    if(held_count > 0)
    {
        // Queda alguna tecla pulsada: volver a la mas reciente (cima). Cambio de
        // pitch SIN reatacar: la envolvente sigue en sustain (legato natural).
        // Se recupera tambien su velocity: al volver a ella debe sonar con la
        // dinamica con que se toco, no con la de la tecla que se acaba de soltar.
        uint8_t top = held_notes[held_count - 1];
        osc.SetFreq(note_to_hz(top));
        midi_vel_gain = vel_to_gain(held_vels[held_count - 1]);
        midi_gate     = true;
    }
    else
    {
        // Ninguna tecla: soltar el gate -> el ADSR entra en release.
        midi_gate = false;
    }

#if MIDI_DEBUG
    hw.PrintLine("# NOTE_OFF note=%d held=%d gate=%d",
                 (int)note, held_count, (int)midi_gate);
#endif
}

// Vacia la cola de eventos MIDI. Omni: no se filtra por canal (responde a todos).
static void midi_process()
{
    midi.Listen();
    while(midi.HasEvents())
    {
        MidiEvent m = midi.PopEvent();
        midi_events++;
        switch(m.type)
        {
            case NoteOn:
            {
                NoteOnEvent e = m.AsNoteOn();
                handle_note_on(e.note, e.velocity);
            }
            break;
            case NoteOff:
            {
                NoteOffEvent e = m.AsNoteOff();
                handle_note_off(e.note);
            }
            break;
            default: break;  // CC, pitch bend, etc.: fuera del alcance del MVP
        }
    }
}

static void midi_init()
{
    MidiUartHandler::Config c;
    // El Config por defecto ya usa USART_1 con rx=D14/tx=D13; se fijan explicito
    // por claridad y para que quede documentado en el propio codigo.
    c.transport_config.periph = UartHandler::Config::Peripheral::USART_1;
    c.transport_config.rx     = {DSY_GPIOB, 7};  // D14 (5V-tolerante -> 6N138 directo)
    c.transport_config.tx     = {DSY_GPIOB, 6};  // D13
    midi.Init(c);
    midi.StartReceive();
}

#if MIDI_SELFTEST
// Vuelca la tabla nota->Hz->phase_inc para las 128 notas MIDI, con la MISMA
// note_to_hz() y la MISMA sample rate que usa el runtime, para validar contra
// mtof en 8_validate_midi.py. Valores como enteros (el logger del Daisy no lleva
// %f fiable): hz en milihercios, phase_inc en micro-unidades.
static void dump_note_table(float sr)
{
    hw.PrintLine("NOTE_TABLE_BEGIN sr_milli=%d len=%d",
                 (int)(sr * 1000.f + 0.5f), TABLE_LEN);
    for(int n = 0; n < 128; ++n)
    {
        float hz   = note_to_hz(n);
        float pinc = hz * TABLE_LEN / sr;
        hw.PrintLine("%d %d %d",
                     n, (int)(hz * 1000.f + 0.5f), (int)(pinc * 1e6f + 0.5f));
    }
    hw.PrintLine("NOTE_TABLE_END");
}
#endif


// --------------------------------------------------------------------------- //
// Recepcion SPI (S7): esclavo SPI_1 + DMA  --  NO SE TOCA en S8
// --------------------------------------------------------------------------- //
static const int SPI_SAMPLES   = 1024;
static const int SPI_PAYLOAD   = SPI_SAMPLES * 2;   // 2048 bytes
static const int SPI_FRAME_LEN = SPI_PAYLOAD + 6;   // 2054 bytes (header+seq+crc)

SpiHandle spi;

static uint8_t DMA_BUFFER_MEM_SECTION spi_rx_buffer[SPI_FRAME_LEN];
static int16_t spi_wave[SPI_SAMPLES];

static volatile bool     spi_dma_done = false;
static volatile uint32_t spi_frames   = 0;

void OnSpiComplete(void* context, SpiHandle::Result result);

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

void OnSpiComplete(void* context, SpiHandle::Result result)
{
    (void)context;
    if(result == SpiHandle::Result::OK)
        spi_dma_done = true;
    else
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

    spi.DmaReceive(spi_rx_buffer, SPI_FRAME_LEN, nullptr, OnSpiComplete, nullptr);
}

#if SPI_DEBUG_DUMP
static void dump_wave(const int16_t* w)
{
    hw.PrintLine("WAVE_BEGIN");
    for(int n = 0; n < SPI_SAMPLES; ++n)
        hw.PrintLine("%d", (int)w[n]);
    hw.PrintLine("WAVE_END");
}
#endif

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
            std::memcpy(spi_wave, spi_rx_buffer + 4, SPI_PAYLOAD);
            osc.LoadNext(spi_wave);   // mismo crossfade de S5
            spi_frames++;
        }
    }

    spi_dma_done = false;
    spi.DmaReceive(spi_rx_buffer, SPI_FRAME_LEN, nullptr, OnSpiComplete, nullptr);

    if(ok)
    {
        hw.SetLed(true);
        int16_t vmin = 32767, vmax = -32768;
        for(int n = 0; n < SPI_SAMPLES; ++n) {
            if(spi_wave[n] < vmin) vmin = spi_wave[n];
            if(spi_wave[n] > vmax) vmax = spi_wave[n];
        }
        hw.PrintLine("# SPI ok seq=%u frames=%u min=%d max=%d s0=%d s512=%d",
                     seq, (unsigned)spi_frames, (int)vmin, (int)vmax,
                     (int)spi_wave[0], (int)spi_wave[512]);
#if SPI_DEBUG_DUMP
        dump_wave(spi_wave);
#endif
    }
    else
    {
        hw.PrintLine("# SPI DESCARTADA seq=%u (header/CRC)", seq);
    }
}


// --------------------------------------------------------------------------- //
// Bloque B: panel analogico (6 potes + selector) y filtro Svf
// --------------------------------------------------------------------------- //
// Los siete canales van al ADC1 del STM32H750, con los potes alimentados desde
// 3V3A (pin fisico 21) y NUNCA desde el rail de 5 V: el ADC referencia su fondo
// de escala a esa misma tension analogica, asi que cualquier deriva afecta por
// igual a referencia y senal y se cancela. Colgarlos del 3V3 digital meteria
// ademas el ruido de conmutacion en la lectura. (veroboard.md seccion 2.)

enum PotIdx
{
    POT_ATTACK = 0,
    POT_DECAY,
    POT_SUSTAIN,
    POT_RELEASE,
    POT_CUTOFF,
    POT_RES,
    POT_SELECT,
    POT_COUNT
};

// Indice para hw.GetPin() de cada canal, EN EL MISMO ORDEN que PotIdx. Ver la
// tabla de correspondencia con los pines fisicos en la cabecera del fichero.
static const uint8_t POT_PIN_D[POT_COUNT] = {15, 16, 23, 24, 25, 20, 22};

// Rangos de mapeo. La frecuencia de corte va en escala EXPONENCIAL porque el
// oido percibe la altura logaritmicamente. Los tres tiempos del ADSR pasaron a
// escala LINEAL el 1 sep 2026 por decision del autor. Queda anotada la
// contrapartida: con recorrido lineal sobre 1 ms - 2 s, el tramo de 1 a 100 ms
// -- el que decide el caracter de un ataque percusivo -- cae dentro del primer
// 5 % del giro del mando.
static const float ATTACK_MIN  = 0.001f;   // 1 ms
static const float ATTACK_MAX  = 2.0f;     // 2 s
static const float DECAY_MIN   = 0.005f;   // 5 ms
static const float DECAY_MAX   = 2.0f;     // 2 s
static const float RELEASE_MIN = 0.005f;   // 5 ms
static const float RELEASE_MAX = 4.0f;     // 4 s
static const float CUTOFF_MIN  = 30.f;     // Hz
static const float CUTOFF_MAX  = 12000.f;  // Hz. El Svf exige f < sr/3 (16 kHz):
                                           // 12 kHz deja margen y ya esta fuera
                                           // del rango util del oido para un LPF.
static const float RES_MAX     = 0.90f;    // SetRes admite 0..1; 0.9 deja margen
                                           // antes del limite de estabilidad.

// Suavizado de los controles: un polo aplicado UNA VEZ POR BLOQUE de audio
// (48 muestras a 48 kHz -> 1 kHz de tasa de control). El coeficiente 0.03
// equivale a una constante de tiempo de ~30 ms.
//
// ESTO es lo que elimina el zipper noise: sin el, cada bloque saltaria de golpe
// al valor nuevo del ADC y la escalera de escalones en la frecuencia de corte se
// oye como un crujido al girar el pote. Con el, el salto por bloque es una
// fraccion del error y el barrido suena continuo. Complementa (no sustituye) a
// los 100 nF de cada cursor a AGND, que atacan el ruido captado por el cable.
static const float CTRL_SMOOTH = 0.03f;

enum FiltType
{
    FILT_LPF = 0,
    FILT_BPF,
    FILT_HPF
};

daisysp::Svf filt;

// Valor suavizado 0..1 de cada canal. Lo escribe SOLO el hilo de audio; el bucle
// principal lo lee para el OLED y el volcado por serie. Es una carrera benigna:
// una lectura desactualizada un bloque (1 ms) no cambia nada de lo que se pinta.
static float ctrl[POT_COUNT];

static volatile int filt_type = FILT_LPF;

// Mapeo exponencial de 0..1 al rango [lo, hi].
static inline float map_exp(float x, float lo, float hi)
{
    return lo * powf(hi / lo, x);
}

// Mapeo lineal de 0..1 al rango [lo, hi]. Lo usan los tres tiempos del ADSR.
static inline float map_lin(float x, float lo, float hi)
{
    return lo + (hi - lo) * x;
}

// Decodifica el selector ON-OFF-ON leido en el pin fisico 29. Las tres tensiones
// las fija el divisor de dos resistencias de 10k descrito en veroboard.md:
//   arriba (a 3V3A) = 3,3 V -> HPF   centro (abierto) = 1,65 V -> BPF
//   abajo  (a AGND) = 0 V   -> LPF
// El sentido se corrigio el 27 ago 2026: el panel ya esta impreso y serigrafiado
// con HPF arriba, BPF en medio y LPF abajo, y el codigo lo tenia al reves.
// El centro NO es un pin al aire: si lo fuera, flotaria y leeria basura. Son esas
// dos resistencias las que lo mantienen clavado a media escala.
// No hace falta antirrebote aparte: se decide sobre el valor ya suavizado, y los
// ~30 ms del filtro de control son exactamente eso.
static inline int decode_filt(float v)
{
    if(v > 0.75f) return FILT_HPF;
    if(v < 0.25f) return FILT_LPF;
    return FILT_BPF;
}

// Lee el ADC, suaviza y traslada a los parametros. Se llama una vez por bloque
// de audio, DESDE EL HILO DE AUDIO: asi toda mutacion de env y de filt ocurre en
// el mismo hilo que los llama a Process, igual que ya se hacia con el reataque
// del ADSR. GetFloat() solo lee el buffer que llena el DMA, no bloquea.
static void controls_update()
{
    for(int i = 0; i < POT_COUNT; ++i)
        ctrl[i] += (hw.adc.GetFloat(i) - ctrl[i]) * CTRL_SMOOTH;

    // Filtro: se refresca siempre. Es el unico parametro que se barre en vivo y
    // el que tiene que sonar continuo.
    filt.SetFreq(map_exp(ctrl[POT_CUTOFF], CUTOFF_MIN, CUTOFF_MAX));
    filt.SetRes(ctrl[POT_RES] * RES_MAX);

    filt_type = decode_filt(ctrl[POT_SELECT]);

    // ADSR: solo se reescribe cuando el pote se ha movido de verdad. Los cuatro
    // setters recalculan coeficientes con exponenciales, y llamarlos 4000 veces
    // por segundo para reescribir el mismo valor es trabajo tirado.
    static float last[4] = {-1.f, -1.f, -1.f, -1.f};
    const float  EPS     = 0.002f;   // ~2 LSB de un pote de recorrido completo

    if(fabsf(ctrl[POT_ATTACK] - last[0]) > EPS)
    {
        env.SetAttackTime(map_lin(ctrl[POT_ATTACK], ATTACK_MIN, ATTACK_MAX));
        last[0] = ctrl[POT_ATTACK];
    }
    if(fabsf(ctrl[POT_DECAY] - last[1]) > EPS)
    {
        env.SetDecayTime(map_lin(ctrl[POT_DECAY], DECAY_MIN, DECAY_MAX));
        last[1] = ctrl[POT_DECAY];
    }
    if(fabsf(ctrl[POT_SUSTAIN] - last[2]) > EPS)
    {
        env.SetSustainLevel(ctrl[POT_SUSTAIN]);   // nivel, no tiempo: lineal
        last[2] = ctrl[POT_SUSTAIN];
    }
    if(fabsf(ctrl[POT_RELEASE] - last[3]) > EPS)
    {
        env.SetReleaseTime(map_lin(ctrl[POT_RELEASE], RELEASE_MIN, RELEASE_MAX));
        last[3] = ctrl[POT_RELEASE];
    }
}

static void controls_init()
{
    static AdcChannelConfig adc_cfg[POT_COUNT];
    for(int i = 0; i < POT_COUNT; ++i)
        adc_cfg[i].InitSingle(hw.GetPin(POT_PIN_D[i]));

    hw.adc.Init(adc_cfg, POT_COUNT);
    hw.adc.Start();

    // Arrancar el suavizado ya en el valor real de cada pote. Si se dejara en 0,
    // los primeros ~100 ms serian un barrido audible desde cutoff minimo hasta
    // donde este el mando: un "wop" en cada encendido.
    System::Delay(5);   // que el DMA complete al menos una conversion
    for(int i = 0; i < POT_COUNT; ++i)
        ctrl[i] = hw.adc.GetFloat(i);

    filt_type = decode_filt(ctrl[POT_SELECT]);
}


// --------------------------------------------------------------------------- //
// OLED SSD1306 por I2C (pines fisicos 12 = SCL y 13 = SDA)
// --------------------------------------------------------------------------- //
// Va colgado del Daisy, no de la CYD, porque la cadena de datos es unidireccional
// (CYD -> S3 -> Daisy) y los potes estan en el extremo final: pintarlos en la CYD
// exigiria remontar los dos enlaces al reves, incluido el SPI de S7, que esta
// congelado. Aqui es cero protocolo nuevo. (PROJECT.md seccion 9, bloque B.)
//
// TRAMPA EVITADA: I2C1 sale tanto por PB8/PB9 (pines 12-13) como por PB6/PB7
// (pines 14-15), y PB6/PB7 son el USART1 del MIDI. Coger el mapeo "por defecto"
// habria cableado el OLED encima del MIDI. Van obligatoriamente en 12 y 13.
//
// QUE MUESTRA: el parametro que se esta tocando en ese momento, en grande, con
// su valor en unidades reales y una barra con la posicion del mando; y el tipo
// de filtro, permanente, en la ultima linea. Con seis mandos y una pantalla de
// 128x64, repartirla en seis casillas diminutas seria ilegible justo cuando hace
// falta: mientras se gira un mando. El foco sigue al ultimo control movido y se
// queda ahi, sin temporizadores ni vuelta automatica a ninguna pantalla base.
//
// Efecto util durante el montaje: el propio display es la comprobacion de
// cableado. Se gira un mando y tiene que aparecer SU nombre. Si aparece otro, el
// cursor esta en el pin equivocado.

#include "dev/oled_ssd130x.h"

using MyOled = OledDisplay<SSD130xI2c128x64Driver>;
MyOled display;

// El instrumento tiene que sonar con o sin panel de display conectado, asi que
// su presencia se detecta en el arranque en vez de darse por hecha. Motivo: el
// driver transmite en modo BLOQUEANTE y no devuelve error, asi que sin esta
// comprobacion un OLED ausente o mal cableado se traduciria en un arranque
// lentisimo y en un bucle principal frenado en cada refresco.
static bool oled_present = false;

// Limite superior del refresco, no cadencia fija: oled_draw() sale sin tocar el
// bus si no ha cambiado nada de lo que se ve. Tocando el teclado sin mover
// mandos, el display no consume ni un ciclo. Cada Update() manda el framebuffer
// entero (1 kB) y bloquea ~10 ms a 1 MHz.
static const uint32_t OLED_PERIOD_MS = 80;

// Cuanto tiene que moverse un mando para robar el foco. Era el 1 %, y se subio
// al 3 % el 1 sep 2026: medido sobre el montaje final, el cursor de sustain
// tiembla ~2 % del recorrido, cruzaba el umbral continuamente y se quedaba con
// el foco de forma permanente, de modo que ningun otro mando llegaba a
// mostrarse. Subir el umbral NO pierde resolucion de ajuste: MOVE_EPS solo
// decide a que canal MIRA el display, y ctrl[] se aplica siempre entero.
static const float MOVE_EPS = 0.03f;

// Vigilancia del refresco. Un Update() sano cuesta ~10 ms, pero el transporte
// I2C de libDaisy espera hasta 1 s por cada pagina del framebuffer, asi que con
// el bus colgado un solo refresco congela el bucle principal segundos enteros y
// con el se paran el MIDI y el SPI: eso es lo que hacia que un display averiado
// se llevara por delante el instrumento entero. Al tercer refresco que pase de
// 100 ms el display se apaga solo y no se vuelve a tocar el bus en toda la
// sesion. Se prefiere perder la pantalla a perder el instrumento.
static const uint32_t OLED_STALL_MS  = 100;
static const int      OLED_STALL_MAX = 3;
static int            oled_stalls    = 0;

// Margenes verticales del area de dibujo de las dos graficas.
static const uint8_t GRAPH_TOP = 14;
static const uint8_t GRAPH_BOT = 60;

static int   focus = POT_CUTOFF;    // parametro mostrado; el corte es el de arranque
static float focus_ref[POT_COUNT];  // valor de cada canal la ultima vez que movio

static const char* filt_name(int t)
{
    return (t == FILT_LPF) ? "LPF" : (t == FILT_BPF) ? "BPF" : "HPF";
}

// Longitud del texto del valor. Cuatro cifras, punto y unidad corta caben de
// sobra; se formatea con snprintf y este tamano explicito para que el limite sea
// del compilador y no de la confianza en que el mapeo nunca se desmadre.
static const size_t VAL_CHARS = 12;

// Formatean a entero y devuelven la unidad, porque el printf del Daisy no lleva
// soporte de coma flotante fiable. Por debajo de 1000 se muestra la unidad
// pequena (ms, Hz) y por encima la grande con un decimal (s, kHz): asi el numero
// nunca pasa de cuatro cifras y entra en la fuente grande.
static const char* fmt_time(char* dst, float seconds)
{
    int ms = (int)(seconds * 1000.f + 0.5f);
    if(ms < 1000)
    {
        snprintf(dst, VAL_CHARS, "%d", ms);
        return "ms";
    }
    snprintf(dst, VAL_CHARS, "%d.%d", ms / 1000, (ms % 1000) / 100);
    return "s";
}

static const char* fmt_freq(char* dst, float hz)
{
    int h = (int)(hz + 0.5f);
    if(h < 1000)
    {
        snprintf(dst, VAL_CHARS, "%d", h);
        return "Hz";
    }
    snprintf(dst, VAL_CHARS, "%d.%d", h / 1000, (h % 1000) / 100);
    return "kHz";
}

// Lo que se pinta, ya resuelto a texto. Se compara entero contra lo anterior
// para decidir si hace falta refrescar.
struct FocusView
{
    const char* name;
    char        value[VAL_CHARS];
    const char* unit;
    int         bar;    // relleno de la barra, en pixeles (0..125)
    int         type;   // tipo de filtro, para la linea de abajo
};

static FocusView focus_view()
{
    FocusView v;
    v.type = filt_type;
    v.bar  = (int)(ctrl[focus] * 125.f);
    v.unit = "";

    switch(focus)
    {
        case POT_ATTACK:
            v.name = "ATTACK";
            v.unit = fmt_time(v.value,
                              map_lin(ctrl[POT_ATTACK], ATTACK_MIN, ATTACK_MAX));
            break;
        case POT_DECAY:
            v.name = "DECAY";
            v.unit = fmt_time(v.value,
                              map_lin(ctrl[POT_DECAY], DECAY_MIN, DECAY_MAX));
            break;
        case POT_SUSTAIN:
            v.name = "SUSTAIN";
            snprintf(v.value, VAL_CHARS, "%d", (int)(ctrl[POT_SUSTAIN] * 100.f + 0.5f));
            v.unit = "%";
            break;
        case POT_RELEASE:
            v.name = "RELEASE";
            v.unit = fmt_time(v.value,
                              map_lin(ctrl[POT_RELEASE], RELEASE_MIN, RELEASE_MAX));
            break;
        case POT_CUTOFF:
            v.name = "CUTOFF";
            v.unit = fmt_freq(v.value,
                              map_exp(ctrl[POT_CUTOFF], CUTOFF_MIN, CUTOFF_MAX));
            break;
        case POT_RES:
            v.name = "RESONANCE";
            snprintf(v.value, VAL_CHARS, "%d", (int)(ctrl[POT_RES] * RES_MAX * 100.f + 0.5f));
            v.unit = "%";
            break;
        default:  // POT_SELECT: aqui el valor ES el tipo de filtro
            v.name = "FILTER";
            strcpy(v.value, filt_name(filt_type));
            break;
    }
    return v;
}

// Pasa el foco al ultimo mando que se haya movido de verdad. Cada canal lleva su
// propia referencia, asi que el ruido nunca acumula deriva suficiente para
// disparar el cambio, y un mando quieto no compite con el que se esta girando.
static void focus_update()
{
    for(int i = 0; i < POT_COUNT; ++i)
    {
        if(fabsf(ctrl[i] - focus_ref[i]) > MOVE_EPS)
        {
            focus        = i;
            focus_ref[i] = ctrl[i];
        }
    }
}

// Envolvente en cuatro tramos. El sustain es un nivel y no un tiempo, asi que se
// le da un ancho fijo y los tres tramos que si son tiempos se reparten
// proporcionalmente lo que queda. Los tiempos se leen ya mapeados, con el mismo
// map_lin que usa el audio, para que la figura sea la que de verdad suena.
static void draw_adsr()
{
    const float a = map_lin(ctrl[POT_ATTACK], ATTACK_MIN, ATTACK_MAX);
    const float d = map_lin(ctrl[POT_DECAY], DECAY_MIN, DECAY_MAX);
    const float r = map_lin(ctrl[POT_RELEASE], RELEASE_MIN, RELEASE_MAX);
    const float s = ctrl[POT_SUSTAIN];

    const int SUS_W = 22;
    const int avail = 124 - SUS_W;   // 2 px de margen a cada lado

    float tsum = a + d + r;
    if(tsum < 1e-6f)
        tsum = 1e-6f;

    int wa = (int)(avail * (a / tsum) + 0.5f);
    int wd = (int)(avail * (d / tsum) + 0.5f);
    int wr = avail - wa - wd;
    if(wr < 0)
        wr = 0;

    const int ysus = GRAPH_BOT - (int)((GRAPH_BOT - GRAPH_TOP) * s + 0.5f);

    const int x0 = 2;
    const int x1 = x0 + wa;
    const int x2 = x1 + wd;
    const int x3 = x2 + SUS_W;
    const int x4 = x3 + wr;   // <= 126 por construccion, nunca se sale

    display.DrawLine((uint_fast8_t)x0, GRAPH_BOT, (uint_fast8_t)x1, GRAPH_TOP, true);
    display.DrawLine((uint_fast8_t)x1, GRAPH_TOP, (uint_fast8_t)x2, (uint_fast8_t)ysus, true);
    display.DrawLine((uint_fast8_t)x2, (uint_fast8_t)ysus, (uint_fast8_t)x3, (uint_fast8_t)ysus, true);
    display.DrawLine((uint_fast8_t)x3, (uint_fast8_t)ysus, (uint_fast8_t)x4, GRAPH_BOT, true);
}

// Respuesta del filtro, esquematica: banda plana, pico de resonancia sobre el
// corte y pendiente. La posicion del corte sale directa del valor del mando sin
// volver a tomar logaritmos, porque map_exp ya es exponencial y por tanto el eje
// logaritmico de frecuencia es lineal en ctrl[POT_CUTOFF].
static void draw_filter()
{
    int xc = 2 + (int)(122.f * ctrl[POT_CUTOFF] + 0.5f);
    if(xc < 2)
        xc = 2;
    if(xc > 124)
        xc = 124;

    const int yflat = 34;
    int       ypk   = yflat - (int)(16.f * ctrl[POT_RES] + 0.5f);
    if(ypk < GRAPH_TOP)
        ypk = GRAPH_TOP;

    const int W  = 14;   // ancho de la pendiente
    int       xl = xc - W;
    int       xr = xc + W;
    if(xl < 2)
        xl = 2;
    if(xr > 126)
        xr = 126;

    const uint_fast8_t ul = (uint_fast8_t)xl;
    const uint_fast8_t uc = (uint_fast8_t)xc;
    const uint_fast8_t ur = (uint_fast8_t)xr;
    const uint_fast8_t uf = (uint_fast8_t)yflat;
    const uint_fast8_t up = (uint_fast8_t)ypk;

    if(filt_type == FILT_LPF)
    {
        display.DrawLine(2, uf, ul, uf, true);
        display.DrawLine(ul, uf, uc, up, true);
        display.DrawLine(uc, up, ur, GRAPH_BOT, true);
        display.DrawLine(ur, GRAPH_BOT, 126, GRAPH_BOT, true);
    }
    else if(filt_type == FILT_HPF)
    {
        display.DrawLine(2, GRAPH_BOT, ul, GRAPH_BOT, true);
        display.DrawLine(ul, GRAPH_BOT, uc, up, true);
        display.DrawLine(uc, up, ur, uf, true);
        display.DrawLine(ur, uf, 126, uf, true);
    }
    else   // FILT_BPF
    {
        display.DrawLine(2, GRAPH_BOT, ul, uf, true);
        display.DrawLine(ul, uf, uc, up, true);
        display.DrawLine(uc, up, ur, uf, true);
        display.DrawLine(ur, uf, 126, GRAPH_BOT, true);
    }
}

static void oled_draw()
{
    static int  last_focus = -1, last_bar = -1, last_type = -1;
    static char last_value[VAL_CHARS] = "";

    FocusView v = focus_view();

    // Sin cambios visibles no se toca el bus: el Update() es lo caro. Con el
    // panel quieto la funcion sale por aqui y el I2C no se toca en absoluto.
    if(focus == last_focus && v.bar == last_bar && v.type == last_type
       && strcmp(v.value, last_value) == 0)
        return;
    last_focus = focus;
    last_bar   = v.bar;
    last_type  = v.type;
    strcpy(last_value, v.value);

    display.Fill(false);

    // Cabecera de una linea con el nombre y el valor del ultimo mando movido. El
    // numero en fuente grande y la barra de posicion se han retirado: con la
    // grafica debajo, lo que decian ya esta en la figura, y cada pantalla
    // distinta era una transferencia mas por un bus que va justo.
    char head[24];
    snprintf(head, sizeof(head), "%s %s%s", v.name, v.value, v.unit);
    display.SetCursor(0, 0);
    display.WriteString(head, Font_6x8, true);

    // Una sola vista por bloque, sin temporizadores ni pantallas intermedias: la
    // envolvente para los cuatro mandos del ADSR, la respuesta del filtro para
    // el corte, la resonancia y el selector.
    if(focus <= POT_RELEASE)
        draw_adsr();
    else
        draw_filter();

    display.Update();
}

// Configuracion I2C comun al sondeo y al driver: un unico sitio donde estan los
// pines, para que no puedan divergir.
static I2CHandle::Config oled_i2c_config()
{
    I2CHandle::Config c;
    c.periph = I2CHandle::Config::Peripheral::I2C_1;
    // 1 MHz es el valor por defecto de libDaisy y va sobrado. Si en protoboard el
    // display se corrompe (hilos largos, sin masa trenzada), bajar a I2C_400KHZ
    // antes de sospechar de nada mas.
    c.speed          = I2CHandle::Config::Speed::I2C_1MHZ;
    c.mode           = I2CHandle::Config::Mode::I2C_MASTER;
    c.pin_config.scl = hw.GetPin(11);   // pin fisico 12 = PB8
    c.pin_config.sda = hw.GetPin(12);   // pin fisico 13 = PB9
    return c;
}

// Desbloqueo del bus antes de sondear. Si el instrumento se reinicio o perdio
// tension a mitad de una transferencia, el SSD1306 se queda sujetando SDA a
// nivel bajo esperando los pulsos de reloj que le faltan para terminar el byte,
// y el bus queda muerto: el boton de reinicio no lo arregla, porque no le quita
// la alimentacion al modulo. Era lo que obligaba a esperar a que se descargaran
// los condensadores. La maniobra estandar es tomar las dos lineas como GPIO de
// drenador abierto y sacar a mano nueve pulsos por SCL -- ocho por los bits del
// byte y uno mas por el ciclo de reconocimiento -- y cerrar con una condicion de
// parada. Despues, el Init() del I2C reconfigura los dos pines en su funcion
// alternativa, asi que esto no deja nada tocado.
static void oled_bus_recover()
{
    // hw.GetPin() devuelve el tipo antiguo dsy_gpio_pin y GPIO::Init() pide el
    // nuevo Pin; la conversion solo existe en un sentido, asi que se reconstruye
    // a mano. Se hace asi, y no escribiendo PB8/PB9 a pelo, para que los pines
    // sigan saliendo de un unico sitio y no puedan divergir de oled_i2c_config().
    const dsy_gpio_pin p_scl = hw.GetPin(11);   // pin fisico 12 = PB8
    const dsy_gpio_pin p_sda = hw.GetPin(12);   // pin fisico 13 = PB9

    GPIO scl, sda;
    scl.Init(Pin(static_cast<GPIOPort>(p_scl.port), p_scl.pin),
             GPIO::Mode::OUTPUT_OD,
             GPIO::Pull::PULLUP);
    sda.Init(Pin(static_cast<GPIOPort>(p_sda.port), p_sda.pin),
             GPIO::Mode::OUTPUT_OD,
             GPIO::Pull::PULLUP);

    // En drenador abierto, escribir true suelta la linea y la sube el pull-up.
    scl.Write(true);
    sda.Write(true);
    System::Delay(1);

    for(int i = 0; i < 9; ++i)
    {
        scl.Write(false);
        System::DelayUs(5);
        scl.Write(true);
        System::DelayUs(5);
    }

    // Condicion de parada: SDA sube estando SCL ya alto.
    sda.Write(false);
    System::DelayUs(5);
    scl.Write(true);
    System::DelayUs(5);
    sda.Write(true);
    System::Delay(1);
}

// Sondeo de presencia: se manda un comando inocuo y se mira si hay ACK. Timeout
// corto a proposito, para que un display ausente cueste 10 ms y no un arranque
// entero.
static bool oled_probe()
{
    I2CHandle i2c;
    if(i2c.Init(oled_i2c_config()) != I2CHandle::Result::OK)
        return false;

    // 0x00 = byte de control "lo que sigue es comando"; 0xAE = display off.
    uint8_t cmd[2] = {0x00, 0xAE};
    return i2c.TransmitBlocking(OLED_ADDR, cmd, 2, 10) == I2CHandle::Result::OK;
}

static void oled_init()
{
    MyOled::Config c;
    c.driver_config.transport_config.i2c_config  = oled_i2c_config();
    c.driver_config.transport_config.i2c_address = OLED_ADDR;
    display.Init(c);

    display.Fill(false);
    display.SetCursor(0, 4);
    display.WriteString("ESPACIO", Font_11x18, true);
    display.SetCursor(0, 24);
    display.WriteString("LATENTE", Font_11x18, true);
    display.SetCursor(0, 52);
    display.WriteString("TFG - GITST UPV", Font_6x8, true);
    display.Update();
}


// --------------------------------------------------------------------------- //
// Callback de audio (regla critica: nada de malloc/printf/bloqueos)
// --------------------------------------------------------------------------- //
void AudioCallback(AudioHandle::InterleavingInputBuffer  in,
                   AudioHandle::InterleavingOutputBuffer out,
                   size_t size)
{
    // Reataque del ADSR pedido desde el loop (Note On): se aplica aqui, en el
    // hilo de audio, para que Retrigger no colisione con Process.
    if(midi_retrigger_req)
    {
        env.Retrigger(false);   // soft: sin click
        midi_retrigger_req = false;
    }

    // Panel analogico: una sola lectura + suavizado por bloque (1 kHz). Va aqui
    // y no en el bucle principal para que env y filt los mute el mismo hilo que
    // los llama a Process, igual que el reataque de arriba.
    controls_update();

    // Ganancia de velocity suavizada. Estado persistente entre bloques: solo la
    // toca este hilo, asi que no necesita proteccion.
    static float vel_gain_smooth = 1.f;

    // Se sacan del bucle: son constantes dentro del bloque.
    const int ft = filt_type;

    // Compensacion de la ganancia de resonancia. El pico del Svf en la frecuencia
    // de corte vale ~1/damp, con damp = 2*(1-Q^0.25): a Q alto son mas de 20 dB,
    // suficientes para saturar la salida en cuanto un armonico de la wavetable cae
    // cerca del corte. La correccion es cuadratica en Q y NEUTRA en Q=0, asi que
    // con la resonancia al minimo el nivel es exactamente el calibrado en S8 y las
    // medidas de THD no la ven.
    const float res    = ctrl[POT_RES] * RES_MAX;
    const float makeup = 1.f / (1.f + 2.f * res * res);

    for(size_t i = 0; i < size; i += 2)
    {
        vel_gain_smooth += (midi_vel_gain - vel_gain_smooth) * VEL_SMOOTH;

        float s = osc.NextSample();                // VCO: wavetable + crossfade (S5)

        // VCF: el Svf calcula las cuatro salidas a la vez, asi que elegir el tipo
        // de filtro cuesta cero CPU. Es la ventaja concreta que decidio usarlo en
        // lugar de MoogLadder.
        filt.Process(s);
        s = (ft == FILT_HPF) ? filt.High() : (ft == FILT_BPF) ? filt.Band()
                                                              : filt.Low();
        s *= makeup;

        float amp = env.Process(midi_gate);        // VCA: envolvente MIDI (gate)
        s *= amp * vel_gain_smooth * OUT_GAIN;

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

#if HEARTBEAT
    // 3 parpadeos: prueba de vida VISIBLE, sin depender del PC ni del serie.
    for(int i = 0; i < 3; ++i)
    {
        hw.SetLed(true);  System::Delay(120);
        hw.SetLed(false); System::Delay(120);
    }
    hw.PrintLine("=== SintetizadorEspacioLatente (S8 + bloque B) ===");
#define TRACE(msg) hw.PrintLine("# init " msg)
#else
#define TRACE(msg)
#endif

    osc.Init(hw.AudioSampleRate());
    osc.SetFreq(NOTE_HZ);   // pitch por defecto; gate=false -> en silencio hasta el 1er MIDI

    // Timbre de arranque: senoidal, hasta que el S3 mande la primera wavetable.
    make_boot_wave();
    osc.SetActiveNow(boot_wave);
    TRACE("osc ok");

    env.Init(hw.AudioSampleRate());
    env.SetAttackTime(ADSR_ATTACK);
    env.SetDecayTime(ADSR_DECAY);
    env.SetSustainLevel(ADSR_SUSTAIN);
    env.SetReleaseTime(ADSR_RELEASE);
    TRACE("env ok");

    // Filtro del bloque B. Arranca abierto y sin resonancia; el primer bloque de
    // audio ya lo pone donde digan los mandos.
    filt.Init(hw.AudioSampleRate());
    filt.SetFreq(CUTOFF_MAX);
    filt.SetRes(0.f);
    filt.SetDrive(0.f);
    TRACE("filtro ok");

    // Despues de env.Init(): controls_init() deja ctrl[] en el valor real de cada
    // pote, y el primer bloque de audio escribe el ADSR encima de las constantes
    // de arranque.
    controls_init();
    for(int i = 0; i < POT_COUNT; ++i)
        focus_ref[i] = ctrl[i];   // que el arranque no cuente como "mando movido"
    TRACE("potes ok");

    midi_init();
    TRACE("midi ok");

    spi_slave_init();
    TRACE("spi ok");

    // Antes de StartAudio: el driver de I2C bloquea, y es preferible que un
    // display mal cableado se note en el arranque y no como cortes en un audio
    // que ya esta sonando. Si no contesta, el instrumento sigue funcionando.
    oled_bus_recover();
    oled_present = oled_probe();
    if(oled_present)
    {
        oled_init();
        TRACE("oled ok");
    }
    else
    {
        TRACE("oled AUSENTE -- se sigue sin display");
    }

    hw.StartAudio(AudioCallback);
    TRACE("audio ok -- arranque completo");

#if MIDI_SELFTEST
    dump_note_table(hw.AudioSampleRate());
    uint32_t last_dump = System::GetNow();
#endif
    uint32_t last_blink = System::GetNow();
#if HEARTBEAT
    uint32_t last_beat = System::GetNow();
#endif
    uint32_t last_oled = System::GetNow();

    while(true)
    {
        // MIDI: pitch/gate de la voz monofonica.
        midi_process();

        // SPI: una trama lista -> validar y (si procede) crossfade de timbre.
        if(spi_dma_done)
            spi_process_frame();

#if MIDI_SELFTEST
        // Re-volcar la tabla cada 3 s para que la captura de serie siempre pille
        // un bloque completo, sin depender de cuando se abra el terminal.
        if(System::GetNow() - last_dump >= 3000)
        {
            dump_note_table(hw.AudioSampleRate());
            last_dump = System::GetNow();
        }
#endif

#if HEARTBEAT
        // Latido cada 2 s: prueba de vida del bucle principal aunque no entre
        // nada. Lleva los contadores para ver de un vistazo que subsistema recibe.
        if(System::GetNow() - last_beat >= 2000)
        {
            hw.PrintLine("# vivo midi_ev=%u spi_frames=%u gate=%d held=%d",
                         (unsigned)midi_events, (unsigned)spi_frames,
                         (int)midi_gate, held_count);
            last_beat = System::GetNow();
        }
#endif

        // Panel: seguir al mando que se este girando y refrescar el display. El
        // foco se actualiza SIEMPRE (es una comparacion de siete floats), pero
        // oled_draw() se autolimita: si no ha cambiado nada de lo que se ve, sale
        // sin tocar el bus y el bucle no se bloquea.
        focus_update();
        if(oled_present && System::GetNow() - last_oled >= OLED_PERIOD_MS)
        {
            const uint32_t t0 = System::GetNow();
            oled_draw();

            // Si el refresco se ha eternizado es que el bus esta colgado. A la
            // tercera, el display se desconecta y el instrumento sigue.
            if(System::GetNow() - t0 > OLED_STALL_MS
               && ++oled_stalls >= OLED_STALL_MAX)
                oled_present = false;

            last_oled = System::GetNow();
        }

        // Apagar el LED 100 ms despues del ultimo parpadeo de trama SPI valida.
        if(System::GetNow() - last_blink >= 100)
        {
            hw.SetLed(false);
            last_blink = System::GetNow();
        }

        System::Delay(1);
    }
}
