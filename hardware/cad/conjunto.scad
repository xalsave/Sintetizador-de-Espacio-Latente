// ============================================================================
//  conjunto.scad -- Vista de montaje del Sintetizador de Espacio Latente
//  TFG - Bloque C - 23 ago 2026
//
//  NO GENERA PIEZAS PARA IMPRIMIR. Es un visor: monta el panel sobre la caja,
//  permite separarlas y deja elegir el color de cada una para decidir que
//  filamento comprar antes de gastarlo.
//
//  Las piezas de verdad salen de panel.scad y caja.scad, cada una con su
//  parametro "part". Este fichero solo las llama.
//
//  F5 y a mirar. F6 no hace falta.
// ============================================================================

use <panel.scad>
use <caja.scad>

/* [1. Vista] */
// "montado"      -> todo en su sitio
// "explosionado" -> el panel levantado y la trasera separada
// el resto -> una sola pieza, para mirarla de cerca
vista   = "montado";   // [montado, explosionado, panel, bandeja, trasera]
explode = 40;          // separacion en la vista explosionada

/* [2. Colores] */
// Cambia estos tres y mira. Elige "custom" en cualquiera para que use el
// hex de la casilla de abajo en vez de la lista.
col_panel  = "naranja";   // [naranja, negro, gris, blanco, plata, azul, rojo, verde, amarillo, madera, custom]
col_caja   = "negro";     // [naranja, negro, gris, blanco, plata, azul, rojo, verde, amarillo, madera, custom]
col_letras = "negro";     // [negro, blanco, plata, rojo, amarillo, naranja, custom, ninguno]

// Solo se leen cuando el desplegable de arriba correspondiente esta en
// "custom". Formato hex de 6 cifras, con o sin '#'.
col_panel_hex  = "#e4610f";
col_caja_hex   = "#1a1a1a";
col_letras_hex = "#ffffff";

/* [3. Que se ensena] */
show_letras  = true;   // el relleno del grabado (simula el rotulador)
show_modulos = true;   // pantalla de la CYD y del OLED, en negro

/* [4. Cotas de la caja -- DEBEN COINCIDIR con caja.scad] */
box_w    = 186;
panel_d  = 116;
h_front  = 30;
h_back   = 62;
bay_d    = 30;
panel_t  = 3.4;

/* [Hidden] */
$fa = 2; $fs = 0.5;

deep    = sqrt(panel_d*panel_d - (h_back - h_front)*(h_back - h_front));
ang     = atan((h_back - h_front) / deep);
hf_wall = h_front - panel_t / cos(ang);

// Colores de filamento aproximados, mirados sobre bobinas reales.
// "custom" tira del hex escrito a mano en la casilla que le corresponde.
function hexof(n, custom = "#cccccc") =
      n == "custom"   ? custom
    : n == "naranja"  ? "#e4610f"
    : n == "negro"    ? "#1a1a1a"
    : n == "gris"     ? "#6e7378"
    : n == "blanco"   ? "#edede8"
    : n == "plata"    ? "#a8adb3"
    : n == "azul"     ? "#1b4f8c"
    : n == "rojo"     ? "#b0201e"
    : n == "verde"    ? "#1f6f4f"
    : n == "amarillo" ? "#e8b517"
    : n == "madera"   ? "#9c6b3f"
    :                   "#cccccc";

// ---------------------------------------------------------------------------
// El panel, colocado sobre el plano de apoyo de la caja.
// El giro es +ang alrededor de X: asi la y local del panel (que corre sobre
// la pendiente) cae sobre la pendiente real, y su z local apunta hacia fuera.
// ---------------------------------------------------------------------------
module place_panel(lift = 0) {
    translate([0, -lift * sin(ang), hf_wall + lift * cos(ang)])
        rotate([ang, 0, 0])
            children();
}

module panel_pintado(lift = 0) {
    place_panel(lift) {
        color(hexof(col_panel, col_panel_hex)) panel();
        if (show_letras && col_letras != "ninguno")
            color(hexof(col_letras, col_letras_hex)) label_ink();
    }
}

// Pantallas, para hacerse una idea de como contrastan con el color elegido.
// Cotas copiadas de panel.scad; si las cambias alli, aqui solo es la vista.
module pantallas(lift = 0) {
    place_panel(lift) {
        color("#0b0b0d") {
            translate([11 + 13.5, 56 + 2.5, panel_t - 0.4])
                cube([59.5, 45, 0.5]);
            // Aproximacion visual: el hueco real del OLED sale del STL
            // injertado en panel.scad (oled_frame_cut), no de un rectangulo.
            // Esto es solo una caja parecida para ver el contraste de color.
            translate([135 - 14, 90 - 7.25, panel_t - 0.4])
                cube([28.0, 14.5, 0.5]);
        }
    }
}

// ---------------------------------------------------------------------------
module todo(lift_panel = 0, back = 0) {
    panel_pintado(lift_panel);
    if (show_modulos) pantallas(lift_panel);
    color(hexof(col_caja, col_caja_hex)) bandeja();
    color(hexof(col_caja, col_caja_hex)) translate([0, back, 0]) trasera();
}

if (vista == "montado")            todo(0, 0);
else if (vista == "explosionado")  todo(explode, explode);
else if (vista == "panel")       { color(hexof(col_panel, col_panel_hex)) panel();
                                   if (show_letras && col_letras != "ninguno")
                                       color(hexof(col_letras, col_letras_hex)) label_ink(); }
else if (vista == "bandeja")       color(hexof(col_caja, col_caja_hex)) bandeja();
else if (vista == "trasera")       color(hexof(col_caja, col_caja_hex)) trasera();
