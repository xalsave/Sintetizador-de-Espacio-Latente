    
   // ============================================================================
//  panel.scad -- Panel frontal del Sintetizador de Espacio Latente
//  TFG - Bloque C - 23 ago 2026
//
//  Se imprime PLANO sobre la cama, cara trasera abajo (z=0 es la cara que
//  mira a los componentes; z=panel_t es la cara vista, con las etiquetas).
//  Ender 3 V3 SE, 220x220. Boquilla 0,4 / capa 0,2.
//
//  F5 previsualiza - F6 renderiza - File > Export > Export as STL
//
//  NO lleva: DIN del MIDI, entrada de alimentacion, interruptor de red.
//  Esos tres van en la cara trasera de la caja (decidido el 23 ago).
// ============================================================================

/* [1. VERIFICAR CON EL PIE DE REY ANTES DE IMPRIMIR] */

// Diametro de la rosca del potenciometro. La ficha del WH148 dice M7x0,75.
// Si midiendo sale 6,0 hay que poner 6,0 aqui. NO imprimir sin comprobarlo.
pot_thread_d   = 7.0;
// Longitud de la parte roscada del pote. Limita el grosor del panel:
// grosor <= rosca - 3,0 (tuerca + arandela).
pot_thread_len = 7.0;   // MEDIDO 23 ago con pie de rey. Tuerca de 10 mm
                        // entrecaras -> M7x0,75 confirmado.
// Rosca del selector de filtro (toggle miniatura M6x0,75).
sw_thread_d    = 6.0;
// Rosca del jack de audio de 3,5 mm de chasis.
jack_thread_d  = 6.0;

/* [2. Panel] */

panel_w   = 186;    // ancho
panel_h   = 116;    // alto
panel_t   = 3.4;    // grosor (multiplo de 0,2)
corner_r  = 4;      // radio de las esquinas

// Taladros M3 para atornillar el panel al cuerpo de la caja (mas adelante)
mount_holes   = true;
mount_hole_d  = 3.2;
mount_inset   = 7;   // desde cada borde

/* [3. Potenciometros] */

pot_count   = 6;
pot_pitch   = 24;    // separacion entre centros
pot_x0      = 22;    // centro del primero
pot_row_y   = 24;    // altura de la fila
pot_clear   = 0.3;   // VALIDADO en probeta el 23 ago: el pote entra justo

// Espiga antigiro del pote. NO es redonda: es una pletina RECTANGULAR de
// 2,8 x 1,2 mm (medida el 23 ago), con el lado largo TANGENTE a la
// circunferencia del eje. La posicion (r = 7,8, angulo 90) esta validada
// sobre la probeta; lo unico que estaba mal era la forma.
pot_antirot     = true;
pot_antirot_w   = 2.8;   // lado largo, tangencial
pot_antirot_h   = 1.2;   // lado corto, radial
pot_antirot_clear = 0.4; // VALIDADO en probeta: 0,2 entra perfecta y 0,4 tambien.
                         // Se elige 0,4 porque el panel son seis ranuras en una
                         // sola impresion de 2,5 h: si una sale apretada, no hay
                         // segunda oportunidad. La tuerca es la que sujeta; que
                         // la pletina tenga 0,2 de juego no afecta a nada.
pot_antirot_r   = 7.8;   // del centro del eje al centro de la pletina
// 180 = pletina a la IZQUIERDA del eje. NO es indiferente: las tres patillas
// del pote salen a 90 grados de la pletina, asi que con la pletina arriba
// apuntan a la izquierda, hacia el pote vecino, y no caben dos seguidos.
// Con 180 las patillas apuntan HACIA ABAJO, perpendiculares a la fila: dejan
// de estorbarse entre ellas sea cual sea el paso, y los 24 mm se mantienen.
pot_antirot_ang = 180;

/* [4. Selector de filtro y jack] */

sw_x = 166;  sw_y = 24;
sw_clear = 0.3;
// Antigiro del toggle: la ficha lo acota, D2,4 a 6,4 mm del centro.
sw_antirot      = true;
sw_antirot_d    = 2.8;
sw_antirot_r    = 6.4;
sw_antirot_ang  = 90;

