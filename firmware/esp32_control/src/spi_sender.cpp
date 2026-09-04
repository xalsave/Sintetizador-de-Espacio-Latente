// spi_sender.cpp - Implementacion del emisor SPI maestro del S3.
#include "spi_sender.h"
#include <Arduino.h>
#include <SPI.h>
#include <string.h>

// TABLE_LEN vale 1024 (grid.h). No se incluye grid.h aqui a proposito: eso
// arrastraria la definicion del array GRID_TABLES a esta unidad de compilacion
// y daria multiple definition en el enlazado. Se fija el tamano localmente.
static const int      SAMPLES     = 1024;             // muestras por wavetable
static const int      PAYLOAD_LEN = SAMPLES * 2;      // 2048 bytes
static const int      FRAME_LEN   = PAYLOAD_LEN + 6;  // 2054 bytes (header+seq+crc)
static const uint32_t SPI_HZ      = 10000000;         // 10 MHz

static SPIClass spi(FSPI);        // SPI2 (FSPI) del ESP32-S3
static int      cs_pin = -1;
static uint16_t seq    = 0;
static uint8_t  frame[FRAME_LEN]; // buffer de trama reutilizado

// CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF, sin reflexion ni xorout).
// Identico en el Daisy y en 7_validate_spi.py para que la validacion cruzada
// pueda comparar el CRC bit a bit, no solo las muestras.
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

void spi_tx_begin(int sck, int miso, int mosi, int cs)
{
    cs_pin = cs;
    pinMode(cs_pin, OUTPUT);
    digitalWrite(cs_pin, HIGH);     // CS en reposo alto (activo a nivel bajo)
    // ss = -1: gestionamos CS a mano; writeBytes() no togglea el SS del
    // periferico.
    spi.begin(sck, miso, mosi, -1);
}

uint16_t spi_send_wavetable(const int16_t* wave)
{
    uint16_t this_seq = seq++;

    // Cabecera + seq_id (little-endian).
    frame[0] = 0xDE;
    frame[1] = 0xAD;
    frame[2] = (uint8_t)(this_seq & 0xFF);
    frame[3] = (uint8_t)(this_seq >> 8);

    // Payload: 1024 int16 en little-endian. El ESP32-S3 y el STM32 del Daisy son
    // ambos little-endian, asi que una copia directa ya deja los bytes en el
    // orden que espera el receptor.
    memcpy(frame + 4, wave, PAYLOAD_LEN);

    // CRC16 sobre el payload (little-endian).
    uint16_t crc = crc16_ccitt(frame + 4, PAYLOAD_LEN);
    frame[4 + PAYLOAD_LEN]     = (uint8_t)(crc & 0xFF);
    frame[4 + PAYLOAD_LEN + 1] = (uint8_t)(crc >> 8);

    // Transferencia bloqueante: ~1.6 ms a 10 MHz, de sobra para la tasa de
    // control (un dedo genera decenas de coordenadas por segundo, no miles).
    spi.beginTransaction(SPISettings(SPI_HZ, MSBFIRST, SPI_MODE0));
    digitalWrite(cs_pin, LOW);
    spi.writeBytes(frame, FRAME_LEN);
    digitalWrite(cs_pin, HIGH);
    spi.endTransaction();

    return this_seq;
}
