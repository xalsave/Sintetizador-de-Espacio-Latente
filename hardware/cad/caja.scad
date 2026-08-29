// ============================================================================
//  caja.scad -- Cuerpo del Sintetizador de Espacio Latente
//  TFG - Bloque C - 23 ago 2026.  Complementa a panel.scad.
//
//  Cuna estilo Moog: 30 mm delante, 62 detras, 16,0 grados, mas una BAHIA
//  TRASERA plana de 58 mm donde vive el shield MIDI TUMBADO. Quedan tres
//  cotas del shield por medir (marcadas en el bloque 4) antes de imprimirla.
//
//  TRES piezas, y ninguna necesita soportes:
//    "bandeja"          -> suelo + frontal + laterales. Se imprime con el
//                          suelo sobre la cama.
//    "trasera_carcasa"  -> pared trasera + cubierta + los dos laterales de la
//                          bahia. Se imprime TUMBADA SOBRE LA CARA EXTERIOR:
//                          asi la cubierta y los laterales son paredes
//                          verticales y los huecos del DIN salen como
//                          agujeros verticales pasantes, sin puentes.
//    "trasera_suelo"    -> la plancha del suelo de la bahia con los pilares,
//                          los tacos de tope y las columnas. Plana sobre la
//                          cama, columnas hacia arriba.
//  La trasera se parte en dos porque de una pieza la cubierta de la bahia es
//  un voladizo de 63 mm. Partida, cada mitad va en su orientacion natural.
//
//  Nada de separadores de nylon ni de taladros en la veroboard: esta entra
//  deslizando sobre repisas impresas, y el shield MIDI va tumbado sobre
//  pilares con una costilla de tope detras. Los tornillos van siempre contra
//  TUERCA EMBUTIDA, nunca roscando en el plastico.
//
//  F5 previsualiza - F6 renderiza - File > Export > Export as STL
// ============================================================================

/* [1. Que pieza exportar] */
part = "conjunto";   // [bandeja, trasera_carcasa, trasera_suelo, conjunto, conectores, trasera]

/* [2. Caja] */
box_w    = 186;    // = ancho del panel
panel_d  = 116;    // = fondo del panel (medido sobre la pendiente)
h_front  = 44;     // altura de la pared delantera
h_back   = 62;     // altura de la pared trasera
// Fondo de la bahia trasera, por detras del panel.
// El video del 24 ago demostro que el shield va TUMBADO, no de pie: sus DIN
// salen paralelos a la PCB, por el canto, asi que de pie apuntarian al techo.
// Tumbado ocupa 57,4 de fondo, y con bay_d = 30 solo habia 33,5 libres.
// Con 58 quedan 60,5: entran los 57,4 y sobran 3 de aire a la veroboard.
// 66 y no 58: con 58 la huella del shield (57,4 + 3 de tope = 60,4) era mas
// larga que la bahia util y CRUZABA la linea de particion, dejando media
// sujecion en cada pieza. Con 66 la bahia util es de 63 y el montaje entero
// queda dentro de la TRASERA, que se imprime de una pieza.
// La linea de particion bandeja/trasera ya NO es el borde del panel: se
// retrasa a split_y para que las cabezas de las torres del panel quepan
// enteras en la bandeja. La bahia crece en consecuencia.
split_y  = 118;
bay_d    = 72;
wall     = 3;      // espesor de pared
floor_t  = 3;      // espesor del suelo
panel_t  = 3.4;    // debe coincidir con panel.scad

/* [3. Veroboard] */
board_w  = 166;  board_h = 100;   // 166 a lo largo de X, 100 a lo largo de Y
board_x0 = 13;   board_y0 = 5;    // esquina delantera izquierda
board_t  = 1.5;                   // espesor de la baquelita
rail_z   = 8;                     // cara inferior de la placa sobre el suelo
                                  // (8 - 3 de suelo = 5 mm para los rabillos)