// El jack sale por el LATERAL de la caja, no por el panel (decidido el 23 ago).
// La geometria se deja aqui por si hay que devolverlo al frente: basta con
// poner jack_on_panel = true.
jack_on_panel = false;
jack_x = 168; jack_y = 62;
jack_clear = 0.3;

/* [5. OLED 0,96 pulgadas -- modulo de 26 x 26] */
// VALIDADO EN PROBETA (25 ago): estos valores dan el ajuste bueno. El cristal
// entra, queda a ras, el flex sale por su canal y los pines no chocan.
// NO tocar sin volver a imprimir una probeta.
// TODO EN MILIMETROS. Origen: el CENTRO de la PCB. dy positivo = hacia
// arriba (el lado de los pines). Tres niveles como la CYD: asiento de la
// PCB -> hueco del cristal entero -> labio con la ventana de pantalla.

// Posicion del centro de la PCB en el panel, eje X
oled_cx = 135;
// Posicion del centro de la PCB en el panel, eje Y
oled_cy = 90;
// Ancho de la PCB
oled_pcb_w = 26.0;
// Alto de la PCB
oled_pcb_h = 26.0;
// Holgura total del asiento de la PCB (la mitad por lado)
oled_pcb_clear = 0.8;
// Ancho del cristal que sobresale (todo lo gris del croquis)
oled_glass_w = 25.60;
// Alto del cristal
oled_glass_h = 17.6;
// Centro del cristal respecto al centro de la PCB (0 = centrado, y lo esta)
oled_glass_dy = 0;
// Holgura total del hueco del cristal
oled_glass_clear = 1.0;
// Cuanto LEVANTA el cristal sobre la cara de la PCB (3,5 total - 1,2 PCB - aire)
oled_glass_protr = 1.4;
// Ancho de la ventana del labio (pantalla util 21,74 + holgura)
oled_win_w = 22.2;
// Alto de la ventana (pantalla util 10,86 + holgura)
oled_win_h = 11.3;
// Centro de la pantalla util respecto al centro de la PCB: el cristal esta
// centrado pero la pantalla empieza a 1,5 de su borde superior -> +1,52
oled_win_dy = 1.52;
// Grosor del labio que pisa el cristal no-pantalla (3 capas de 0,2)
oled_lip_t = 0.6;
// Distancia entre CENTROS de taladros, horizontal. NO confirmada: asume
// 1,5 de cada borde. Si los agujeros no caen, medir y corregir esta
oled_hole_pitch_x = 23;
// Distancia entre centros de taladros, vertical (del croquis: 22.000)
oled_hole_pitch_y = 22;
// Centro de la parrilla de taladros vs centro de la PCB: arriba estan a
// 1,5 del borde y abajo a 2,5 -> la parrilla esta 0,5 subida
oled_hole_dy = 0.5;
// Broca del taladro: 3,0 reales + 0,4 de contraccion de impresion
oled_screw_d = 3.4;
// Descarga de las puntas de los pines: ancho (4 pines a 2,54 = 7,6 + margen)
oled_pin_w = 13;
// Descarga de pines: alto
oled_pin_h = 4;
// Descarga de pines: centro respecto al centro de la PCB (fila superior)
oled_pin_y = 10.5;
// Pared que queda por delante de las puntas de los pines
oled_pin_wall = 0.6;
// Escote del flex en el borde inferior: ancho (tab de 14 + margen)
oled_flex_w = 16;
// Escote del flex: cuanto se prolonga mas alla del borde de la PCB
oled_flex_ext = 1;

// caja util para dimensionar las probetas
oled_ref_w = oled_pcb_w + 12;  oled_ref_h = oled_pcb_h + 12;  oled_ref_t = 5.2;

/* [6. CYD (ESP32-2432S028R)] */

