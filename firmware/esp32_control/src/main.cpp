// main.cpp - Sesion 6 (S3): genera la wavetable por interpolacion bilineal.
//
// Dos entradas a la vez:
//   1) UART en GPIO18  <- trama de 6 bytes de la CYD (entrada real).
//   2) Texto "x y" por USB (Serial0) <- util para depurar sin la CYD.
//
// Salida de verificacion por USB: celda+pesos, resumen y volcado de las 1024
// muestras (WAVE_BEGIN..WAVE_END), igual que antes.

#include <Arduino.h>
#include <math.h>
#include "interpolation.h"
#include "uart_receiver.h"

#define CYD_RX_PIN 18          // pin del S3 por el que entra el UART de la CYD

static int16_t g_wave[TABLE_LEN];   // wavetable interpolada actual (RAM, ~2 KB)
static bool    g_have_wave = false;
static String  g_input;             // acumula la linea tecleada por USB

static void print_stats()
{
    long   vmin = 32767, vmax = -32768;
    double sumsq = 0.0;
    for (int n = 0; n < TABLE_LEN; ++n) {
        int v = g_wave[n];
        if (v < vmin) vmin = v;
        if (v > vmax) vmax = v;
        sumsq += (double)v * (double)v;
    }
    double rms = sqrt(sumsq / TABLE_LEN);
    Serial0.printf("# min=%ld max=%ld rms=%.1f  s[0]=%d s[%d]=%d\n",
                   vmin, vmax, rms, g_wave[0], TABLE_LEN - 1, g_wave[TABLE_LEN - 1]);
}

static void dump_wave()
{
    Serial0.println("WAVE_BEGIN");
    for (int n = 0; n < TABLE_LEN; ++n)
        Serial0.println(g_wave[n]);
    Serial0.println("WAVE_END");
}

// 'src' identifica de donde vino la coordenada: "UART" (CYD) o "USB" (teclado).
static void handle_coords(uint16_t x, uint16_t y, const char* src)
{
    GridLocation loc = interpolate_wavetable(x, y, g_wave);
    g_have_wave = true;
    // Confirmacion corta: coordenada recibida + celda/pesos usados.
    Serial0.printf("# [%s] coord=(%u,%u)  celda X[%d->%d] fx=%.3f  Y[%d->%d] fy=%.3f\n",
                   src, x, y, loc.ix0, loc.ix1, loc.fx, loc.iy0, loc.iy1, loc.fy);
    Serial0.println("tabla encontrada");
    // (El volcado de las 1024 muestras sigue disponible bajo demanda: escribe
    //  "dump" por USB; "stat" para solo el resumen min/max/rms.)
}

// --- Procesa una linea de texto del USB ("x y", "dump", "stat") --------------
static void process_line(String line)
{
    line.trim();
    if (line.length() == 0) return;

    if (line.equalsIgnoreCase("dump")) {
        if (g_have_wave) dump_wave();
        else Serial0.println("# aun no hay wavetable; envia una coordenada primero");
        return;
    }
    if (line.equalsIgnoreCase("stat")) {
        if (g_have_wave) print_stats();
        else Serial0.println("# aun no hay wavetable");
        return;
    }

    int sep = line.indexOf(' ');
    if (sep < 0) {
        Serial0.println("# formato: \"x y\"  (0..65535 cada uno)");
        return;
    }
    long x = line.substring(0, sep).toInt();
    long y = line.substring(sep + 1).toInt();
    if (x < 0) x = 0; else if (x > 65535) x = 65535;
    if (y < 0) y = 0; else if (y > 65535) y = 65535;
    handle_coords((uint16_t)x, (uint16_t)y, "USB");
}

void setup()
{
    Serial0.begin(115200);
    delay(300);
    Serial0.println();
    Serial0.println("=== S3 bilinear (sesion 6) ===");
    Serial0.printf("Grid %dx%d, TABLE_LEN=%d\n", GRID_SIZE, GRID_SIZE, TABLE_LEN);
    Serial0.println("Entradas: UART(GPIO18) desde la CYD  |  texto \"x y\" por USB");

    // UART fisico hacia/desde la CYD: solo recibimos, en GPIO18.
    uart_rx_begin(CYD_RX_PIN);
}

void loop()
{
    // 1) Coordenada desde la CYD por UART (entrada real).
    uint16_t ux, uy;
    if (uart_rx_poll(&ux, &uy)) {
        handle_coords(ux, uy, "UART");
    }

    // 2) Texto por USB (depuracion). Acepta '\n', '\r' o '\r\n'.
    while (Serial0.available()) {
        char c = (char)Serial0.read();
        if (c == '\n' || c == '\r') {
            if (g_input.length() > 0) {
                process_line(g_input);
                g_input = "";
            }
        } else {
            g_input += c;
        }
    }
}
