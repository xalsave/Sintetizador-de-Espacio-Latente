// ============================================================================
//  caja.scad -- Cuerpo del Sintetizador de Espacio Latente
//  TFG - Bloque C - 23 ago 2026.  Complementa a panel.scad.
//
//  Cuna estilo Moog: 30 mm delante, 62 detras, 16,0 grados, mas una BAHIA
//  TRASERA plana de 58 mm donde vive el shield MIDI TUMBADO (ver aviso en
//  el bloque 4: la trasera esta a medio rehacer y no debe imprimirse aun).
//
//  Dos piezas, ninguna necesita soportes:
//    "bandeja" -> suelo + frontal + laterales. Se imprime con el suelo abajo.
//    "trasera" -> pared trasera + cubierta de la bahia. Se imprime TUMBADA
//                 sobre su cara exterior (girala en la laminadora).
//
//  Nada de separadores de nylon ni de taladros en la veroboard: esta entra
//  deslizando sobre repisas impresas, y el shield en una ranura impresa.
//  Los unicos tornillos son los 4 del panel y los 2 de union de las piezas.
//
//  F5 previsualiza - F6 renderiza - File > Export > Export as STL
// ============================================================================

/* [1. Que pieza exportar] */
part = "conjunto";   // [bandeja, trasera, conjunto, conectores]

/* [2. Caja] */
box_w    = 186;    // = ancho del panel
panel_d  = 116;    // = fondo del panel (medido sobre la pendiente)
h_front  = 30;     // altura de la pared delantera
h_back   = 62;     // altura de la pared trasera
// Fondo de la bahia trasera, por detras del panel.
// El video del 24 ago demostro que el shield va TUMBADO, no de pie: sus DIN
// salen paralelos a la PCB, por el canto, asi que de pie apuntarian al techo.
// Tumbado ocupa 57,4 de fondo, y con bay_d = 30 solo habia 33,5 libres.
// Con 58 quedan 60,5: entran los 57,4 y sobran 3 de aire a la veroboard.
bay_d    = 58;
wall     = 3;      // espesor de pared
floor_t  = 3;      // espesor del suelo
panel_t  = 3.4;    // debe coincidir con panel.scad

/* [3. Veroboard] */
board_w  = 160;  board_h = 100;   // 160 a lo largo de X, 100 a lo largo de Y
board_x0 = 13;   board_y0 = 5;    // esquina delantera izquierda
board_t  = 1.5;                   // espesor de la baquelita
rail_z   = 8;                     // cara inferior de la placa sobre el suelo
                                  // (8 - 3 de suelo = 5 mm para los rabillos)
// La veroboard NO esta taladrada, asi que no hay tornillos: entra DESLIZANDO
// por detras (con la trasera desmontada) sobre dos repisas laterales, y la
// propia trasera hace de tope. Las repisas solo apoyan, sin labio superior:
// los zocalos van por la cara de componentes y un labio chocaria con ellos.
//
// Margenes de baquelita limpia medidos el 23 ago sobre la cara de cobre:
//   canto x = board_x0 + board_w  ->  libre entero, 12 mm de fondo
//   canto x = board_x0            ->  solo 42 mm de largo, 24 mm de fondo
rail_w_right = 8;    // < 12 medidos
rail_w_left  = 8;    // < 24 medidos
rail_len_left = 42;  // tramo util del canto que tiene el zocalo de 22
// Pestanas que impiden que la placa se levante. Van al FRENTE, encima de los
// cantos, y la placa se mete por debajo al deslizar.
tab_w    = 10;   tab_over = 4;   tab_gap = 0.6;

/* [4. Shield MIDI] */
// ###########################################################################
// # PENDIENTE (25 ago): TODO ESTE BLOQUE SIGUE MODELADO PARA EL SHIELD DE   #
// # PIE, Y EL VIDEO DEL 24 DEMOSTRO QUE VA TUMBADO.                         #
// # La bahia ya se ensancho a 58 para que quepa, pero falta rehacer:        #
// #   - shield_cradle_solid() y shield_slot(): la ranura vertical no vale;  #
// #     tumbado necesita cuatro apoyos a la altura del PCB.                 #
// #   - los dos huecos del DIN: ahora se cortan APILADOS en vertical, y     #
// #     tumbado van UNO AL LADO DEL OTRO en horizontal.                     #
// #   - shield_z / din_from_bottom: pasan a medirse desde el suelo de la    #
// #     bahia, con 9 mm de pines colgando por debajo del PCB.               #
// # NO IMPRIMIR LA TRASERA hasta rehacerlo.                                 #
// ###########################################################################
// Medidas del shield real (23 ago): 56 x 52 x 29 con los DIN y la tira de
// pines ya soldados. De los 29: 19,5 el DIN, 5 las patas, 4,5 el plastico.
// Va DE PIE contra la trasera, asi los DIN apuntan a la pared y no al techo.
shield_w = 56;     // ancho del PCB (a lo largo de X)
shield_h = 52;     // alto del PCB (a lo largo de Z)
shield_t = 1.6;
shield_x = 75;     // centro del PCB, en X
shield_z = 3.2;    // borde inferior del PCB sobre el suelo. Con 4 el canto
                   // superior se comia la cubierta por medio milimetro.