// Esquina inferior izquierda de la PCB de la CYD, sobre el panel
cyd_x0 = 11;  cyd_y0 = 56;
cyd_pcb_w = 86;  cyd_pcb_h = 50;
// Area VISIBLE de la pantalla y donde empieza dentro de la PCB
cyd_vis_w = 59.5; cyd_vis_h = 45;
// La CYD va GIRADA 180 grados respecto al plano del fabricante, para que el
// USB-C quede en el lado OPUESTO al OLED (decidido el 23 ago). Girada, el
// margen que queda a la izquierda del area visible es el otro: 86-13,5-59,5.
// Acuerdate de girar tambien la imagen en firmware (TFT_eSPI setRotation).
cyd_vis_dx = 13.0;   // del borde IZQUIERDO de la PCB al area visible
cyd_vis_dy = 2.5;    // del borde INFERIOR de la PCB al area visible
cyd_win_clear = 0.5; // la ventana se cala centrada sobre el area visible
// El MODULO negro (marco incluido) mide 69 x 50 y sobresale 4 mm de la PCB.
// Entra en un rebaje por detras y apoya contra el anillo del bisel, de modo
// que el marco queda tapado y el cristal solo se hunde cyd_bezel.
// Es la misma receta que tampa.stl: 1,5 de bisel + 4 de hueco.
cyd_mod_w = 69;  cyd_mod_h = 50;
cyd_mod_protr = 4.0;
// 1,0 y no 0,5: en la probeta del 23 ago el modulo entraba pero no asentaba
// del todo. Un hueco impreso sale 0,2-0,35 menor que la cota, asi que de los
// 0,5 no quedaba casi nada, y ademas las esquinas del hueco salen redondeadas
// por el radio de la boquilla mientras que las del modulo son vivas.
cyd_mod_clear = 1.0;
cyd_corner_r  = 1.2;   // descarga en las cuatro esquinas del rebaje
cyd_bezel = 1.5;     // material que queda por delante del cristal
// Taladros de montaje de la CYD. Cotas del diagrama oficial del proyecto
// ESP32-Cheap-Yellow-Display (OriginalDocumentation/3-Structure_Diagram):
// los cuatro estan a 4,0 mm de cada borde, separacion 78,0 x 42,0.
cyd_screws   = true;
cyd_screw_d  = 3.4;    // paso de un M3
cyd_screw_xy = [[4, 4], [86 - 4, 4], [4, 50 - 4], [86 - 4, 50 - 4]];
// El tornillo entra por DELANTE y lleva tuerca por detras. Los cuatro caen
// FUERA del rebaje del modulo (x = 4 y 82 contra un rebaje de 8,5 a 78), o
// sea en los 3,4 mm macizos del panel.
// Como el modulo entra 1,9 y sobresale 4, la PCB queda 2,1 mm por detras de
// la cara trasera del panel: hacen falta cuatro espaciadores de esa altura.
// Se imprimen aparte, con part = "espaciadores" (dos minutos).
// Avellanado DESACTIVADO: la cabeza necesita apoyar en los 3,4 macizos.
cyd_cbore     = false;
cyd_cbore_d   = 6.0;   // cabeza de M3 cilindrica + holgura
cyd_cbore_dep = 1.6;

/* [7. Etiquetas] */

labels       = true;
// "grabado" -> hueco en la cara vista. Necesita profundidad y, para leerse de
//              verdad, pasarle un rotulador y limpiar: la pintura se queda en
//              el hueco y ahi aparece el contraste.
// "relieve" -> letra saliente. Define mucho mejor en FDM, y permite un cambio
//              de filamento a la altura panel_t para tener letras de otro
//              color (en el laminador: pausa / cambio de color por capa).
label_mode   = "relieve";   // [grabado, relieve]
label_depth  = 1.0;   // profundidad del hueco si label_mode = "grabado"
                      // (0,6 era demasiado poco: solo tres capas)
label_relief = 0.6;   // altura de la letra si label_mode = "relieve".
                      // Con "grabado" no se usa para nada.
label_size   = 4.0;   // tamano MAXIMO; las etiquetas largas se encogen solas
label_dy     = -11;   // desplazamiento respecto al centro del mando.
                      // -11 alinea la fila de potes con la etiqueta LPF
