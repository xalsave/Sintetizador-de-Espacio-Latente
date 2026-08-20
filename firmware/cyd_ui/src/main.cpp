// main.cpp - CYD (ESP32-2432S028R) - Bloque A (20 ago 2026)
//
// Dos cosas a la vez, sobre el mismo UART full-duplex:
//   TX (IO22, 460800) -> coordenada tactil (x,y) al S3, trama de 6 bytes (S6).
//   RX (IO35, 460800) <- onda diezmada que devuelve el S3, y se PINTA.
//
// IO35 es input-only, por eso es el pin correcto para RX. Los dos extremos del
// enlace tienen que ir a la misma velocidad: si se cambia aqui, hay que cambiar
// CYD_UART_BAUD en el main.cpp del S3.
//
// Lo que llega del S3 es dato de DISPLAY, no de audio: 256 puntos int8 para
// dibujar. La wavetable real (1024 muestras Q15) no pasa por aqui nunca; va del
// S3 al Daisy por SPI. El grid y la bilineal siguen viviendo solo en el S3.
//
// Validacion por pasos:
//   1) Solo la CYD, sin el S3: al arrancar sale el patron de prueba de colores.
//      Si la pantalla se queda negra, mira la retroiluminacion (IO21).
//   2) Con el S3: DESLIZA el dedo por la pantalla (no des toques sueltos), que
//      solo se envia coordenada si el dedo se mueve mas de MOVE_THRESHOLD.

#include <Arduino.h>
#include <SPI.h>
#include <TFT_eSPI.h>
#include <XPT2046_Touchscreen.h>

// --- Pines del tactil XPT2046 (FIJOS en la ESP32-2432S028R, del esquematico) --
#define TOUCH_CLK   25
#define TOUCH_CS    33
#define TOUCH_MOSI  32   // DIN
#define TOUCH_MISO  39   // DOUT (input-only, correcto para MISO)
#define TOUCH_IRQ   36   // (input-only, correcto para IRQ)

// --- UART con el S3 (los dos pines salen por el cabezal "Expansion IO1") ------
#define UART_TX_PIN   22        // hacia el S3 (entra por su GPIO18)
#define UART_RX_PIN   35        // desde el S3 (sale de su GPIO17); input-only
#define UART_BAUD     460800

// --- Retroiluminacion --------------------------------------------------------
// TFT_eSPI ya la enciende en init() porque TFT_BL esta definido, pero se hace
// tambien a mano y lo primero de todo: si algo falla mas adelante, al menos se
// ve que la placa arranca, en vez de una pantalla negra indistinguible de un
// cuelgue.
#define TFT_BL_PIN  21

// --- Trama del canal de vuelta (ver firmware/esp32_control/src/wave_sender.h) -
//   0x5A | seq_hi | seq_lo | 256 x int8 | XOR de los bytes 1..258
#define WAVE_HEADER 0x5A
#define WAVE_POINTS 256

// --- Calibracion del tactil (valores CRUDOS del ADC del XPT2046 en esquinas) --
int TS_MINX = 133,  TS_MAXX = 3947;
int TS_MINY = 193,  TS_MAXY = 3897;

// SPI dedicado para el tactil: sus pines NO son los de la pantalla. La pantalla
// va por HSPI (ver USE_HSPI_PORT en platformio.ini) y el tactil por VSPI: son
// dos buses distintos y por eso pueden convivir sin estorbarse.
SPIClass touchSPI(VSPI);
XPT2046_Touchscreen ts(TOUCH_CS, TOUCH_IRQ);
TFT_eSPI tft = TFT_eSPI();

// --- Geometria de la pantalla (rotacion 1 = apaisado, 320x240) ---------------
static const int SCR_W    = 320;
static const int SCR_H    = 240;
static const int PLOT_TOP = 44;
static const int PLOT_BOT = 236;
static const int PLOT_CY  = (PLOT_TOP + PLOT_BOT) / 2;       // eje 0 de la onda
static const int PLOT_AMP = (PLOT_BOT - PLOT_TOP) / 2 - 4;   // media altura util

#define COLOR_BG    TFT_BLACK
#define COLOR_GRID  0x2124      // gris muy oscuro: se ve, pero no compite
#define COLOR_WAVE  TFT_CYAN
#define COLOR_TEXT  TFT_WHITE
#define COLOR_DIM   0x7BEF

// --- Estado ------------------------------------------------------------------
uint16_t x_prev = 0, y_prev = 0;    // ultima coordenada ENVIADA (para el umbral)
uint16_t x_last = 0, y_last = 0;    // la misma, para mostrarla en pantalla
const long MOVE_THRESHOLD = 300;    // en unidades 0..65535; evita saturar el UART
const unsigned long TOUCH_PERIOD_MS = 50;   // ~20 Hz, sobrado para un dedo

static int8_t   s_wave[WAVE_POINTS];
static bool     s_have_wave = false;
static uint16_t s_wave_seq  = 0;
static uint32_t s_frames    = 0;    // tramas buenas recibidas
static uint32_t s_bad       = 0;    // tramas descartadas por checksum

