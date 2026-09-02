// spi_sender.h - Envio de la wavetable interpolada al Daisy por SPI (maestro).
//
// Trama (2054 bytes, ver docs/spi.md seccion 2):
//   byte 0..1     : header 0xDE 0xAD
//   byte 2..3     : seq_id  uint16 little-endian (incrementa por wavetable)
//   byte 4..2051  : payload 1024 muestras int16 little-endian (Q15)
//   byte 2052..53 : CRC16/CCITT-FALSE sobre el payload, little-endian
//
// SPI: maestro, 10 MHz, modo 0 (CPOL=0/CPHA=0), MSB first.
#pragma once
#include <stdint.h>

// Inicializa el bus SPI maestro con los pines GPIO del S3:
//   sck=12, mosi=11, miso=13, cs=10.
// miso no se usa (el Daisy recibe en RX_ONLY), pero se cablea por coherencia.
void spi_tx_begin(int sck, int miso, int mosi, int cs);

// Empaqueta y envia 'wave' (1024 muestras Q15) como una trama completa.
// Devuelve el seq_id usado, util para casar el envio con el lado del Daisy en la
// validacion cruzada.
uint16_t spi_send_wavetable(const int16_t* wave);