pot_names    = ["ATTACK", "DECAY", "SUSTAIN", "RELEASE", "CUTOFF", "Q"];

// Fuente. Viene de serie con Windows, asi que no hay nada que instalar.
// Es una grotesca americana pesada: trazo grueso, aperturas amplias y cero
// florituras, que es lo que pide un panel de instrumento. A 4,8 mm el trazo
// mide ~0,9 mm, o sea dos pasadas de boquilla: el grabado sale limpio.
// (Se descarto Akira Expanded: solo estaba instalada para el usuario y
// OpenSCAD no ve ese almacen. Ver el historial de la sesion del 23 ago.)
label_font   = "Franklin Gothic Heavy";

// Relacion ancho/alto media de un caracter. Sirve para encoger las etiquetas
// largas: OpenSCAD no sabe medir texto, asi que se estima.
// 0,61 esta medido sobre el propio FRAHV.TTF y es cota superior de todas las
// etiquetas de este panel: con el ninguna se encoge y ninguna se sale.
// Si cambias de fuente y alguna invade a su vecina, sube este numero.
label_aspect = 0.61;
label_max_w  = pot_pitch - 3;   // ancho util entre dos mandos contiguos

/* [8. Que pieza exportar] */

// "panel"  -> el panel completo (2,5 h)
// "coupon" -> probeta de 46 x 30 con un agujero de pote y uno de selector,
//             al grosor real del panel. 10 minutos. IMPRIMIR ESTA PRIMERO:
//             si la rosca no entra o la tuerca no llega, te enteras ahora y
//             no despues de dos horas y media.
part = "panel";   // [panel, coupon, ventanas, espaciadores, oled_solo]

// Escalera de holguras de la RANURA antigiro, de izquierda a derecha en la
// probeta. Se prueba el pote en cada una y la primera en la que la pletina
// entre sin forzar se copia arriba, en pot_antirot_clear.
slot_clear_test = [0.2, 0.4, 0.6, 0.8];

// La probeta de ventanas vuelve al grosor real del panel: ahora lo que
// comprueba no es solo la alineacion, sino que el modulo entra en su rebaje y
// que el bisel de 1,5 lo tapa. Con 2,0 no habria bisel que comprobar.

/* [Hidden] */
$fa = 2; $fs = 0.4;
eps = 0.01;

// Ventana de la CYD: centrada sobre el area visible, con holgura
// Labio izquierdo 4 mm mas hacia dentro (validado en probeta 24 ago: la CYD
// encaja y alinea perfecta; solo asomaba borde negro por la izquierda).
cyd_lip_left = 4;
cyd_win_w  = cyd_vis_w + cyd_win_clear - cyd_lip_left;
cyd_win_h  = cyd_vis_h + cyd_win_clear;
cyd_win_dx = cyd_vis_dx - cyd_win_clear/2 + cyd_lip_left;
cyd_win_dy = cyd_vis_dy - cyd_win_clear/2;
// Rebaje trasero del modulo, centrado sobre la ventana
cyd_pocket_depth = panel_t - cyd_bezel;
cyd_spacer_h     = cyd_mod_protr - cyd_pocket_depth;   // 2,1 mm
// El rebaje del modulo NO se deriva de la ventana: el labio izquierdo extra
// recorta la ventana pero el modulo fisico sigue donde estaba (validado en
// probeta). Centro sobre el area visible original, sin el labio.
cyd_mod_cx = cyd_vis_dx + cyd_vis_w/2;
cyd_mod_cy = cyd_vis_dy + cyd_vis_h/2;
cyd_pocket_x0 = cyd_mod_cx - (cyd_mod_w + cyd_mod_clear)/2;
cyd_pocket_x1 = cyd_mod_cx + (cyd_mod_w + cyd_mod_clear)/2;
// Rebaje trasero del cristal del OLED

// ---------------------------------------------------------------------------
// Avisos en la consola
// ---------------------------------------------------------------------------
assert(panel_w <= 220 && panel_h <= 220, "El panel no cabe en la cama de 220x220");