static int16_t s_prev_y[WAVE_POINTS];
static bool    s_have_prev = false;

// ============================ UART: envio (S6) ===============================

// Trama de 6 bytes: 0xA5, x_hi, x_lo, y_hi, y_lo, checksum(XOR de 1..4)
static void send_coord(uint16_t x, uint16_t y)
{
    uint8_t xh = x >> 8, xl = x & 0xFF;
    uint8_t yh = y >> 8, yl = y & 0xFF;
    uint8_t chk = xh ^ xl ^ yh ^ yl;
    uint8_t frame[6] = { 0xA5, xh, xl, yh, yl, chk };
    Serial1.write(frame, 6);
}

// ========================= UART: recepcion de la onda ========================

// Maquina de estados equivalente a la del S3: se resincroniza buscando 0x5A, de
// modo que un byte perdido no descuadra el flujo para siempre. Un 0x5A dentro
// del payload no confunde nada, porque a partir de la cabecera la trama es de
// longitud fija; y si se desincroniza, esa trama cae por checksum y la
// siguiente reengancha.
static bool wave_rx_poll()
{
    static uint8_t state = 0, chk = 0, seq_hi = 0, seq_lo = 0;
    static int     idx = 0;
    static int8_t  buf[WAVE_POINTS];
    bool got = false;

    while (Serial1.available()) {
        uint8_t b = (uint8_t)Serial1.read();
        switch (state) {
            case 0:  if (b == WAVE_HEADER) { chk = 0; state = 1; } break;
            case 1:  seq_hi = b; chk ^= b; state = 2; break;
            case 2:  seq_lo = b; chk ^= b; idx = 0; state = 3; break;
            case 3:
                buf[idx++] = (int8_t)b;
                chk ^= b;
                if (idx >= WAVE_POINTS) state = 4;
                break;
            case 4:
                state = 0;
                if (chk == b) {
                    memcpy(s_wave, buf, sizeof(buf));
                    s_wave_seq  = ((uint16_t)seq_hi << 8) | seq_lo;
                    s_have_wave = true;
                    s_frames++;
                    got = true;
                } else {
                    s_bad++;
                }
                break;
        }
    }
    return got;
}

// ================================ Pantalla ===================================

static inline int x_of(int i) { return (i * (SCR_W - 1)) / (WAVE_POINTS - 1); }
static inline int y_of(int8_t v) { return PLOT_CY - ((int)v * PLOT_AMP) / 128; }

// Patron de prueba de arranque: valida driver, orientacion y colores antes de
// que haya nada que pintar. Barras de izquierda a derecha, en este orden.
static void draw_test_pattern()
{
    const uint16_t bars[8] = { TFT_RED, TFT_GREEN, TFT_BLUE, TFT_YELLOW,
                               TFT_CYAN, TFT_MAGENTA, TFT_WHITE, TFT_BLACK };
    for (int i = 0; i < 8; ++i) tft.fillRect(i * 40, 0, 40, 120, bars[i]);
    tft.drawRect(0, 0, SCR_W, SCR_H, TFT_WHITE);   // marco: confirma la orientacion

    tft.setTextColor(TFT_WHITE, TFT_BLACK);
    tft.drawString("TFT_eSPI OK - ILI9341 320x240", 8, 132, 4);
    tft.drawString("barras: rojo verde azul amarillo", 8, 168, 2);
    tft.drawString("        cian magenta blanco negro", 8, 186, 2);
    tft.drawString("si no cuadran: platformio.ini, nota 1", 8, 210, 2);
}

// Marco fijo: se pinta una vez y ya no se toca.
static void draw_ui_frame()
{
    tft.fillScreen(COLOR_BG);
    tft.setTextColor(COLOR_TEXT, COLOR_BG);
    tft.drawString("Sintetizador de Espacio Latente", 4, 2, 2);

    tft.drawRect(0, PLOT_TOP - 3, SCR_W, (PLOT_BOT - PLOT_TOP) + 6, COLOR_GRID);
    for (int x = 0; x < SCR_W; x += 4) tft.drawPixel(x, PLOT_CY, COLOR_GRID);

    tft.setTextColor(COLOR_DIM, COLOR_BG);
    tft.drawString("esperando onda del S3...", 8, PLOT_CY - 8, 2);
    s_have_prev = false;
}

static void draw_status()
{
    tft.fillRect(0, 20, SCR_W, 20, COLOR_BG);
    tft.setTextColor(s_have_wave ? TFT_GREEN : COLOR_DIM, COLOR_BG);
    char buf[64];
    snprintf(buf, sizeof(buf), "x=%5u  y=%5u   seq=%u  err=%u",
             x_last, y_last, s_wave_seq, s_bad);
    tft.drawString(buf, 4, 22, 2);
}

