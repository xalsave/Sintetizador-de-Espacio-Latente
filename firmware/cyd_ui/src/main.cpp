// main.cpp - CYD (ESP32-2432S028R) - Sesion 6
// Lee el tactil resistivo XPT2046 y envia la coordenada (x,y) normalizada al
// ESP32-S3 por UART (trama de 6 bytes). NO dibuja en la pantalla (firmware
// minimo de S6; el mapa latente en pantalla se deja para S9, opcional).
//
// Validacion (CYD sola, sin el S3):
//   Abre el monitor USB y toca la pantalla. Veras las coordenadas CRUDAS del
//   tactil y las NORMALIZADAS (0..65535). Usa las crudas de las esquinas para
//   ajustar la calibracion (TS_MINX..TS_MAXY). Cuando esten bien, cablea el TX
//   al S3.

#include <Arduino.h>
#include <SPI.h>
#include <XPT2046_Touchscreen.h>

// --- Pines del tactil XPT2046 (FIJOS en la ESP32-2432S028R, del esquematico) --
#define TOUCH_CLK   25
#define TOUCH_CS    33
#define TOUCH_MOSI  32   // DIN
#define TOUCH_MISO  39   // DOUT (input-only, correcto para MISO)
#define TOUCH_IRQ   36   // (input-only, correcto para IRQ)

// --- Salida UART hacia el S3 (pin IO22, libre, sale por el conector P3) -------
#define UART_TX_PIN 22
#define UART_RX_PIN -1   // en esta direccion no recibimos nada del S3

// --- Calibracion del tactil (AJUSTAR con valores reales; ver instrucciones) ---
// Valores CRUDOS del ADC del XPT2046 en las esquinas. Estos por defecto son
// razonables, pero casi seguro tendras que afinarlos mirando el monitor.
int TS_MINX = 133,  TS_MAXX = 3947;
int TS_MINY = 193,  TS_MAXY = 3897;

// SPI dedicado para el tactil: sus pines NO son los del SPI por defecto del ESP32.
SPIClass touchSPI(VSPI);
XPT2046_Touchscreen ts(TOUCH_CS, TOUCH_IRQ);

uint16_t  x_prev = 0, y_prev = 0;
const long MOVE_THRESHOLD = 300;   // en unidades 0..65535; evita saturar el UART

// Envia la trama de 6 bytes: 0xA5, x_hi, x_lo, y_hi, y_lo, checksum(XOR de 1..4)
static void send_coord(uint16_t x, uint16_t y)
{
    uint8_t xh = x >> 8, xl = x & 0xFF;
    uint8_t yh = y >> 8, yl = y & 0xFF;
    uint8_t chk = xh ^ xl ^ yh ^ yl;
    uint8_t frame[6] = { 0xA5, xh, xl, yh, yl, chk };
    Serial1.write(frame, 6);
}

void setup()
{
    Serial.begin(115200);             // monitor USB (depuracion)
    delay(300);
    Serial.println();
    Serial.println("=== CYD touch -> UART (sesion 6) ===");

    // UART hacia el S3: solo TX en IO22 (RX sin usar).
    Serial1.begin(115200, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);

    // Tactil en su SPI propio.
    touchSPI.begin(TOUCH_CLK, TOUCH_MISO, TOUCH_MOSI, TOUCH_CS);
    ts.begin(touchSPI);
    ts.setRotation(1);                // orientacion del tactil; ajustable

    Serial.println("Toca la pantalla. crudo -> norm (0..65535).");
}

void loop()
{
    if (ts.tirqTouched() && ts.touched()) {
        TS_Point p = ts.getPoint();   // p.x, p.y crudos (~200..3900)

        // Normaliza a 0..65535 con la calibracion.
        long nx = map(p.x, TS_MINX, TS_MAXX, 0, 65535);
        long ny = map(p.y, TS_MINY, TS_MAXY, 0, 65535);
        nx = constrain(nx, 0, 65535);
        ny = constrain(ny, 0, 65535);

        // Envia solo si el dedo se movio lo suficiente (evita spamear el UART).
        bool sent = false;
        if (labs(nx - (long)x_prev) > MOVE_THRESHOLD ||
            labs(ny - (long)y_prev) > MOVE_THRESHOLD) {
            send_coord((uint16_t)nx, (uint16_t)ny);
            x_prev = (uint16_t)nx;
            y_prev = (uint16_t)ny;
            sent = true;
        }

        Serial.printf("crudo=(%4d,%4d)  norm=(%5ld,%5ld)%s\n",
                      p.x, p.y, nx, ny, sent ? "  [enviado]" : "");
        delay(50);   // ~20 Hz: legible para calibrar y sobrado para un dedo
    }
}