// La veroboard NO esta taladrada, asi que no hay tornillos: entra DESLIZANDO
// por detras (con la trasera desmontada) y la propia trasera hace de tope.
// Para que eso sea posible, la sujecion tiene que ser un CANAL de seccion
// constante y abierto por detras. Cada canto lleva tres piezas:
//   repisa -> apoya la placa por la cara de cobre
//   pilar  -> pared vertical PEGADA AL LATERAL DE LA CAJA, en los 10 mm
//             libres que hay entre la pared (x=3 / x=183) y el canto
//   pinza  -> labio que vuela sobre la cara de componentes e impide que la
//             placa se levante una vez dentro
// El pilar va SIEMPRE por fuera de la huella de la placa. (26 ago: las
// pestanas antiguas nacian DENTRO de esa huella y hacian el montaje
// fisicamente imposible; ver la nota larga en board_rails.)
//
// Margenes de baquelita limpia, medidos en las DOS caras (26 ago):
//   cara de cobre (donde pisa la repisa) -> 12 mm en el canto
//     x = board_x0 + board_w y 24 mm en el canto x = board_x0
//   cara de componentes (donde pisa la pinza) -> 12 mm en los dos cantos
// Por debajo los dos cantos estan limpios en los 100 mm de largo, asi que
// las DOS repisas corren la placa entera. Esto corrige la nota anterior,
// que limitaba el apoyo del canto x = board_x0 a 42 mm.
rail_w_right = 8;    // < 12 medidos
rail_w_left  = 8;    // < 24 medidos
board_side_gap = 0.5;  // aire lateral por cada lado, entre canto y pilar
// La PINZA si tiene un lado corto: el zocalo de 22 pines va pegado a uno de
// los cantos por la CARA DE COMPONENTES y solo deja limpios 42 mm de ese
// canto. Ahi la pinza mide tab_len_socket; en el otro canto corre los 100.
//
// DONDE VA EL ZOCALO (fijado por el autor el 26 ago): mirando el
// instrumento de frente, con la placa puesta y la cara de componentes hacia
// arriba, el zocalo queda en la esquina TRASERA DERECHA. Es decir: canto
// x = board_x0 + board_w, y en la mitad de ATRAS de ese canto -- es lo
// ultimo que entra al deslizar.
//
// Y no podria ser de otra forma: los 42 mm limpios TIENEN que ser los
// delanteros. Si el zocalo cayera en la mitad delantera, ese canto no
// admitiria pinza de ninguna longitud, porque el zocalo tendria que pasar
// por debajo de ella durante la insercion.
socket_side    = "right"; // [left, right]  canto donde vive el zocalo de 22
                          // "right" = x = board_x0 + board_w
tab_len_socket = 40;      // el canto limpio son 42; se dejan 2 de margen
tab_over = 4.0;   // cuanto pisa la pinza sobre la placa
tab_t    = 2;     // espesor de la pinza
tab_gap  = 0.8;   // aire entre la cara de componentes y la pinza. Generoso a
                  // proposito: la cara baja de la pinza es un voladizo de
                  // 3,5 mm y su primera capa descuelga algo al imprimir
tab_lead  = 2;    // chaflan de entrada de la pinza (= tab_t -> 45 grados)
rail_lead = 3;    // rampa de entrada de la repisa. Sube los 5 mm en 3 y no
                  // pasa nada: es una cara vista POR ABAJO, cada capa es
                  // mas corta que la anterior, no hay voladizo. Corta,
                  // para dejar 97 de los 100 con apoyo plano

/* [4. Shield MIDI -- TUMBADO] */
// El video del 24 ago fijo la postura: la placa va TUMBADA (PCB horizontal),
// los pines de la tira colgando hacia abajo, y los DIN salen PARALELOS a la
// PCB por uno de sus cantos. Ese canto se apoya contra la trasera y los DIN
// atraviesan la pared.
//
// CERTEZA ALTA (se ve en el video y en la foto acotada):
shield_pcb_t   = 1.2;    // espesor de la PCB del shield
shield_pin_drop = 9;     // cuanto cuelgan los pines por debajo de la PCB
din_sq   = 20;         // cuerpo del DIN, cuadrado
din_clear = 0.6;
din_pitch = 22.0;        // 19,5 de cuerpo + 2,5 de aire, centro a centro
din_count = 2;           // IN y OUT, UNO AL LADO DEL OTRO en horizontal
din_z_over_pcb = 9.75;   // centro del DIN sobre la cara superior de la PCB
shield_floor_gap = 12;    // aire entre la punta de los pines y el suelo

// !! PENDIENTE DE MEDIR -- estos tres son estimaciones, no medidas:
shield_w = 53.1;   // canto que apoya contra la trasera (57,4 o 53,1?)
shield_d = 57.4;   // cuanto entra hacia dentro de la caja
shield_x = 75;     // centro de la placa en X
// Del canto izquierdo de la placa al centro del DIN de IN. El autor midio
// ~15,5 pero sin fijar desde que canto con la placa ya en su postura.
din_from_left = 15.6;

/* [4bis. Apoyo del shield -- PROVISIONAL] */
// Cuatro pilares en las esquinas de la huella. NO esta comprobado que libren
// las tiras de pines: en un shield de formato Arduino los conectores van por
// los cantos, asi que puede que haya que moverlos hacia dentro. Medir donde
// hay hueco libre por debajo antes de imprimir la trasera.
shield_post_d = 7;
shield_post_inset = 10;   // de la esquina de la huella hacia dentro
// TOPE TRASERO. Sin el, al enchufar el cable MIDI el shield se iria hacia
// dentro: los pilares solo lo sostienen, no lo retienen. Esta costilla va
// justo detras del canto trasero de la placa y encaja la fuerza de insercion
// contra la propia trasera. El shield se coloca bajandolo en vertical: el
// canto cae DELANTE de la costilla y ya no puede retroceder.
shield_stop = true;
shield_stop_t = 3;     // espesor de la costilla
shield_stop_gap = 0.4;  // aire entre el canto del shield y la costilla
shield_stop_up = 3;    // cuanto sube por encima de la cara inferior del PCB
// RETENCION LATERAL: aletas cortas en los propios pilares, que solo suben
// DESDE la cara inferior del PCB. Debajo no hay nada, asi que los tres hilos
// del MIDI salen por donde quieran. Unas costillas de suelo a PCB habrian
// encerrado el hueco de los pines.
shield_side_ribs = true;
shield_rib_t = 3;        // espesor de la aleta
shield_rib_clear = 0.4;  // aire entre el canto del PCB y la aleta
shield_rib_up = 3;       // cuanto sube la aleta por encima del PCB
// El tope trasero tampoco es corrido: son dos tacos en los extremos, y por el
// hueco central pasan los cables.
shield_stop_w = 15;      // ancho de cada taco