slot_clear = 0.5;
slot_h   = 16;     // altura de las guias en U
din_sq   = 19.5;   // el cuerpo del DIN es CUADRADO, 19,5 x 19,5
din_clear = 0.6;
// Posicion del DIN de IN, deducida de la foto acotada del 23 ago:
//   5 mm del canto superior de la PCB al borde alto del DIN
//   -> centro del DIN a 5 + 19,5/2 = 14,75 del canto superior
//   -> o sea a 52 - 14,75 = 37,25 del canto INFERIOR, que es el que apoya
// En horizontal el autor confirma que el DIN va A RAS del canto izquierdo,
// sin volar por fuera -> centro a 19,5/2 = 9,75 de ese canto.
//   !! Queda una inconsistencia de 5,5 mm sin resolver: la cota de 42 del
//   borde derecho del DIN al canto derecho daria una PCB de 19,5 + 42 = 61,5,
//   y la medida directa del conjunto son 56. CONFIRMAR con el pie de rey
//   antes de imprimir la trasera (hoy no se imprime, no corre prisa).
din_from_bottom = 37.25;   // del canto inferior de la PCB al centro del DIN IN
// El shield lleva DOS DIN apilados en el canto izquierdo, con 2,5 mm de aire
// entre cuerpos: 19,5 + 2,5 = 22,0 de centro a centro. El de abajo es el OUT.
// Aunque solo usemos el IN, la pared necesita los dos huecos o el shield no
// entra hasta el fondo.
din_pitch = 22.0;
din_count = 2;
din_from_left   = 9.75;    // del canto izquierdo de la PCB al centro del DIN

/* [5. Conectores de pared] */
jack_d   = 6.3;   jack_y = 55;  jack_z = 22;   // lateral IZQUIERDO
sw_d     = 6.3;   sw_x = 110;   sw_z = 40;     // interruptor de red, trasera
sw_antirot_d = 2.8;  sw_antirot_off = 6.4;
pwr_d    = 12.2;  pwr_x = 160;  pwr_z = 20;    // entrada de alimentacion

/* [6. Union de las dos piezas] */
tongue_d = 6;     // cuanto avanza la lengueta de la trasera sobre el suelo.
                  // 6 y no mas: con 12 se metia debajo de los pilares traseros
                  // de la veroboard, que estan en y = 99.
tongue_t = 3;
// Dos tornillos, y a los lados. En el centro no caben: el macizo sube a
// z = 9 y la veroboard vuela a z = 8. A x = 8 y x = 178 el macizo queda
// fuera de la placa (que ocupa x 13..173) y ademas se funde con la pared.
join_x   = [8, 178];
join_free = 3.4;  join_pilot = 2.6;  pad_h = 6;

/* [7. Panel] */
// Taladros del panel (coordenadas LOCALES del panel, ver panel.scad)
panel_screw_xy = [[7, 7], [179, 7], [7, 109], [179, 109]];
boss_d = 9;
post_pilot = 2.6;   // piloto para M3 autorroscante en plastico

/* [Hidden] */
$fa = 2; $fs = 0.4;
eps = 0.02;
deep    = sqrt(panel_d*panel_d - (h_back-h_front)*(h_back-h_front));  // 111.5
total_d = deep + bay_d;
slope   = (h_back - h_front) / deep;
ang     = atan(slope);

// h_front y h_back son la altura ACABADA, con el panel puesto. El panel tiene
// 3,4 mm medidos perpendiculares a su cara, que sobre la vertical son
// 3,4/cos(16) = 3,54 mm. Las paredes tienen que quedarse esos 3,54 mm por
// debajo: el panel mide 186, exactamente lo mismo que la caja, asi que se
// apoya ENCIMA del borde. No puede encajar entre las paredes -- el hueco
// interior son 180 y le sobran 6 mm.
seat    = panel_t / cos(ang);
hf_wall = h_front - seat;    // 26,46
hb_wall = h_back  - seat;    // 58,46

// Plano del PCB del shield: su cara de los DIN queda a (din_sq - wall) de la
// cara interior de la trasera, porque el cuerpo del conector atraviesa la
// pared y asi recupera esos 3 mm.
shield_y = total_d - wall - (din_sq - wall) - shield_t/2;

