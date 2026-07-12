// uart_receiver.h - Receptor de la trama (x,y) de la CYD por UART.
//
// Trama (6 bytes):  0xA5  x_hi  x_lo  y_hi  y_lo  checksum(XOR de los 4 datos)
// Funciona como maquina de estados que se resincroniza buscando 0xA5, asi un
// byte perdido no descuadra el flujo para siempre.
#pragma once

#include <Arduino.h>

// Inicializa el UART fisico (Serial1) en los pines indicados.
// rx_pin: pin por el que ENTRAN los bytes de la CYD (GPIO18 en el S3).
// tx_pin: no se usa en esta direccion; -1 para no asignarlo.
void uart_rx_begin(int rx_pin, int tx_pin = -1, uint32_t baud = 115200);

// Procesa los bytes pendientes del UART. Si se completa una trama valida,
// escribe la coordenada en *out_x / *out_y y devuelve true (una vez por trama).
// Llamar a menudo desde loop(); no bloquea.
bool uart_rx_poll(uint16_t* out_x, uint16_t* out_y);