/* [5. Conectores de pared] */
// El jack va en la TRASERA, junto al MIDI y en el extremo opuesto al de la
// entrada de 9 V. Se aprovecha que esa pieza ya se imprime tumbada.
// Mirando la pared trasera DESDE FUERA, la X crece hacia la izquierda: por
// eso un jack_x pequeno lo deja en la esquina derecha vista desde detras.
jack_x   = 18;    // posicion a lo ancho de la trasera
jack_z   = 22;    // altura sobre el suelo
jack_d   = 6.3;
// La rosca del jack mide solo 5,5 de largo: con 3 de pared asomarian 2,5,
// que no da para la tuerca. Se rebaja el cuerpo (9 x 10,5) por la cara
// INTERIOR para que la rosca salga mas y la tuerca agarre bien.
jack_recess   = 1.5;    // deja 1,5 de pared -> asoman 4,0 de rosca
// El cuerpo NO esta centrado en el eje del jack: mide 4,5 por un lado y 6,0
// por el otro. El lado de 4,5 va ARRIBA. Se le dan 0,2 de juego por cara.
jack_body_w    = 9.0;   // ancho del cuerpo, sobre el eje X
jack_body_up   = 4.5;   // del eje del jack al limite superior
jack_body_down = 6.0;   // del eje al limite inferior
jack_body_play = 0.2;   // juego por cara
// Interruptor de red: al lado de la entrada de 9 V y a su misma altura, que
// es donde tiene sentido -- los dos son de instalacion, no de uso.
sw_d     = 6.3;   sw_x = 145;   sw_z = 20;
sw_antirot_d = 2.8;  sw_antirot_off = 6.4;
pwr_d    = 12.2;  pwr_x = 160;  pwr_z = 20;    // entrada de alimentacion

/* [6. Union de las dos piezas] */
// Union trasera_suelo <-> bandeja: DOS PIES macizos que bajan hasta z=0 y
// encajan en sendos bolsillos pasantes recortados en el suelo de la bandeja.
// Sustituye a la lengueta corrida: aquella era un carril de 3 mm en voladizo
// que ni imprimia bien ni agarraba. El pie es macizo desde la cama (cero
// voladizo), el bolsillo lo posiciona en X e Y, y el tornillo verticales lo
// aprieta en Z contra su tuerca embutida en la cara alta.
join_foot_w    = 9;    // ancho del pie (en X)
join_foot_len  = 12;    // cuanto avanza el pie sobre la bandeja (en Y)
join_foot_clear = 0.8;  // holgura del bolsillo, por cara (boquilla 0,2:
                        // los tornillos aprietan, un poco de baile da igual)
join_skin_t     = 1.2;  // piel de suelo que la bandeja CONSERVA bajo el pie:
                        // el bolsillo ya no es pasante, y el tornillo
                        // atraviesa esa piel para unir de verdad las piezas.
                        // El pie queda a 1,2 de la cama al imprimir: es el
                        // voladizo minimo (un puente corto de 10 mm)
// Dos tornillos, y a los lados. En el centro no caben: el macizo sube a
// z = 9 y la veroboard vuela a z = 8. A x = 8 y x = 178 el macizo queda
// fuera de la placa (que ocupa x 13..173) y ademas se funde con la pared.
join_x   = [8, 178];
function join_y() = split_y - join_foot_len/2;   // centro del pie y su tornillo
join_free = 3.8;  pad_h = 9;
// Alojamiento de la cabeza en la cara inferior del suelo, para que no
// sobresalga y la caja apoye plana.
join_head_d    = 5.4;    // diametro del hueco de la cabeza
join_head_deep = 2.6;    // profundidad
// TUERCAS EMBUTIDAS, no rosca en el plastico: el PLA aguanta tres montajes y
// al cuarto gira en vacio, y ademas el apriete depende de la tolerancia de
// impresion. Se mete una tuerca M3 en un hueco hexagonal y el tornillo tira
// de ella. M3: 5,5 entrecaras y 2,4 de espesor, mas holgura de impresion.
nut_af   = 5.9;   // entrecaras + holgura
nut_th   = 2.7;   // espesor + holgura
nut_free = 3.8;   // paso del tornillo a traves del plastico

/* [6bis. Particion de la trasera en dos impresiones] */
// La trasera se parte en SUELO y CARCASA porque en una sola pieza la cubierta
// de la bahia es un voladizo de 63 mm que obliga a soportes. Partida:
//   suelo    -> plano sobre la cama, columnas hacia arriba. Sin soportes.
//   carcasa  -> tumbada sobre su cara exterior; la cubierta y los laterales
//               pasan a ser paredes verticales y los huecos del DIN quedan
//               como agujeros verticales pasantes. Sin soportes.
// Se unen con cuatro M3 desde abajo contra tuerca embutida, igual que el
// resto de la caja.
split_gap  = 0.4;    // aire entre las dos piezas
sj_inset_y  = 14;    // de los extremos de la bahia
sj_boss_d   = 10;    // lado del macizo, pegado al lateral
sj_boss_h   = 12;    // alto del macizo sobre la plancha
// Agujero de los cuatro macizos sj, parametrizable:
sj_hole_d       = 3.8;    // M3 + holgura
sj_hole_through = true;   // true = pasante y visible por dentro
                          // false = ciego, con la profundidad de abajo