// Redibuja la onda en dos pasadas: primero se borra entera la anterior y luego
// se pinta la nueva. Repintar el area de golpe con un fillRect daria parpadeo
// con cada trama, y borrar segmento a segmento intercalado con el dibujo se
// comeria trozos de la linea nueva donde las dos se cruzan.
static void draw_wave()
{
    int16_t ny[WAVE_POINTS];
    for (int i = 0; i < WAVE_POINTS; ++i) ny[i] = (int16_t)y_of(s_wave[i]);

    if (s_have_prev) {
        for (int i = 0; i < WAVE_POINTS - 1; ++i) {
            int x0 = x_of(i), x1 = x_of(i + 1);
            tft.drawLine(x0, s_prev_y[i], x1, s_prev_y[i + 1], COLOR_BG);
            // El borrado se lleva por delante los puntos de la linea central.
            for (int x = x0; x <= x1; ++x)
                if ((x & 3) == 0) tft.drawPixel(x, PLOT_CY, COLOR_GRID);
        }
    } else {
        // Primera onda: limpiar el "esperando onda del S3...".
        tft.fillRect(1, PLOT_TOP - 2, SCR_W - 2, (PLOT_BOT - PLOT_TOP) + 4, COLOR_BG);
        for (int x = 0; x < SCR_W; x += 4) tft.drawPixel(x, PLOT_CY, COLOR_GRID);
    }

    for (int i = 0; i < WAVE_POINTS - 1; ++i)
        tft.drawLine(x_of(i), ny[i], x_of(i + 1), ny[i + 1], COLOR_WAVE);

    memcpy(s_prev_y, ny, sizeof(ny));
    s_have_prev = true;
}

// ================================== Arranque =================================

void setup()
{
    Serial.begin(115200);             // monitor USB (depuracion)
    delay(300);
    Serial.println();
    Serial.println("=== CYD: tactil -> UART, onda <- UART (bloque A) ===");

    // Retroiluminacion ANTES que nada (ver comentario de TFT_BL_PIN).
    pinMode(TFT_BL_PIN, OUTPUT);
    digitalWrite(TFT_BL_PIN, HIGH);

    tft.init();
    tft.setRotation(1);               // apaisado, 320x240
    tft.fillScreen(COLOR_BG);
    draw_test_pattern();

    // UART con el S3, ahora en los dos sentidos.
    // El buffer de RX por defecto (256 B) se queda justo por debajo de los 260
    // que ocupa una trama de onda: hay que agrandarlo, y antes del begin().
    Serial1.setRxBufferSize(1024);
    Serial1.begin(UART_BAUD, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
    Serial.printf("UART con el S3: RX=IO%d TX=IO%d @%u baud\n",
                  UART_RX_PIN, UART_TX_PIN, UART_BAUD);

    // Tactil en su SPI propio.
    touchSPI.begin(TOUCH_CLK, TOUCH_MISO, TOUCH_MOSI, TOUCH_CS);
    ts.begin(touchSPI);
    ts.setRotation(1);                // orientacion del tactil; ajustable

    delay(2000);                      // tiempo para mirar el patron de prueba
    draw_ui_frame();
    draw_status();

    Serial.println("DESLIZA el dedo (los toques sueltos no llegan al umbral).");
}

void loop()
{
    // 1) Onda de vuelta del S3. Se atiende siempre y lo primero: el parser no
    //    bloquea, y asi el buffer de RX no se llena mientras se lee el tactil.
    if (wave_rx_poll()) {
        draw_wave();
        draw_status();
        Serial.printf("onda seq=%u  (tramas=%u, err=%u)\n",
                      s_wave_seq, s_frames, s_bad);
    }

    // 2) Tactil, a ~20 Hz y sin delay(): un delay aqui dejaria sin atender la
    //    recepcion de la onda justo mientras el dedo se mueve, que es cuando
    //    llegan las tramas.
    static unsigned long t_touch = 0;
    if (millis() - t_touch >= TOUCH_PERIOD_MS) {
        t_touch = millis();

        if (ts.tirqTouched() && ts.touched()) {
            TS_Point p = ts.getPoint();   // p.x, p.y crudos (~200..3900)

            // Normaliza a 0..65535 con la calibracion.
            long nx = map(p.x, TS_MINX, TS_MAXX, 0, 65535);
            long ny = map(p.y, TS_MINY, TS_MAXY, 0, 65535);
            nx = constrain(nx, 0, 65535);
            ny = constrain(ny, 0, 65535);

            // Envia solo si el dedo se movio lo suficiente (evita spamear).
            bool sent = false;
            if (labs(nx - (long)x_prev) > MOVE_THRESHOLD ||
                labs(ny - (long)y_prev) > MOVE_THRESHOLD) {
                send_coord((uint16_t)nx, (uint16_t)ny);
                x_prev = (uint16_t)nx;
                y_prev = (uint16_t)ny;
                x_last = (uint16_t)nx;
                y_last = (uint16_t)ny;
                sent = true;
                draw_status();
            }

            Serial.printf("crudo=(%4d,%4d)  norm=(%5ld,%5ld)%s\n",
                          p.x, p.y, nx, ny, sent ? "  [enviado]" : "");
        }
    }
}
