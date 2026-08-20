// wave_sender.cpp - Diezmado 1024 -> 256, Q15 -> int8, y envio por Serial1.
#include "wave_sender.h"

#include <Arduino.h>

static uint16_t s_seq = 0;

uint16_t wave_send(const int16_t* wave, int len)
{
    const int step = len / WAVE_TX_POINTS;   // 1024 / 256 = 4

    uint8_t frame[3 + WAVE_TX_POINTS + 1];
    frame[0] = 0x5A;
    frame[1] = (uint8_t)(s_seq >> 8);
    frame[2] = (uint8_t)(s_seq & 0xFF);

    for (int i = 0; i < WAVE_TX_POINTS; ++i) {
        // Media de las 'step' muestras del grupo antes de diezmar: sin ella, las
        // ondas con mucho armonico se dibujarian con aliasing y la figura de la
        // pantalla no se pareceria a la que suena.
        int32_t acc = 0;
        for (int k = 0; k < step; ++k) acc += wave[i * step + k];
        int32_t v = (acc / step) >> 8;             // Q15 -> Q7
        if (v >  127) v =  127;
        if (v < -128) v = -128;
        frame[3 + i] = (uint8_t)(int8_t)v;
    }

    uint8_t chk = 0;
    for (int i = 1; i < 3 + WAVE_TX_POINTS; ++i) chk ^= frame[i];
    frame[3 + WAVE_TX_POINTS] = chk;

    Serial1.write(frame, sizeof(frame));

    return s_seq++;
}