sj_hole_depth   = 9;      // profundidad si es ciego, desde la cara exterior
sj_wall_hole_d  = 3.8;    // el mismo agujero, pero en el lateral de la
                          // carcasa: se parametriza aparte por si conviene
                          // darle mas holgura que al del macizo

// Union LATERAL carcasa <-> pared de la bandeja: un bloque por lado, pegado
// a la cara interior del lateral de la carcasa, que asoma unos mm por delante
// de la particion y aterriza contra la cara interior del lateral de la
// bandeja. Un tornillo horizontal desde fuera atraviesa la pared de la
// bandeja y el bloque. En la orientacion de impresion de la carcasa (tumbada
// sobre la cara trasera) el bloque es una columna vertical fusionada al
// lateral, sin soportes, con chaflan de arranque a 45 grados.
side_join       = true;
side_block_w    = 10;    // cuanto entra el bloque hacia dentro desde la pared
side_block_len  = 24;    // largo total en Y (parte asoma delante de split_y)
side_block_over = 12;     // cuanto asoma por delante de la particion
side_block_z0   = 24;    // cara inferior del bloque
side_block_h    = 12;    // alto
side_hole_d     = 3.8;   // taladro del bloque
side_wall_hole_d = 3.8;  // taladro en la pared de la bandeja (mas holgura)
side_hole_y     = 112;   // posicion Y del tornillo (en el tramo que asoma)
side_hole_z     = 30;    // altura del tornillo
side_tri_rot    = 0;     // giro del triangulo alrededor de su arista de pared
                         // (grados; por si la orientacion no cae bien)
side_tri_len    = 10;    // cuanto se extiende el triangulo hacia los
                         // conectores (10 = hipotenusa a 45 grados)
// El paso atraviesa pared + macizo ENTERO, para que la punta del M3 x 20
// salga por el otro lado y agarre en todo el recorrido. Lo que NO puede hacer
// es seguir hasta el infinito: antes cruzaba la bahia y perforaba las
// columnas del shield.

/* [7. Panel] */
// Taladros del panel (coordenadas LOCALES del panel, ver panel.scad)
panel_screw_xy = [[7, 7], [179, 7], [7, 109], [179, 109]];
panel_screw_free = 3.6;   // taladro de paso del tornillo del panel en las
                          // cabezas de la bandeja (M3 + holgura)
// La cabeza de la torre se corta con el MISMO plano del panel y lleva la
// tuerca metida dentro, no en la cara: asi queda material por encima y el
// apriete no depende de una pared fina. El taladro y el hexagono van
// alineados con la NORMAL del panel, no con la vertical, para que el tornillo
// entre recto. Como esa cabeza va inclinada, se hace mas gruesa que el cuerpo
// para que el taladro no se salga por el costado.
boss_head_d   = 13;   // diametro de la cabeza inclinada
boss_head_h   = 12;   // cuanto baja la cabeza desde el plano de apoyo
boss_nut_deep = 16;    // a que profundidad queda la cara alta de la tuerca
boss_slot_ext = 8;    // ranura para meter la tuerca de lado
gusset_w  = 9;        // cuanto sale la cartela desde el lateral
gusset_l  = 12;       // largo de la cartela, en Y
gusset_z0 = 16;       // arranca por encima de los macizos de union (z 3..15)
panel_gusset = false; // cartela de apoyo. Desactivada: la cabeza ya se funde
                      // con el lateral por si sola.

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

// Alturas del shield tumbado, todas encadenadas desde el suelo de la bahia:
shield_pcb_z = floor_t + shield_floor_gap + shield_pin_drop;  // cara inferior
shield_top_z = shield_pcb_z + shield_pcb_t;                   // cara superior
din_z        = shield_top_z + din_z_over_pcb;   // altura del centro de AMBOS
// El canto de los DIN se apoya contra la cara interior de la trasera
shield_y     = total_d - wall;

echo(str("Fondo del panel en planta: ", deep, " mm | caja ", box_w, " x ", total_d));
echo(str("Angulo de la cuna: ", ang, " grados"));
assert(box_w <= 220 && total_d <= 220, "No cabe en la cama de 220x220");
assert(din_z + (din_sq + din_clear)/2 <= h_back - wall,
       str("El hueco del DIN llega a z=", din_z + (din_sq + din_clear)/2,
           " y la pared solo tiene ", h_back));
assert(shield_y - shield_d - shield_stop_gap - (shield_stop ? shield_stop_t : 0) >= board_y0 + board_h,
       str("El shield tumbado invade la veroboard: llega a y=",
           shield_y - shield_d, " y la placa acaba en ", board_y0 + board_h));
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

