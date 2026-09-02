// main.cpp - CYD (ESP32-2432S028R): lee el tactil y dibuja la onda.
//
// Dos cosas a la vez, sobre el mismo UART full-duplex:
//   TX (IO22, 460800) -> coordenada tactil (x,y) al S3, trama de 6 bytes.
//   RX (IO35, 460800) <- onda diezmada que devuelve el S3, y se PINTA.
//
// IO35 es input-only, por eso es el pin correcto para RX. Los dos extremos del
// enlace tienen que ir a la misma velocidad: si se cambia aqui, hay que cambiar
// CYD_UART_BAUD en el main.cpp del S3.
//
// Lo que llega del S3 es dato de DISPLAY, no de audio: 256 puntos int8 para
// dibujar. La wavetable real (1024 muestras Q15) va del S3 al Daisy por SPI.
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

// --- Calibracion del tactil (valores CRUDOS del ADC del XPT2046) -------------
//
// La CYD va montada girada 180 grados en el panel (USB-C lejos del OLED), por
// eso pantalla y tactil usan setRotation(3). La libreria XPT2046_Touchscreen
// aplica la rotacion (case 3: xraw = 4095 - x, yraw = 4095 - y), asi que la
// calibracion del panel completo con rotacion 1 (X 133..3947, Y 193..3897)
// queda espejada: X 148..3962, Y 198..3902.
//
// Medido en banco con la placa YA MONTADA en la carcasa, tocando las cuatro
// esquinas del hueco visible del panel:
//
//        sup. izq. (480, 480)          sup. der. (3730, 250)
//        inf. izq. (480,3730)          inf. der. (3730,3730)
//
// Hay DOS ventanas, y a proposito no son la misma:
//
//   VISIBLE (450..3730)  lo que asoma por el hueco del panel. Solo se usa para
//                        calcular el area de DIBUJO (VIS_* mas abajo).
//
//   CAPTURA (600..3580)  la que decide que toques valen. 150 cuentas (~2,5 mm)
//                        mas estrecha por cada lado: el labio impreso apoya
//                        sobre el cristal en todo el perimetro y genera
//                        pulsaciones fantasma pegadas al borde (una que se
//                        colaba daba crudo (3714, 643), a 16 cuentas del limite).
//
// No hay ajuste fino por esquina: el tactil esta un pelo girado respecto al
// hueco y un mapeo rectangular no puede corregir un giro.
//
// OJO: es la ventana de CAPTURA la que se mapea a 0..65535, no la visible. Asi
// el espacio latente se alcanza entero; lo que se pierde son ~2,5 mm de
// recorrido del dedo por lado, no rango de timbre.
int TS_MINX = 600,  TS_MAXX = 3580;    // ventana de CAPTURA, para el tactil
int TS_MINY = 600,  TS_MAXY = 3580;

// SPI dedicado para el tactil: sus pines NO son los de la pantalla. La pantalla
// va por HSPI (ver USE_HSPI_PORT en platformio.ini) y el tactil por VSPI: son
// dos buses distintos y por eso pueden convivir sin estorbarse.
SPIClass touchSPI(VSPI);
XPT2046_Touchscreen ts(TOUCH_CS, TOUCH_IRQ);
TFT_eSPI tft = TFT_eSPI();

// --- Geometria de la pantalla (rotacion 1 = apaisado, 320x240) ---------------
static const int SCR_W    = 320;
static const int SCR_H    = 240;

// --- Area VISIBLE por la ventana del panel, en pixeles -----------------------
// El panel impreso tapa un borde del cristal, asi que pintar de 0 a 320 deja
// parte de la interfaz debajo del plastico. Estos cuatro numeros salen de pasar
// la ventana VISIBLE a pixeles (450..3730 en crudo, NO la de captura), con el
// panel COMPLETO en 148..3962 (X) y 198..3902 (Y), mas 1 px de margen:
//
//   x0 = (450-148)/(3962-148) * 320 =  25      y0 = (450-198)/(3902-198) * 240 = 16
//   x1 = (3730-148)/(3962-148)* 320 = 300      y1 = (3730-198)/(3902-198)* 240 = 229
static const int VIS_X0 = 26;
static const int VIS_X1 = 301;
static const int VIS_Y0 = 17;
static const int VIS_Y1 = 229;
static const int VIS_W  = VIS_X1 - VIS_X0;
static const int VIS_H  = VIS_Y1 - VIS_Y0;

// Reparto vertical dentro del area visible (VIS_Y0 = 17):
//   17..33  titulo (fuente 2, 16 px de alto)
//   33..51  banda de estado x=/y=/seq/err
//   56..227 recuadro de la onda  ->  PLOT_TOP-3 = 56, y 5 px de aire tras la
//                                    banda de estado para que no se toquen.
static const int PLOT_TOP = VIS_Y0 + 42;                     // 59
static const int PLOT_BOT = VIS_Y1 - 5;                      // 224
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

