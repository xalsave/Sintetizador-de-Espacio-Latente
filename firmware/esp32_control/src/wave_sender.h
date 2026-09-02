// wave_sender.h - Canal de vuelta S3 -> CYD: envia la onda para PINTARLA.
//
// Lo que viaja NO son datos de sintesis: es una version diezmada y reducida a
// 8 bits, solo para dibujar. La wavetable real de 1024 muestras Q15 solo sale
// por el SPI hacia el Daisy.
//
// Por que diezmar: 1024 muestras int16 son 2048 bytes = 178 ms a 115200 baud,
// imposible de seguir con el dedo. 256 puntos int8 son 256 bytes y sobran para
// los 320 px de ancho de la pantalla: ~5,6 ms de trama a 460800 baud.
//
// Trama (260 bytes), mismo patron que los otros dos enlaces:
//   byte 0     : header 0x5A  (espejo del 0xA5 que usa la CYD al enviar)
//   byte 1..2  : seq  uint16 BIG-endian (incrementa por onda enviada)
//   byte 3..258: payload, 256 muestras int8 (Q7, -128..127)
//   byte 259   : checksum XOR de los bytes 1..258
#pragma once

#include <stdint.h>

#define WAVE_TX_POINTS 256   // puntos que se envian a la CYD (uno por columna)

// Diezma 'wave' (len muestras Q15, len debe ser multiplo de WAVE_TX_POINTS),
// la reduce a int8 y la manda por Serial1. Devuelve el seq usado.
// Requiere que uart_rx_begin() se haya llamado ya con un tx_pin valido.
uint16_t wave_send(const int16_t* wave, int len);