echo(str("Fondo del panel en planta: ", deep, " mm | caja ", box_w, " x ", total_d));
echo(str("Angulo de la cuna: ", ang, " grados"));
assert(box_w <= 220 && total_d <= 220, "No cabe en la cama de 220x220");
assert(shield_z + shield_h <= hb_wall - wall,
       str("El shield llega a z=", shield_z + shield_h,
           " y la cubierta empieza en ", hb_wall - wall));
assert(total_d - wall - (din_sq - wall) - shield_t/2 - 9.5 > board_y0 + board_h,
       "La tira de pines del shield choca con la veroboard");
assert(board_y0 + board_h + wall <= deep + bay_d - wall,
       "La veroboard invade la bahia del shield");

// --- altura de la cara superior / inferior del panel a un fondo y dado ------
function z_top(y) = h_front + y * slope;        // cara vista del panel
function z_bot(y) = hf_wall + y * slope;        // donde apoya = borde de pared

// ---------------------------------------------------------------------------
// El cuerpo, como perfil lateral extruido a lo ancho
// ---------------------------------------------------------------------------
// La cubierta de la bahia SI sube hasta h_back: ahi no hay panel, y asi queda
// a ras con la cara superior de este. El escalon en y = deep es justamente el
// tope contra el que apoya el borde trasero del panel.
OUTER = [[0,0], [total_d,0], [total_d,h_back], [deep,h_back],
         [deep,hb_wall], [0,hf_wall]];
INNER = [[wall,floor_t], [total_d-wall,floor_t], [total_d-wall,hb_wall],
         [deep,hb_wall], [deep,h_back+8], [wall,hf_wall+8]];

module profile(pts, w) {
    rotate([90, 0, 90]) linear_extrude(w) polygon(pts);
}

module shell() {
    difference() {
        profile(OUTER, box_w);
        translate([wall, 0, 0]) profile(INNER, box_w - 2*wall);
    }
}

// ---------------------------------------------------------------------------
// Anadidos
// ---------------------------------------------------------------------------

// Repisas laterales sobre las que desliza la veroboard, y las dos pestanas
// delanteras que la sujetan contra el levantamiento.
module board_rails() {
    // canto derecho: libre entero
    translate([board_x0 + board_w - rail_w_right, board_y0, floor_t - eps])
        cube([rail_w_right, board_h, rail_z - floor_t + eps]);
    // canto izquierdo: solo el tramo delantero, el resto lo ocupa el zocalo
    translate([board_x0, board_y0, floor_t - eps])
        cube([rail_w_left, rail_len_left, rail_z - floor_t + eps]);

    // pestanas: pilar hasta la cara superior de la placa + ala que la pisa
    for (s = [0, 1]) {
        x = s == 0 ? board_x0 : board_x0 + board_w - tab_w;
        translate([x, board_y0, floor_t - eps])
            cube([tab_w, 6, rail_z + board_t + tab_gap - floor_t + eps]);
        translate([s == 0 ? board_x0 : board_x0 + board_w - tab_over,
                   board_y0, rail_z + board_t + tab_gap])
            cube([tab_over, 6, 2]);
    }
}

// Torres para los cuatro tornillos del panel. Suben hasta la cara inferior
// del panel; cada una se funde con dos paredes, asi que quedan bien ancladas.
module panel_bosses() {
    for (p = panel_screw_xy) {
        y = p[1] * cos(ang);
        translate([p[0], y, 0]) cylinder(h = z_bot(y), d = boss_d);
    }
}

// Cuna del shield MIDI: dos guias con una ranura vertical. El PCB se desliza
// desde arriba y el propio DIN, metido en su taladro, lo bloquea.
module shield_cradle_solid() {
    for (s = [-1, 1])
        translate([shield_x + s*(shield_w/2 - 4) - 5, shield_y - 6, floor_t - eps])
            cube([10, 12, shield_z - floor_t + slot_h]);
}
module shield_slot() {
    translate([shield_x - shield_w/2 - 1, shield_y - (shield_t + slot_clear)/2,
               shield_z])
        cube([shield_w + 2, shield_t + slot_clear, slot_h + 2*eps]);
}

// Union de las dos piezas, en solape:
// la TRASERA lleva una lengueta que se apoya sobre el suelo de la BANDEJA, con
// tres macizos roscados encima. Los tornillos entran por DEBAJO de la caja, a
// traves del suelo de la bandeja, y muerden 8 mm de plastico macizo. Quedan
// escondidos bajo las patas y no se ven desde ningun angulo.
module tongue_with_pads() {
    translate([wall, deep - tongue_d, floor_t])
        cube([box_w - 2*wall, tongue_d, tongue_t]);
    for (x = join_x)
        translate([x, deep - tongue_d/2, floor_t - eps])
            cylinder(h = pad_h + eps, d = 10);
}

