// interpolation.cpp - Interpolacion bilineal del grid 16x16.
#include "interpolation.h"
#include <math.h>

GridLocation interpolate_wavetable(uint16_t x, uint16_t y, int16_t* out)
{
    // Rango tactil 0..65535 -> rango de indices 0..(GRID_SIZE-1).
    const float scale = (float)(GRID_SIZE - 1) / 65535.0f;
    float gx = (float)x * scale;   // eje X (columna)
    float gy = (float)y * scale;   // eje Y (fila)

    int ix0 = (int)floorf(gx);
    int iy0 = (int)floorf(gy);
    if (ix0 < 0) ix0 = 0; else if (ix0 > GRID_SIZE - 1) ix0 = GRID_SIZE - 1;
    if (iy0 < 0) iy0 = 0; else if (iy0 > GRID_SIZE - 1) iy0 = GRID_SIZE - 1;

    // Vecino derecho / inferior; clamp en el borde para no salir del array.
    int ix1 = (ix0 < GRID_SIZE - 1) ? ix0 + 1 : ix0;
    int iy1 = (iy0 < GRID_SIZE - 1) ? iy0 + 1 : iy0;

    float fx = gx - (float)ix0;    // peso hacia ix1
    float fy = gy - (float)iy0;    // peso hacia iy1
    if (fx < 0.0f) fx = 0.0f; else if (fx > 1.0f) fx = 1.0f;
    if (fy < 0.0f) fy = 0.0f; else if (fy > 1.0f) fy = 1.0f;

    // Convencion de ejes: GRID_TABLES[fila i = eje Y][columna j = eje X][muestra].
    // En ESP32 el array 'const' vive en flash y se lee directamente (la cache lo
    // mapea), no hace falta pgm_read_*.
    const int16_t* tl = GRID_TABLES[iy0][ix0];   // top-left
    const int16_t* tr = GRID_TABLES[iy0][ix1];   // top-right
    const int16_t* bl = GRID_TABLES[iy1][ix0];   // bottom-left
    const int16_t* br = GRID_TABLES[iy1][ix1];   // bottom-right

    for (int n = 0; n < TABLE_LEN; ++n) {
        // Bilineal en float. Las muestras ya son Q15 ([-32768..32767]) y el
        // resultado es una combinacion convexa de ellas: no puede desbordar.
        float top = (float)tl[n] + ((float)tr[n] - (float)tl[n]) * fx;
        float bot = (float)bl[n] + ((float)br[n] - (float)bl[n]) * fx;
        float val = top + (bot - top) * fy;
        out[n] = (int16_t)lroundf(val);
    }

    GridLocation loc = { ix0, ix1, iy0, iy1, fx, fy };
    return loc;
}
