// interpolation.h - Interpolacion bilineal sobre el grid 16x16 de wavetables.
//
// Mapea una coordenada tactil normalizada (x,y en 0..65535) a una wavetable de
// TABLE_LEN muestras Q15, interpolando entre las 4 celdas vecinas del grid.
// Mismo criterio de mapeo que 5_demo_morph.py (validacion en PC).
#pragma once

#include <stdint.h>
#include "grid.h"   // aporta GRID_SIZE, TABLE_LEN y
                    // const int16_t GRID_TABLES[GRID_SIZE][GRID_SIZE][TABLE_LEN]
                    // indexado [fila i = eje Y][columna j = eje X][muestra].

// Celda y pesos usados en un mapeo. Util para depurar y para validar contra el
// PC (poder reproducir exactamente la misma celda/fraccion en numpy).
struct GridLocation {
    int   ix0, ix1;   // columnas (eje X) vecinas
    int   iy0, iy1;   // filas (eje Y) vecinas
    float fx, fy;     // pesos fraccionarios hacia ix1 / iy1, en [0..1]
};

// Interpola la wavetable para (x,y) normalizados a 0..65535.
// Escribe TABLE_LEN muestras Q15 en 'out' (el llamador reserva el buffer).
// Devuelve la celda y los pesos empleados.
GridLocation interpolate_wavetable(uint16_t x, uint16_t y, int16_t* out);