// Cubo definido por dos esquinas opuestas, en cualquier orden. Los dos
// canales son simetricos pero crecen en sentidos opuestos, y escribirlos con
// translate + cube obligaba a repartir min() y abs() por todas partes.
module blk(xa, xb, ya, yb, za, zb) {
    translate([min(xa, xb), min(ya, yb), min(za, zb)])
        cube([abs(xb - xa), abs(yb - ya), abs(zb - za)]);
}

// Canales laterales por los que desliza la veroboard.
//
// POR QUE ESTO ESTABA MAL (26 ago). Las dos pestanas antiguas nacian en
// x = board_x0 y en x = board_x0 + board_w - tab_w, es decir DENTRO de la
// huella de la placa, y subian hasta su cara superior. Se comprobo cortando
// el solido de la placa contra bandeja(): la interseccion no era vacia, eran
// dos bloques de 10 x 6 x 1,5 en x 13..23 y x 163..173, y 5..11, z 8..9,5.
// Traducido: la placa chocaba contra sus propias pestanas 6 mm antes de
// llegar al fondo y no habia forma humana de montarla. El resto del recorrido
// estaba limpio, asi que el fallo era solo ese.
//
// COMO SE ARREGLA. El pilar se muda a los 10 mm libres que quedan entre la
// pared de la caja y el canto de la placa, y la unica pieza que invade el
// espacio de la placa es la pinza, que vuela POR ENCIMA. Asi el canal es de
// seccion constante en toda su longitud: se presenta la placa por detras,
// se empuja y entra.
//
//        pared                     placa
//          |   pilar   pinza  ->
//          |####|============            z_lip1  12,3
//          |####|                        z_lip0  10,3   (aire tab_gap)
//          |####|  - - - - - - -  cara de componentes    9,5
//          |####|________________ cara de cobre / repisa  8,0  = rail_z
//          |###########|                                        repisa
//          |___________|__________ suelo                  3,0  = floor_t
//
module board_rails() {
    z_shelf = rail_z;                        // 8,0  donde apoya el cobre
    z_lip0  = rail_z + board_t + tab_gap;    // 10,3 cara baja de la pinza
    z_lip1  = z_lip0 + tab_t;                // 12,3 cara alta de la pinza
    y0 = board_y0;                           // 5    canto delantero
    y1 = board_y0 + board_h;                 // 105  canto trasero = boca

    for (s = [0, 1]) {
        left = (s == 0);
        xw = left ? wall : box_w - wall;                     // cara interior
                                                             // del lateral
        xp = left ? board_x0 - board_side_gap                // cara interior
                  : board_x0 + board_w + board_side_gap;     // del pilar
        xs = left ? board_x0 + rail_w_left                   // hasta donde
                  : board_x0 + board_w - rail_w_right;       // llega la repisa
        xl = left ? xp + tab_over : xp - tab_over;           // vuelo de la pinza
        // La pinza es corta en el canto del zocalo de 22 y larga en el otro.
        tl = (left == (socket_side == "left")) ? tab_len_socket : board_h;

        // 1. Pilar: de la pared al canto de la placa, del suelo a la pinza.
        //    Los 100 mm, en los dos lados.
        blk(xw, xp, y0, y1, floor_t - eps, z_lip0);

        // 2. Repisa: entra rail_w_* por debajo de la placa. Los 100 mm en los
        //    dos lados: la cara de cobre esta limpia en todo el canto.
        blk(xp, xs, y0, y1 - rail_lead, floor_t - eps, z_shelf);
        //    rampa de entrada, para presentar la placa a ciegas
        hull() {
            blk(xp, xs, y1 - rail_lead, y1 - rail_lead + eps,
                floor_t - eps, z_shelf);
            blk(xp, xs, y1 - eps, y1, floor_t - eps, floor_t);
        }

        // 3. Pinza: pisa tab_over mm de la cara de componentes. Nace sobre el
        //    pilar (de xw a xl) para que quede bien anclada.
        blk(xw, xl, y0, y0 + tl - tab_lead, z_lip0, z_lip1);
        //    chaflan de entrada, tambien a 45 grados
        hull() {
            blk(xw, xl, y0 + tl - tab_lead, y0 + tl - tab_lead + eps,
                z_lip0, z_lip1);
            blk(xw, xl, y0 + tl - eps, y0 + tl, z_lip1 - eps, z_lip1);
        }
    }
}

// Torres para los cuatro tornillos del panel. Suben hasta la cara inferior
// del panel; cada una se funde con dos paredes, asi que quedan bien ancladas.
// Semiespacio por encima del plano donde apoya el panel. Sirve para cortar
// las torres con ese mismo angulo en vez de dejarlas planas.
module seat_cut() {
    big = 600;
    translate([0, 0, hf_wall]) rotate([ang, 0, 0])
        translate([-big/2, -big/2, 0]) cube(big);
}

// Marco local de cada torre: origen sobre el plano de apoyo, z local = normal
// del panel. Todo lo que se coloque aqui queda alineado con el panel.
module boss_frame(p) {
    translate([p[0], 0, hf_wall]) rotate([ang, 0, 0])
        translate([0, p[1], 0]) children();
}

