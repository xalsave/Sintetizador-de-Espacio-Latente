#include "daisy_seed.h"
#include <cmath>

using namespace daisy;

DaisySeed hw;

// Tabla de seno: 1024 muestras (mismo tamaño que nuestro grid)
static float sine_table[1024];

static void build_sine_table() {
    for (int i = 0; i < 1024; i++) {
		const float PI = 3.14159265358979f;
		sine_table[i] = sinf(2.f * PI * i / 1024.f);    
		}
}

// Acumulador de fase
static float phase     = 0.f;
static float phase_inc = 0.f;

void AudioCallback(AudioHandle::InterleavingInputBuffer  in,
                   AudioHandle::InterleavingOutputBuffer out,
                   size_t size) {
    for (size_t i = 0; i < size; i += 2) {
        // Interpolación lineal entre muestras
        uint32_t idx0 = (uint32_t)phase;
        uint32_t idx1 = (idx0 + 1) & 1023;
        float    frac = phase - idx0;
        float    s    = sine_table[idx0] * (1.f - frac)
                      + sine_table[idx1] * frac;
        s *= 0.5f;  // bajar ganancia para no saturar

        out[i]     = s;  // L
        out[i + 1] = s;  // R

        phase += phase_inc;
        if (phase >= 1024.f) phase -= 1024.f;
    }
}

int main(void) {
    hw.Init();
    hw.SetAudioBlockSize(48);

    float sr  = hw.AudioSampleRate();  // 48000 Hz
    phase_inc = 440.f * 1024.f / sr;   // La4 = 440 Hz

    build_sine_table();
    hw.StartAudio(AudioCallback);

    // LED parpadeando para confirmar que el programa corre
    while (true) {
        hw.SetLed(true);
        System::Delay(500);
        hw.SetLed(false);
        System::Delay(500);
    }
}