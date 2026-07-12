// uart_receiver.cpp - Maquina de estados que decodifica la trama de la CYD.
#include "uart_receiver.h"

// Estados del parser.
enum RxState {
    WAIT_HEADER,   // buscando 0xA5
    READ_XH,       // leyendo x_high
    READ_XL,
    READ_YH,
    READ_YL,
    READ_CHK       // leyendo checksum y validando
};

static RxState  s_state = WAIT_HEADER;
static uint8_t  s_xh, s_xl, s_yh, s_yl;

void uart_rx_begin(int rx_pin, int tx_pin, uint32_t baud)
{
    // Serial1 es el UART fisico. En el S3 los bytes de la CYD entran por GPIO18.
    Serial1.begin(baud, SERIAL_8N1, rx_pin, tx_pin);
    s_state = WAIT_HEADER;
}

bool uart_rx_poll(uint16_t* out_x, uint16_t* out_y)
{
    while (Serial1.available()) {
        uint8_t b = (uint8_t)Serial1.read();

        switch (s_state) {
            case WAIT_HEADER:
                if (b == 0xA5) s_state = READ_XH;
                break;

            case READ_XH: s_xh = b; s_state = READ_XL; break;
            case READ_XL: s_xl = b; s_state = READ_YH; break;
            case READ_YH: s_yh = b; s_state = READ_YL; break;
            case READ_YL: s_yl = b; s_state = READ_CHK; break;

            case READ_CHK: {
                uint8_t chk = s_xh ^ s_xl ^ s_yh ^ s_yl;
                s_state = WAIT_HEADER;          // listos para la siguiente trama
                if (chk == b) {                 // checksum correcto -> trama valida
                    *out_x = ((uint16_t)s_xh << 8) | s_xl;
                    *out_y = ((uint16_t)s_yh << 8) | s_yl;
                    return true;
                }
                // checksum malo: descartar y reanudar la busqueda de 0xA5.
                break;
            }
        }
    }
    return false;
}
