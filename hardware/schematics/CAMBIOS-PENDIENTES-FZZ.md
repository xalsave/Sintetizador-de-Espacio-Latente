# Cambios pendientes en el Fritzing

> **Fichero base:** `sistema-midi-cyd-daisy-VEROBOARD-FINAL.fzz` (16 ago, 02:31)
> **Fichero destino:** `sistema-midi-cyd-daisy-VEROBOARD-FINAL-v2.fzz` — **ya creado**
> (copia del FINAL hecha el 21 ago). Trabajar sobre la v2; el FINAL no se toca.
>
> **La especificación que manda es `docs/veroboard.md` §6sexies.** El §6ter y el
> §6quinquies quedaron anulados el 21 de agosto.

**Revisión del 21 de agosto.** Esta lista se reescribió entera después de decodificar el
`.fzz` hueco a hueco (la propiedad `buses` del stripboard y los 44 cables). **La versión
anterior tenía dos errores que habrían roto el fichero**, anotados abajo para que no se
repitan.

Coordenadas en **(tira, posición)**: tira 1…39 perpendicular al cobre, posición 1…63 a
lo largo. **Tira 1 = raíl GND · tira 2 = raíl +5 V.** *(La versión anterior de este
documento decía tira 1 = +5 V y tira 39 = GND: eso es el §6ter, que nunca llegó al
fichero.)*

---

## 0. Lo que el fichero YA tiene bien (no tocar)

Comprobado net a net el 21 de agosto. Está todo correcto contra el pinout del §2:

- **52 cortes** trazados: 22 del S3 (tiras 1–22, entre pos 6 y 7), 20 del Daisy (tiras
  20–39, entre 41 y 42), 6 de separación (tiras 17–22, entre 19 y 20), 3 de raíles
  locales (tiras 23‑24‑25, entre 47 y 48) y 1 de la rama de la CYD (tira 3, entre 21 y 22).
- Los **4 puentes del SPI**, los 2 hilos de la CYD, el `RX` del MIDI, el jack (punta a
  la tira 37, manguito a la 39 lado A), el OLED y el mazo de los seis potes con el
  selector.
- El **puente de `AGND` que cruza la línea de cortes** (tira 39 pos 35 → `AGND local`).
- **`C3` ya existe**: es el `C9` (idx 10072), 100 nF entre las tiras 20 y 21 en la
  posición 49, o sea entre los pines 40 y 39 del Daisy. Llevaba desde el 8 de agosto
  anotado como pendiente. **Se da por cerrado.**
- **`D1`** (tira 2 → tira 3, pos 41) y su corte de aislamiento.

---

## 1. Los duplicados: cuál es cuál ⚠️ ERROR CORREGIDO

**No están superpuestos.** Son dos juegos distintos y solo uno está conectado:

| Juego | `modelIndex` | Dónde está | Estado |
|---|---|---|---|
| `C4`–`C7` + `C8` | **9007, 9008, 9009, 9010, 9011** | Coordenadas negativas, **fuera del lienzo** | 🗑️ **Huérfanos.** Cuelgan de un breadboard (`modelIndex 7374`) que ya no existe en el fichero. Restos de la protoboard |
| `C4`–`C7` + `C8` | **10348, 10349, 10350, 10351, 10352** | Tira 1 ↔ tira 2, posiciones 19, 23, 27, 31 y 35 | ✅ **Los buenos.** Son el bulk real y el 100 nF del raíl |

> 🔴 **La versión anterior de este documento mandaba borrar los 10348–10352 "por
> duplicados" y conservar los 9007–9011.** Habría borrado el bulk real de la placa y
> dejado cinco componentes fantasma sin conectar a nada.

---

## 2. BORRAR

| Qué | `modelIndex` | Por qué |
|---|---|---|
| `C4`, `C5`, `C6`, `C7`, `C8` **huérfanos** | 9007, 9008, 9009, 9010, 9011 | Restos de la protoboard, sin conexión válida |
| **`R2` y `R3`** | 9004, 9005 | El filtro pasa de 3×10 Ω en paralelo a **una sola 3R3 de 1 W** |
| **Tres de los cuatro** electrolíticos del bulk | 10349, 10350, 10351 | El bulk pasa de 4×100 µF a **un solo 470 µF** |

**Conservar:** `C1` y `C2` (9001, 9002 — los dos 100 µF del filtro), `R1` (9003),
`C9` (10072 — el `C3`), `D1` (9012), `C4` (10348) y `C8` (10352).

Al borrar en Fritzing se van también sus cables. `R2` y `R3` iban de la tira 21 a la 23
(posiciones 53 y 55); esas dos posiciones quedan libres y no hay que heredar nada,
porque `R1` ya ocupa la 51 con las mismas dos tiras.

---

## 3. CAMBIAR valor

| Pieza | idx | Antes | Ahora |
|---|---|---|---|
| **`R1`** | 9003 | 10 Ω | **3,3 Ω**, rotular `R1 — 3R3 1 W FUSIBLE` |
| **`C4`** | 10348 | 100 µF | **470 µF**, rotular `C_BULK — 470 µF` |
| `C1`, `C2` | 9001, 9002 | 100 µF | *sin cambio* — son los dos del filtro del Daisy |
| `C9` | 10072 | 100 nF | *sin cambio* — rotular `C3 — 100 nF (pines 39‑40)` para que se reconozca |

⚠️ El 470 µF real es un **Nichicon FW de ráster 5 mm** y va entre dos tiras contiguas
(2,54 mm): hay que apretarle las patas hacia dentro. En el Fritzing da igual, pero
conviene que el rótulo lo recuerde.

---