// Los tornillos de la CYD tienen que caer FUERA del rebaje del modulo: ahi el
// panel conserva su espesor entero y la cabeza apoya en macizo. Si cayeran
// dentro, solo quedarian panel_t - cyd_pocket_depth = 1,5 mm y se rasgarian.
cyd_head_r  = (cyd_cbore ? cyd_cbore_d : 5.5) / 2;
cyd_screw_x = [for (q = cyd_screw_xy) q[0]];
assert(!cyd_screws ||
       (min(cyd_screw_x) + cyd_head_r <= cyd_pocket_x0 &&
        max(cyd_screw_x) - cyd_head_r >= cyd_pocket_x1),
       str("Algun tornillo de la CYD pisa el rebaje del modulo (x ",
           cyd_pocket_x0, " a ", cyd_pocket_x1, "). Estrecha el rebaje, ",
           "mueve los tornillos o desactiva el avellanado."));

cyd_wall = panel_t - (cyd_cbore ? cyd_cbore_dep : 0);
assert(!cyd_screws || cyd_wall >= 2.0,
       str("Pared de solo ", cyd_wall, " mm en los tornillos de la CYD."));
echo(str("Pared en los tornillos de la CYD: ", cyd_wall, " mm | ",
         "rebaje del modulo de x=", cyd_pocket_x0, " a ", cyd_pocket_x1));
echo(str("Bisel de la CYD: ", cyd_bezel, " mm | espaciadores de ",
         cyd_spacer_h, " mm"));
echo(str("Panel ", panel_w, " x ", panel_h, " x ", panel_t, " mm"));
echo(str("Margen de rosca del pote: ", pot_thread_len - panel_t,
         " mm para tuerca + arandela (hacen falta ~3,0)"));

// ---------------------------------------------------------------------------
// Utilidades
// ---------------------------------------------------------------------------
module rounded_rect(w, h, r) {
    offset(r = r) offset(delta = -r) square([w, h], center = false);
}

// Agujero de mando con espiga antigiro REDONDA (el selector de palanca)
module control_hole(d, antirot, ar_d, ar_r, ar_ang) {
    circle(d = d);
    if (antirot)
        translate([ar_r * cos(ar_ang), ar_r * sin(ar_ang)]) circle(d = ar_d);
}

// Agujero de potenciometro: rosca + ranura RECTANGULAR para la pletina.
// El rectangulo se gira (ang - 90) para que su lado largo quede siempre
// tangente a la circunferencia, sea cual sea el angulo elegido.
module pot_hole(clear = pot_antirot_clear) {
    circle(d = pot_thread_d + pot_clear);
    if (pot_antirot)
        translate([pot_antirot_r * cos(pot_antirot_ang),
                   pot_antirot_r * sin(pot_antirot_ang)])
            rotate(pot_antirot_ang - 90)
                square([pot_antirot_w + clear, pot_antirot_h + clear],
                       center = true);
}

function pot_x(i) = pot_x0 + i * pot_pitch;

// Huella del rebaje del modulo de la CYD, con descarga en las esquinas: una
// esquina impresa nunca sale viva, y la del modulo si lo es. Sin la descarga
// el modulo apoya en los cuatro radios y se queda sin asentar.
module mod_pocket_2d() {
    w = cyd_mod_w + cyd_mod_clear;
    h = cyd_mod_h + cyd_mod_clear;
    square([w, h], center = true);
    for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * w/2, sy * h/2]) circle(r = cyd_corner_r);
}

// ---------------------------------------------------------------------------
// Hueco del OLED, INJERTADO tal cual del STL de referencia (ver bloque 5).
// ---------------------------------------------------------------------------
// El STL es un objeto SOLIDO (el frame que alguien se imprimiria aparte).
// Para convertirlo en el "hueco" que necesitamos, se resta ese solido de un
// bloque que ocupa exactamente su misma caja: lo que queda es el negativo
// exacto de la pieza -- la ventana, los 4 taladros y el hueco de los pines,
// tal cual estan en la malla, sin volver a medir nada a mano.
module oled_frame_void() {
    // z=0 es la cara VISTA; +z hacia dentro. Todo en mm.
    e = 0.02;
    seat_d = panel_t - oled_lip_t - oled_glass_protr;  // asiento de la PCB