module panel_bosses() {
    intersection() {
        difference() {
            union() {
                for (p = panel_screw_xy) {
                    // SOLO la cabeza inclinada, alineada con la normal del
                    // panel. Las torres verticales se han quitado: subian
                    // desde el suelo y se comian los macizos de union de la
                    // trasera con la bandeja.
                    boss_frame(p)
                        translate([0, 0, -boss_head_h])
                            cylinder(h = boss_head_h + 8, d = boss_head_d);
                    if (panel_gusset) {
                        py = p[1] * cos(ang);
                        inw = p[0] < box_w/2;
                        xw  = inw ? wall : box_w - wall - gusset_w;
                        zt  = z_bot(py) + 6;
                        translate([0, py + gusset_l/2, 0]) rotate([90, 0, 0])
                            linear_extrude(gusset_l)
                                polygon(inw
                                    ? [[xw, gusset_z0], [xw + gusset_w, gusset_z0 + gusset_w],
                                       [xw + gusset_w, zt], [xw, zt]]
                                    : [[xw + gusset_w, gusset_z0], [xw, gusset_z0 + gusset_w],
                                       [xw, zt], [xw + gusset_w, zt]]);
                    }
                }
            }
            seat_cut();
        }
        profile(OUTER, box_w);
    }
}

module panel_nut_traps() {
    // En el marco de boss_frame: z local = normal del panel. Antes esto eran
    // cilindros VERTICALES, asi que el tornillo entraba cruzado respecto al
    // agujero del panel. Ahora taladro, tuerca y ranura van los tres en la
    // direccion de la normal, coaxiales con la cabeza.
    for (p = panel_screw_xy)
        boss_frame(p) {
            znut = -(boss_nut_deep + nut_th);
            translate([0, 0, znut])
                cylinder(h = boss_nut_deep + nut_th + 8, d = panel_screw_free);
            translate([0, 0, znut])
                cylinder(h = nut_th, d = nut_af / cos(30), $fn = 6);
            translate([p[0] < box_w/2 ? 0 : -boss_slot_ext, -nut_af/2, znut])
                cube([boss_slot_ext, nut_af, nut_th]);
        }
}


// Cuna del shield MIDI: dos guias con una ranura vertical. El PCB se desliza
// desde arriba y el propio DIN, metido en su taladro, lo bloquea.
module shield_cradle_solid() {
    // Cuatro pilares bajo las esquinas de la huella del shield tumbado.
    for (sx = [-1, 1], sy = [0, 1])
        translate([shield_x + sx * (shield_w/2 - shield_post_inset),
                   shield_y - shield_post_inset - sy * (shield_d - 2*shield_post_inset),
                   floor_t - eps])
            cylinder(h = shield_pcb_z - floor_t + eps, d = shield_post_d);

    // Tope trasero: DOS TACOS en los extremos, no una costilla corrida. Encajan
    // la fuerza de insercion del cable MIDI y dejan libre el hueco del medio,
    // por donde salen los hilos.
    if (shield_stop)
        for (sx = [-1, 1])
            translate([shield_x + sx * shield_w/2
                              - (sx > 0 ? shield_stop_w : 0),
                       shield_y - shield_d - shield_stop_gap - shield_stop_t,
                       floor_t - eps])
                cube([shield_stop_w, shield_stop_t,
                      shield_pcb_z + shield_stop_up - floor_t + eps]);

    // Retencion lateral: cuatro columnas CORTAS, desde el suelo hasta por
    // encima del PCB. Van por fuera del contorno de la placa, y al medir solo
    // shield_post_d de largo dejan el lateral abierto casi entero, asi que
    // los cables siguen saliendo sin problema. Antes eran aletas que
    // arrancaban a la altura del PCB y quedaban flotando en el aire.
    if (shield_side_ribs)
        for (sx = [-1, 1], sy = [0, 1])
            translate([shield_x + sx * (shield_w/2 + shield_rib_clear)
                              - (sx < 0 ? shield_rib_t : 0),
                       shield_y - shield_post_inset - shield_post_d/2
                              - sy * (shield_d - 2*shield_post_inset),
                       floor_t - eps])
                cube([shield_rib_t, shield_post_d,
                      shield_pcb_z + shield_pcb_t + shield_rib_up - floor_t + eps]);
}

module shield_slot() { }   // ya no hay ranura: va tumbado sobre pilares

// Union de las dos piezas, en solape:
// la TRASERA lleva una lengueta que se apoya sobre el suelo de la BANDEJA, con
// tres macizos roscados encima. Los tornillos entran por DEBAJO de la caja, a
// traves del suelo de la bandeja, y muerden 8 mm de plastico macizo. Quedan
// escondidos bajo las patas y no se ven desde ningun angulo.
module join_feet() {
    // Macizos de la cama al tope, fundidos con la plancha del suelo por
    // detras (llegan 2 mm mas alla de split_y).
    // 8 mm fundidos con la plancha del suelo por detras de la particion
    // (mas no: a 9 empezarian los macizos sj). El tramo delantero queda en
    // voladizo sobre la piel de la bandeja, como debe.
    // El pie se recorta al hueco interior (wall + split_gap): centrado en
    // x=8 llegaria hasta x=1, y ese tramo quedaba FUERA de suelo_box, asi que
    // sobrevivia pegado a la carcasa como una pestana espuria.
    for (x = join_x) {
        xa = max(x - join_foot_w/2, wall + split_gap);
        xb = min(x + join_foot_w/2, box_w - wall - split_gap);
        translate([xa, split_y - join_foot_len, join_skin_t])
            cube([xb - xa, join_foot_len + 8, floor_t + pad_h - join_skin_t]);
    }
}

