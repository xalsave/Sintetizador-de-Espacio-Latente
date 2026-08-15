// SintetizadorEspacioLatente.cpp
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
#include "daisysp.h"   // daisysp::Adsr (DaisySP ya compilada y enlazada, -ldaisysp)
#include <cmath>       // powf
#include <cstring>     // memcpy

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

// Envolvente ADSR (segundos / nivel 0..1). Valores de partida; se afinaran de oido.
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

    // Ganancia de velocity suavizada. Estado persistente entre bloques: solo la
    // toca este hilo, asi que no necesita proteccion.
    static float vel_gain_smooth = 1.f;

    for(size_t i = 0; i < size; i += 2)
    {
        vel_gain_smooth += (midi_vel_gain - vel_gain_smooth) * VEL_SMOOTH;

        float amp = env.Process(midi_gate);        // envolvente MIDI (gate)
        float s   = osc.NextSample() * amp * vel_gain_smooth * OUT_GAIN;
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
    hw.PrintLine("=== SintetizadorEspacioLatente (S8) ===");
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

    midi_init();
    TRACE("midi ok");

    spi_slave_init();
    TRACE("spi ok");

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

        // Apagar el LED 100 ms despues del ultimo parpadeo de trama SPI valida.
        if(System::GetNow() - last_blink >= 100)
        {
            hw.SetLed(false);
            last_blink = System::GetNow();
        }

        System::Delay(1);
    }
}