    // nivel 3: ventana de la pantalla, pasante en el labio
    translate([0, oled_win_dy, -e]) linear_extrude(panel_t + 2*e)
        square([oled_win_w, oled_win_h], center = true);
    // nivel 2: hueco del cristal entero, desde detras del labio
    translate([0, oled_glass_dy, oled_lip_t]) linear_extrude(panel_t)
        square([oled_glass_w + oled_glass_clear,
                oled_glass_h + oled_glass_clear], center = true);
    // nivel 1: asiento de la PCB, desde la cara trasera
    translate([0, 0, panel_t - seat_d]) linear_extrude(seat_d + e)
        square([oled_pcb_w + oled_pcb_clear, oled_pcb_h + oled_pcb_clear],
               center = true);
    // taladros pasantes
    for (sx = [-1, 1], sy = [-1, 1])
        translate([sx*oled_hole_pitch_x/2, oled_hole_dy + sy*oled_hole_pitch_y/2, -e])
            cylinder(h = panel_t + 2*e, d = oled_screw_d);
    // descarga de las puntas de los pines
    translate([0, oled_pin_y, oled_pin_wall])
        linear_extrude(panel_t - oled_pin_wall + e)
            square([oled_pin_w, oled_pin_h], center = true);
    // Canal del flex: va del borde exterior de la PCB hasta empalmar con el
    // hueco del cristal, todo a la profundidad de la descarga de los pines.
    // Asi el flex nunca queda pinzado, y lo unico que se queda a media altura
    // (el asiento) son las islas donde apoya la PCB: la franja de arriba y
    // las dos esquinas de abajo, que es donde caen los taladros.
    flex_y_out = -(oled_pcb_h/2 + oled_flex_ext);
    flex_y_in  = oled_glass_dy - (oled_glass_h + oled_glass_clear)/2;
    translate([0, (flex_y_out + flex_y_in)/2, oled_pin_wall])
        linear_extrude(panel_t - oled_pin_wall + e)
            square([oled_flex_w, flex_y_in - flex_y_out + e], center = true);
}

module oled_frame_cut(cx, cy) {
    translate([cx, cy, panel_t])
        mirror([0, 0, 1])
            oled_frame_void();
}

// ---------------------------------------------------------------------------
// Contorno 2D del panel con todas las perforaciones pasantes
// ---------------------------------------------------------------------------
module panel_2d() {
    difference() {
        rounded_rect(panel_w, panel_h, corner_r);

        // -- potenciometros
        for (i = [0 : pot_count - 1])
            translate([pot_x(i), pot_row_y]) pot_hole();

        // -- selector de tipo de filtro
        translate([sw_x, sw_y])
            control_hole(sw_thread_d + sw_clear, sw_antirot,
                         sw_antirot_d, sw_antirot_r, sw_antirot_ang);

        // -- jack de audio (solo si vuelve al frente)
        if (jack_on_panel)
            translate([jack_x, jack_y]) circle(d = jack_thread_d + jack_clear);

        // -- ventana de la CYD, calada en el bisel
        translate([cyd_x0 + cyd_win_dx, cyd_y0 + cyd_win_dy])
            square([cyd_win_w, cyd_win_h]);

        // -- taladros de la CYD (desactivados por defecto)
        if (cyd_screws)
            for (p = cyd_screw_xy)
                translate([cyd_x0 + p[0], cyd_y0 + p[1]])
                    circle(d = cyd_screw_d);

        // El hueco del OLED (ventana + taladros + zona de pines) ya NO se corta
        // aqui: es 3D, no un simple through-cut, y se resta aparte en panel()
        // con oled_frame_cut(). Ver bloque 5 mas arriba.

        // -- taladros de fijacion al cuerpo
        if (mount_holes)
            for (x = [mount_inset, panel_w - mount_inset],
                 y = [mount_inset, panel_h - mount_inset])
                translate([x, y]) circle(d = mount_hole_d);
    }
}