// Tuerca M3 embutida en cada macizo de union, por arriba, y paso del tornillo
// hasta ella. El tornillo entra por DEBAJO de la caja y tira de la tuerca.
module join_nut_traps() {
    for (x = join_x) {
        translate([x, join_y(), floor_t + pad_h - nut_th])
            cylinder(h = nut_th + eps, d = nut_af / cos(30), $fn = 6);
        translate([x, join_y(), join_skin_t - eps])
            cylinder(h = floor_t + pad_h + 2*eps, d = join_free);
    }
}

// ---------------------------------------------------------------------------
// Perforaciones
// ---------------------------------------------------------------------------
module holes() {
    // -- jack de audio, pared IZQUIERDA
    translate([jack_x, total_d + eps, jack_z]) rotate([90, 0, 0])
        cylinder(h = wall + 2*eps, d = jack_d);
    // rebaje del cuerpo, por dentro, para que la rosca asome lo suficiente
    translate([jack_x - jack_body_w/2 - jack_body_play,
               total_d - wall - eps,
               jack_z - jack_body_down - jack_body_play])
        cube([jack_body_w + 2*jack_body_play, jack_recess + eps,
              jack_body_up + jack_body_down + 2*jack_body_play]);

    // -- DIN-5 del MIDI, pared trasera. NO es redondo: el cuerpo del conector
    // es un cuadrado de 19,5 x 19,5 a ras de la PCB, y atraviesa la pared.
    // Los dos DIN, UNO AL LADO DEL OTRO y a la MISMA altura.
    for (i = [0 : din_count - 1])
        translate([shield_x - shield_w/2 + din_from_left + i * din_pitch,
                   total_d - wall/2,
                   din_z])
            cube([din_sq + din_clear, wall + 4*eps, din_sq + din_clear],
                 center = true);

    // -- interruptor de red + su espiga antigiro, pared trasera
    translate([sw_x, total_d + eps, sw_z]) rotate([90, 0, 0])
        cylinder(h = wall + 2*eps, d = sw_d);
    translate([sw_x, total_d + eps, sw_z + sw_antirot_off]) rotate([90, 0, 0])
        cylinder(h = wall + 2*eps, d = sw_antirot_d);

    // -- entrada de alimentacion, pared trasera
    translate([pwr_x, total_d + eps, pwr_z]) rotate([90, 0, 0])
        cylinder(h = wall + 2*eps, d = pwr_d);

    // -- alojamiento de tuerca + paso, en las torres del panel
    panel_nut_traps();

    // -- paso de los tornillos de union, por el suelo de la bandeja
    for (x = join_x) {
        // bolsillo NO pasante: conserva join_skin_t de piel debajo
        translate([x - join_foot_w/2 - join_foot_clear,
                   split_y - join_foot_len - join_foot_clear, join_skin_t])
            cube([join_foot_w + 2*join_foot_clear,
                  join_foot_len + join_foot_clear + 1,
                  floor_t + 2*eps]);
        // paso del tornillo y hueco de su cabeza, a traves de la piel
        translate([x, join_y(), -eps])
            cylinder(h = join_skin_t + 2*eps, d = join_free);
        translate([x, join_y(), -eps])
            cylinder(h = join_head_deep + eps, d = join_head_d);
    }

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

// La particion general va en split_y, pero la CUBIERTA (todo lo que queda
// por encima de hb_wall entre deep y split_y) pertenece entera a la carcasa:
// si se partiera en split_y, la bandeja heredaria una tira de techo de 6,5 mm
// flotando en el aire.
module half(front) {
    big = 400;
    if (front)
        difference() {
            intersection() {
                body();
                translate([-big/2, -big + split_y, -big/2]) cube(big);
            }
            translate([-big/2, deep - eps, hb_wall - eps]) cube(big);
        }
    else
        union() {
            intersection() {
                body();
                translate([-big/2, split_y, -big/2]) cube(big);
            }
            intersection() {
                body();
                translate([-big/2, deep, hb_wall]) cube(big);
            }
        }
}

// Volumen que define la pieza de SUELO: la plancha de la bahia, todo lo que
// va montado encima (pilares, tacos, columnas) y la lengueta de union con la
// bandeja. Se queda por debajo de la cubierta y por dentro de los laterales.
function sj_y() = [split_y + sj_inset_y, total_d - wall - sj_inset_y];

module suelo_box() {
    ztop = shield_pcb_z + shield_pcb_t + shield_rib_up + 1;
    translate([wall + split_gap, split_y - join_foot_len - 1, -eps])
        cube([box_w - 2*wall - 2*split_gap,
              total_d - wall - split_gap - (split_y - join_foot_len - 1),
              ztop]);
}

// Union suelo/carcasa: macizo ENTERO en la pieza de suelo (nace de su propia
// plancha, no depende de la carcasa) y tornillo horizontal desde fuera.
module suelo_join_bosses() {
    for (i = [0, 1], y = sj_y())
        translate([i == 0 ? wall + split_gap : box_w - wall - split_gap - sj_boss_d,
                   y - sj_boss_d/2, floor_t - eps])
            cube([sj_boss_d, sj_boss_d, sj_boss_h]);
}

module suelo_join_traps(d = sj_hole_d) {
    len = sj_hole_through ? wall + split_gap + sj_boss_d + eps : sj_hole_depth;
    for (i = [0, 1], y = sj_y()) {
        zc = floor_t + sj_boss_h/2;
        translate([i == 0 ? -eps : box_w + eps, y, zc])
            rotate([0, i == 0 ? 90 : -90, 0]) cylinder(h = len, d = d);
    }
}

module bandeja() {
    difference() { half(true); side_join_holes(); }
}

module trasera() {
    difference() {
        union() { half(false); join_feet(); }
        join_nut_traps();
    }
}

// Fantasma del panel, solo para la vista de conjunto
// Fantasma del panel, solo para la vista de conjunto. El giro es +ang: con
// -ang el panel se hundia por debajo de la caja y se veia cruzado en diagonal.
module panel_ghost() {
    translate([0, 0, hf_wall]) rotate([ang, 0, 0])
        linear_extrude(panel_t)
            offset(r = 4) offset(delta = -4) square([box_w, panel_d]);
}

// ---------------------------------------------------------------------------
// Probeta de conectores: un recorte UNICO de la trasera real, ancho suficiente
// para llevarse a la vez el jack y los dos DIN con todo su montaje. Como
// ahora los tres conectores viven en la misma pared, ya no hace falta unir
// dos trozos con una pletina: sale de una pieza sola.
// ---------------------------------------------------------------------------
module proba_conectores() {
    x0 = min(shield_x - shield_w/2, jack_x - jack_body_w/2 - 6) - 8;
    x1 = max(shield_x + shield_w/2, jack_x + jack_body_w/2 + 6) + 8;