// ---------------------------------------------------------------------------
// Perforaciones
// ---------------------------------------------------------------------------
module holes() {
    // -- jack de audio, pared IZQUIERDA
    translate([-eps, jack_y, jack_z]) rotate([0, 90, 0])
        cylinder(h = wall + 2*eps, d = jack_d);

    // -- DIN-5 del MIDI, pared trasera. NO es redondo: el cuerpo del conector
    // es un cuadrado de 19,5 x 19,5 a ras de la PCB, y atraviesa la pared.
    for (i = [0 : din_count - 1])
        translate([shield_x - shield_w/2 + din_from_left,
                   total_d - wall - eps,
                   shield_z + din_from_bottom - i * din_pitch])
            cube([din_sq + din_clear, wall + 2*eps, din_sq + din_clear],
                 center = true);

    // -- interruptor de red + su espiga antigiro, pared trasera
    translate([sw_x, total_d + eps, sw_z]) rotate([90, 0, 0])
        cylinder(h = wall + 2*eps, d = sw_d);
    translate([sw_x, total_d + eps, sw_z + sw_antirot_off]) rotate([90, 0, 0])
        cylinder(h = wall + 2*eps, d = sw_antirot_d);

    // -- entrada de alimentacion, pared trasera
    translate([pwr_x, total_d + eps, pwr_z]) rotate([90, 0, 0])
        cylinder(h = wall + 2*eps, d = pwr_d);

    // -- pilotos de los tornillos del panel
    for (p = panel_screw_xy) {
        y = p[1] * cos(ang);
        translate([p[0], y, z_bot(y) - 9]) cylinder(h = 9 + eps, d = post_pilot);
    }

    // -- paso de los tornillos de union, por el suelo de la bandeja
    for (x = join_x)
        translate([x, deep - tongue_d/2, -eps])
            cylinder(h = floor_t + 2*eps, d = join_free);

    // -- ranura del shield
    shield_slot();
}

// ---------------------------------------------------------------------------
// Cuerpo completo, y su corte en dos piezas por el plano y = deep
// ---------------------------------------------------------------------------
module body() {
    difference() {
        union() {
            shell();
            board_rails();
            panel_bosses();
            shield_cradle_solid();
        }
        holes();
    }
}

module half(front) {
    big = 400;
    intersection() {
        body();
        if (front) translate([-big/2, -big + deep, -big/2]) cube(big);
        else       translate([-big/2, deep, -big/2]) cube(big);
    }
}

module bandeja() { half(true); }

module trasera() {
    difference() {
        union() { half(false); tongue_with_pads(); }
        // piloto para el M3 autorroscante, desde abajo
        for (x = join_x)
            translate([x, deep - tongue_d/2, floor_t - eps])
                cylinder(h = pad_h + eps, d = join_pilot);
    }
}

// Fantasma del panel, solo para la vista de conjunto
module panel_ghost() {
    translate([0, 0, h_front]) rotate([-ang, 0, 0])
        translate([0, 0, -panel_t])
            linear_extrude(panel_t)
                offset(r = 4) offset(delta = -4) square([box_w, panel_d]);
}

// ---------------------------------------------------------------------------
// Plaquita plana para comprobar los cuatro pasos de pared: los dos DIN del
// MIDI (que van apilados), el jack de 3,5 y la entrada de 9 V. Mismo espesor
// que la pared real, asi que si aqui entra, entra en la caja. ~10 min.
// ---------------------------------------------------------------------------
module proba_conectores() {
    pw = 92; ph = 58;
    din_cx = 22;              // centro de la columna de DIN
    din_cy = ph/2;            // centro de la pareja
    difference() {
        linear_extrude(wall)
            offset(r = 3) offset(delta = -3) square([pw, ph]);
        // los dos DIN, con el mismo paso que en la trasera
        for (i = [0 : din_count - 1])
            translate([din_cx,
                       din_cy + din_pitch/2 - i * din_pitch,
                       -eps])
                linear_extrude(wall + 2*eps)
                    square([din_sq + din_clear, din_sq + din_clear],
                           center = true);
        // jack de audio 3,5
        translate([56, ph/2, -eps])
            cylinder(h = wall + 2*eps, d = jack_d);
        // entrada de alimentacion 9 V
        translate([76, ph/2, -eps])
            cylinder(h = wall + 2*eps, d = pwr_d);
    }
}

if (part == "bandeja")      bandeja();
else if (part == "trasera") trasera();
else if (part == "conectores") proba_conectores();
else {
    bandeja();
    color("#c8d8e8") trasera();
    %panel_ghost();
}