// ---------------------------------------------------------------------------
// Rebajes de la cara trasera (z = 0). El centro de cada rebaje es la ventana
// pasante, asi que el techo del rebaje es solo un marco de 2,5 a 13,5 mm:
// se imprime sin soportes y los puentes son cortos.
// ---------------------------------------------------------------------------
module back_pockets() {
    // Hueco del MODULO de la CYD. Su techo es el anillo del bisel, de 2,25 a
    // 4,75 mm de ancho: puentes cortos, se imprime sin soportes.
    translate([cyd_x0 + cyd_mod_cx, cyd_y0 + cyd_mod_cy, -eps])
        linear_extrude(cyd_pocket_depth + eps)
            mod_pocket_2d();

}

// ---------------------------------------------------------------------------
// Avellanados de la cara vista (z = panel_t). Se abren hacia arriba, asi que
// no hay puentes que imprimir.
// ---------------------------------------------------------------------------
module front_counterbores() {
    if (cyd_screws && cyd_cbore)
        for (p = cyd_screw_xy)
            translate([cyd_x0 + p[0], cyd_y0 + p[1],
                       panel_t - cyd_cbore_dep])
                cylinder(h = cyd_cbore_dep + eps, d = cyd_cbore_d);
}

// ---------------------------------------------------------------------------
// Etiquetas grabadas en la cara vista (z = panel_t)
// ---------------------------------------------------------------------------
// Tamano que hace que una etiqueta quepa en el ancho disponible, sin pasar
// nunca del maximo. Es lo que evita que SUSTAIN y RELEASE se pisen.
function fit_size(s, maxw) =
    min(label_size, maxw / (len(s) * label_aspect));

module fitted_text(s, maxw = label_max_w) {
    text(s, size = fit_size(s, maxw), font = label_font,
         halign = "center", valign = "center");
}

module labels_2d() {
    for (i = [0 : pot_count - 1])
        translate([pot_x(i), pot_row_y + label_dy])
            fitted_text(pot_names[i]);

    // Selector de filtro: los tres tipos alrededor de la palanca.
    // Arriba HPF, al medio BPF (a la derecha, que en el centro esta el hueco)
    // y abajo LPF. El firmware tiene que mapear 3,3 V -> HPF, 1,65 V -> BPF,
    // 0 V -> LPF para que el panel no mienta.
    translate([sw_x, sw_y + 20]) fitted_text("FILTER");
    translate([sw_x, sw_y + 12]) fitted_text("HPF");
    translate([sw_x + 11, sw_y])  fitted_text("BPF", 14);
    translate([sw_x, sw_y - 11]) fitted_text("LPF");

    if (jack_on_panel)
        translate([jack_x, jack_y - 9]) fitted_text("OUT");
}

module engraved_labels() {
    translate([0, 0, panel_t - label_depth])
        linear_extrude(label_depth + eps) labels_2d();
}

// Solido que RELLENA el grabado. No se imprime y no forma parte del panel:
// existe solo para que conjunto.scad pueda pintarlo de otro color y ver como
// quedaria el rotulador dentro del hueco.
module label_ink() {
    translate([0, 0, panel_t - label_depth])
        linear_extrude(label_depth) labels_2d();
}

module raised_labels() {
    translate([0, 0, panel_t - eps])
        linear_extrude(label_relief + eps) labels_2d();
}

// ---------------------------------------------------------------------------
// Pieza
// ---------------------------------------------------------------------------
module panel() {
    union() {
        difference() {
            linear_extrude(panel_t) panel_2d();
            back_pockets();
            front_counterbores();
            oled_frame_cut(oled_cx, oled_cy);
            if (labels && label_mode == "grabado") engraved_labels();
        }
        if (labels && label_mode == "relieve") raised_labels();
    }
}