    y0 = shield_y - shield_d - shield_stop_gap - shield_stop_t - 4;
    zw = max(din_z + (din_sq + din_clear)/2,
             jack_z + jack_body_up) + 5;
    translate([-x0, -y0, 0])
        intersection() {
            body();
            translate([x0, y0, 0]) cube([x1 - x0, total_d - y0, zw]);
        }
}

// Las dos mitades de la trasera. El corte lo define suelo_box(): todo lo que
// cae dentro es la plancha del suelo con sus columnas; el resto -- pared
// trasera, cubierta y laterales -- es la carcasa.
module trasera_suelo() {
    difference() {
        union() {
            intersection() { trasera(); suelo_box(); }
            suelo_join_bosses();
        }
        suelo_join_traps();
    }
}

// Bloques laterales de la carcasa, con su chaflan de arranque a 45 grados
module side_join_blocks() {
    for (i = [0, 1]) {
        m  = i == 0 ? 1 : -1;   // espejo para el lado derecho
        // SIN split_gap: el bloque nace de la propia pared de la carcasa y
        // forma una pieza integra con ella. split_gap queda solo para los
        // macizos sj del suelo.
        x0 = i == 0 ? wall : box_w - wall;
        y0 = split_y - side_block_over;
        translate([x0, y0, side_block_z0]) scale([m, 1, 1]) {
            cube([side_block_w, side_block_len, side_block_h]);
            // Triangulo de refuerzo DETRAS del bloque (lado de los
            // conectores): un cateto apoya en la cara trasera del bloque, el
            // otro corre por la pared, y la hipotenusa queda mirando hacia
            // los conectores. En la impresion de la carcasa (conectores en la
            // cama) ese triangulo queda DEBAJO del bloque y lo sostiene.
            // side_tri_rot lo gira alrededor de la arista de pared por si
            // hay que recolocarlo.
            translate([0, side_block_len, 0]) rotate([0, side_tri_rot, 0])
                linear_extrude(side_block_h)
                    polygon([[0, 0], [side_block_w, 0], [0, side_tri_len]]);
        }
    }
}
module side_join_holes() {
    if (side_join)
        for (i = [0, 1])
            translate([i == 0 ? -eps : box_w + eps, side_hole_y, side_hole_z])
                rotate([0, i == 0 ? 90 : -90, 0]) {
                    cylinder(h = wall + 2*eps, d = side_wall_hole_d);
                    translate([0, 0, wall - eps])
                        cylinder(h = side_block_w + 2*eps, d = side_hole_d);
                }
}

module trasera_carcasa() {
    difference() {
        union() {
            difference() { trasera(); suelo_box(); }
            if (side_join) side_join_blocks();
        }
        suelo_join_traps(sj_wall_hole_d);
        side_join_holes();
    }
}

if (part == "bandeja")               bandeja();
else if (part == "trasera")          trasera();
else if (part == "trasera_suelo")    trasera_suelo();
else if (part == "trasera_carcasa")  trasera_carcasa();
else if (part == "conectores") proba_conectores();
else {
    bandeja();
    color("#c8d8e8") trasera_carcasa();
    color("#9fb8cc") trasera_suelo();
    %panel_ghost();
}