## 4. RECOLOCAR: la sección de alimentación se va al final de la placa

Decidido el 21 de agosto (razonamiento en `veroboard.md` §6sexies). El interruptor
necesita que el corte del raíl quede aguas arriba de **todas** las cargas, y la entrada
estaba en la posición 15, por detrás del S3 (que se alimenta en la 11).

| Elemento | Antes | Ahora |
|---|---|---|
| Cable `ALIM +5V` | (tira 2, pos 15) | **(tira 2, pos 63)** |
| Cable `ALIM GND` | (tira 1, pos 15) | **(tira 1, pos 63)** |
| `C_BULK` 470 µF (10348) | tira 1↔2, pos 19 | **tira 1↔2, pos 61** ⚠️ polaridad: **+ a la tira 2** |
| `C8` 100 nF (10352) | tira 1↔2, pos 35 | **tira 1↔2, pos 60** |

**Los módulos NO se mueven.** El S3 se queda con las filas en las posiciones 1 y 11 y el
Daisy en la 39 y la 45.

---

## 5. AÑADIR

### a) El corte del raíl +5 V

**Tira 2, entre las posiciones 58 y 59.** Es el único corte nuevo del fichero, y el
único de un raíl en toda la placa. **La tira 1 (GND) no se corta aquí.**

### b) Interruptor de red

- **Pieza:** un SPDT igual que el del selector de filtro (duplicar el `Taiway`, idx
  10386). Se usan **solo el común y un extremo**; el otro queda al aire.
- **Rótulo:** `SW1 — interruptor de red (PANEL)`
- **Colocación:** **fuera de la placa**, junto al resto de los mandos de panel.
- **Dos cables:**
  - común → **(tira 2, posición 59)** — lado sin conmutar, el del bulk
  - un extremo → **(tira 2, posición 58)** — lado conmutado, el que alimenta todo

### c) Mover el `AGND local` de la tira 25 a la tira 31

Deja el mazo de potes en **nueve tiras seguidas (31 a 39)**, o sea un único conector
contiguo, y acerca los seis 100 nF de 8–13 tiras a 2–7.

1. **Nuevo corte: tira 31, entre las posiciones 47 y 48.**
2. **Quitar el corte de la tira 25** (entre 47 y 48): deja de hacer falta.
3. Mover el extremo del cable `AGND -> zona de potes` de `(tira 25, pos 48)` a
   **`(tira 31, pos 48)`**. El otro extremo se queda en `(tira 39, pos 35)`.
4. Mover los seis cables `POT x AGND` y el `SELECTOR AGND` de la tira 25 a la **tira 31**
   (posiciones 49, 51, 53, 55, 57, 59 y 61, sin cambio).

⚠️ La tira 31 es `OLED SCL` (pin 12) en el **lado A**. El corte va en el lado B, así que
no la afecta — pero es exactamente el tipo de cosa que hay que volver a mirar si algún
día se mueve el OLED.

### d) Los seis 100 nF de los cursores

No están en el fichero. Seis cerámicos, cada uno de su tira de cursor a la **tira 31**
(`AGND local`), **escalonados entre las posiciones 50 y 60** para que no se estorben al
soldar:

| Pote | Tira del cursor | Salto hasta la 31 |
|---|---|---|
| Attack | 38 | 7 tiras — formar patas |
| Decay | 37 | 6 tiras — formar patas |
| Sustain | 36 | 5 tiras |
| Release | 35 | 4 tiras |
| Cutoff | 34 | 3 tiras |
| Q | 33 | 2 tiras |

### e) Las dos 10 kΩ del divisor del selector

Van **en la placa**, no en el panel:

- una de la **tira 39** (`3V3A`) a la **tira 32** (`SEL`)
- otra de la **tira 32** a la **tira 31** (`AGND local`)

### f) `D1` se queda

Decidido el 21 de agosto: **se mantiene el diodo-OR**. Ya está dibujado (tira 2 → tira
3, posición 41) y no hay que tocarlo. Añadir al rótulo: `D1 — 1N5817 (puentear si el
raíl < 4,8 V)`.

---

## 6. OPCIONAL: header de 3 pines para el MIDI

Tal como está, el shield sube tres hilos sueltos: `RX` a la tira 34 (pos 21) y `5V`/`GND`
directos a los raíles (tiras 2 y 1, pos 53). Funciona y no necesita nada.

Si se quiere un conector contiguo en las tiras 34‑35‑36:

- 🔴 **obligatorio cortar las tiras 35 y 36 entre las posiciones 30 y 31.** Sin eso, el
  conector mete **+5 V en `AUDIO IN L`** (pin 16, tira 35) y masa en `AUDIO IN R`.
- header en la posición ~29, y dos puentes: tira 2 → (35, ~29) y tira 1 → (36, ~29).

---

## 7. Comprobación final antes de dar el fichero por bueno

1. Que la **tira 1 (GND) solo tiene el corte de la línea del S3** (entre 6 y 7), y
   ninguno más en toda su longitud.
2. Que la **tira 2 tiene exactamente dos cortes**: el de la línea del S3 (6‑7) y el
   nuevo del interruptor (58‑59).
3. Que **no hay ningún componente ni puente bajo el cuerpo del Daisy (pos 39–45) ni del
   S3 (pos 1–11)** — solo las líneas de corte.
4. Que el 470 µF y los dos 100 µF del filtro **no están pegados entre sí**.
5. Que siguen ahí los 20 cortes del Daisy, los 22 del S3 y los 6 de separación.
6. Que el recuento total de cortes es **53**: 52 del fichero − 1 (tira 25) + 1 (tira 31)
   + 1 (tira 2, el del interruptor).