// ============================ UART: envio ====================================

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

static inline int x_of(int i) { return VIS_X0 + (i * (VIS_W - 1)) / (WAVE_POINTS - 1); }
static inline int y_of(int8_t v) { return PLOT_CY - ((int)v * PLOT_AMP) / 128; }

// Patron de prueba de arranque: valida driver, orientacion y colores antes de
// que haya nada que pintar. Barras de izquierda a derecha, en este orden.
static void draw_test_pattern()
{
    const uint16_t bars[8] = { TFT_RED, TFT_GREEN, TFT_BLUE, TFT_YELLOW,
                               TFT_CYAN, TFT_MAGENTA, TFT_WHITE, TFT_BLACK };
    // Todo dentro del area visible: si el marco blanco se ve entero por los
    // cuatro lados, la ventana del panel y estas constantes cuadran.
    const int barw = VIS_W / 8;
    for (int i = 0; i < 8; ++i)
        tft.fillRect(VIS_X0 + i * barw, VIS_Y0, barw, 84, bars[i]);
    tft.drawRect(VIS_X0, VIS_Y0, VIS_W, VIS_H, TFT_WHITE);

    tft.setTextColor(TFT_WHITE, TFT_BLACK);
    tft.drawString("TFT_eSPI OK", VIS_X0 + 6, VIS_Y0 + 92, 4);
    tft.drawString("barras: rojo verde azul amarillo", VIS_X0 + 6, VIS_Y0 + 124, 2);
    tft.drawString("        cian magenta blanco negro", VIS_X0 + 6, VIS_Y0 + 142, 2);
    tft.drawString("marco blanco visible = ventana OK", VIS_X0 + 6, VIS_Y0 + 166, 2);
}

// Marco fijo: se pinta una vez y ya no se toca.
static void draw_ui_frame()
{
    tft.fillScreen(COLOR_BG);
    tft.setTextColor(COLOR_TEXT, COLOR_BG);
    tft.drawString("Sintetizador de Espacio Latente", VIS_X0 + 1, VIS_Y0, 2);

    tft.drawRect(VIS_X0, PLOT_TOP - 3, VIS_W, (PLOT_BOT - PLOT_TOP) + 6, COLOR_GRID);
    for (int x = VIS_X0; x < VIS_X1; x += 4) tft.drawPixel(x, PLOT_CY, COLOR_GRID);

    tft.setTextColor(COLOR_DIM, COLOR_BG);
    tft.drawString("esperando onda del S3...", VIS_X0 + 6, PLOT_CY - 8, 2);
    s_have_prev = false;
}

static void draw_status()
{
    tft.fillRect(VIS_X0, VIS_Y0 + 16, VIS_W, 18, COLOR_BG);
    tft.setTextColor(s_have_wave ? TFT_GREEN : COLOR_DIM, COLOR_BG);
    char buf[64];
    snprintf(buf, sizeof(buf), "x=%5u  y=%5u   seq=%u  err=%u",
             x_last, y_last, s_wave_seq, s_bad);
    tft.drawString(buf, VIS_X0 + 1, VIS_Y0 + 17, 2);
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
        tft.fillRect(VIS_X0 + 1, PLOT_TOP - 2, VIS_W - 2, (PLOT_BOT - PLOT_TOP) + 4, COLOR_BG);
        for (int x = VIS_X0; x < VIS_X1; x += 4) tft.drawPixel(x, PLOT_CY, COLOR_GRID);
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
    tft.setRotation(3);               // apaisado 320x240, GIRADO 180 (ver calibracion)
    tft.fillScreen(COLOR_BG);
    draw_test_pattern();

    // UART con el S3, en los dos sentidos.
    // El buffer de RX por defecto (256 B) se queda justo por debajo de los 260
    // que ocupa una trama de onda: hay que agrandarlo, y antes del begin().
    Serial1.setRxBufferSize(1024);
    Serial1.begin(UART_BAUD, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
    Serial.printf("UART con el S3: RX=IO%d TX=IO%d @%u baud\n",
                  UART_RX_PIN, UART_TX_PIN, UART_BAUD);

    // Tactil en su SPI propio.
    touchSPI.begin(TOUCH_CLK, TOUCH_MISO, TOUCH_MOSI, TOUCH_CS);
    ts.begin(touchSPI);
    ts.setRotation(3);                // MISMO giro que la pantalla, o el dedo va al reves

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
            TS_Point p = ts.getPoint();   // p.x, p.y crudos

            // Fuera de la ventana util -> se IGNORA por completo, no se recorta
            // con constrain(): si no, un contacto del plastico de la carcasa se
            // enviaria igual, clavado al borde del espacio latente.
            if (p.x < TS_MINX || p.x > TS_MAXX ||
                p.y < TS_MINY || p.y > TS_MAXY) {
                Serial.printf("crudo=(%4d,%4d)  [fuera de ventana, ignorado]\n",
                              p.x, p.y);
                return;
            }

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