// ---------------------------------------------------------------------------
// Probeta de ajuste. Mismo grosor y mismos diametros que el panel de verdad,
// para comprobar tres cosas antes de gastar 2,5 h:
//   1. que la rosca del pote entra en el agujero
//   2. que la tuerca del pote llega y aprieta con panel_t de espesor
//   3. lo mismo con el interruptor de palanca, espiga antigiro incluida
// ---------------------------------------------------------------------------
module coupon() {
    pitch = 18; n = len(slot_clear_test);
    cw = pitch * n + 16; ch = 40; y0 = 26;
    // Rosca y posicion ya estan validadas. Lo unico a decidir es la HOLGURA
    // de la ranura rectangular: de izquierda a derecha, slot_clear_test.
    // Y la misma palabra dos veces: en relieve arriba, grabada abajo.
    union() {
        difference() {
            linear_extrude(panel_t)
                difference() {
                    rounded_rect(cw, ch, 3);
                    for (i = [0 : n-1])
                        translate([14 + i*pitch, y0])
                            pot_hole(slot_clear_test[i]);
                }
            translate([0, 0, panel_t - label_depth])
                linear_extrude(label_depth + eps)
                    translate([cw/2, 7]) fitted_text("SUSTAIN", cw - 10);
        }
        translate([0, 0, panel_t - eps])
            linear_extrude(label_relief + eps)
                translate([cw/2, 15]) fitted_text("SUSTAIN", cw - 10);
    }
}

// ---------------------------------------------------------------------------
// Probeta de VENTANAS. Comprueba lo unico del panel que no sale de un plano
// acotado: donde cae la pantalla de la CYD dentro de su placa. Lleva tambien
// la del OLED, que es barata de incluir. ~30 min.
// Se apoyan las dos placas en sus rebajes por detras y se mira si el area
// visible queda centrada y sin comerse bisel.
// ---------------------------------------------------------------------------
module windows_coupon() {
    m = 3;                                   // margen, al minimo
    cw = m + cyd_pcb_w + 5 + oled_ref_w + m;
    ch = max(cyd_pcb_h, oled_ref_h) + 2*m;
    cx = m; cy = m;                          // esquina inf. izq. de la PCB de la CYD
    ox = m + cyd_pcb_w + 5 + oled_ref_w/2;   // centro del hueco del OLED
    oy = ch / 2;
    difference() {
        linear_extrude(panel_t)
            difference() {
                rounded_rect(cw, ch, 3);
                translate([cx + cyd_win_dx, cy + cyd_win_dy])
                    square([cyd_win_w, cyd_win_h]);
                if (cyd_screws)
                    for (p = cyd_screw_xy)
                        translate([cx + p[0], cy + p[1]]) circle(d = cyd_screw_d);
            }
        translate([cx + cyd_mod_cx, cy + cyd_mod_cy, -eps])
            linear_extrude(cyd_pocket_depth + eps) mod_pocket_2d();
        oled_frame_cut(ox, oy);
    }
}

// Cuatro espaciadores entre el panel y la PCB de la CYD. El modulo entra
// cyd_pocket_depth en el rebaje pero sobresale cyd_mod_protr, asi que la PCB
// queda cyd_spacer_h por detras. Sin ellos, apretar el tornillo aplasta el
// modulo contra el bisel. Dos minutos de impresora.
module spacers() {
    for (i = [0 : 3])
        translate([i * 10, 0, 0])
            difference() {
                cylinder(h = cyd_spacer_h, d = 7);
                translate([0, 0, -eps])
                    cylinder(h = cyd_spacer_h + 2*eps, d = cyd_screw_d);
            }
}

// Probeta MINIMA, solo del OLED, para revalidar sin repetir la CYD (que ya
// quedo bien en la probeta de ventanas). ~5 min de impresora.
module oled_coupon() {
    m = 4; cw = oled_ref_w + 2*m; ch = oled_ref_h + 2*m;
    difference() {
        linear_extrude(panel_t) rounded_rect(cw, ch, 3);
        oled_frame_cut(cw/2, ch/2);
    }
}

if (part == "coupon")            coupon();
else if (part == "ventanas")     windows_coupon();
else if (part == "espaciadores") spacers();
else if (part == "oled_solo")    oled_coupon();
else                              panel();
