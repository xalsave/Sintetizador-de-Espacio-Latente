# Cambios pendientes en el Fritzing

> **Fichero base:** `sistema-midi-cyd-daisy-VEROBOARD-FINAL.fzz` (16 ago, 02:31)
> **Fichero destino:** `sistema-midi-cyd-daisy-VEROBOARD-FINAL-v2.fzz`
> **Guardar como versión nueva, no sobrescribir.** El FINAL es la última versión que
> corresponde al montaje de protoboard que funcionó el 15 de agosto.
>
> La especificación que manda es `docs/veroboard.md` §6ter y §6quinquies. Esto es
> solo la lista de diferencias, para no tener que releer el documento entero.

Coordenadas en **(tira, posición)**: tira 1…39 perpendicular al cobre, posición 1…63 a
lo largo. Tira 1 = raíl +5 V, tira 39 = raíl GND.

---

## 1. Inventario actual del `.fzz` (leído del XML)

| Rótulo | Pieza | `modelIndex` | Valor |
|---|---|---|---|
| A1 | Shield MIDI | 100 | |
| U1 | Daisy Seed 40 pin | 110 | |
| U3 | CYD ESP32-2432S028R | 130 | |
| A2 | ESP32-S3 DevKit | 7636 | |
| Power plug1 | Conector de alimentación | 7436 | |
| Stripboard1 | Veroboard 63×39 | 9926 | |
| C1, C2 | Electrolítico | 9001, 9002 | 100 µF / 50 V |
| R1, R2, R3 | Resistencia | 9003, 9004, 9005 | **10 Ω** |
| C4, C5, C6, C7 | Electrolítico | 9007–9010 | 100 µF / 50 V |
| C4, C5, C6, C7 | Electrolítico | **10348–10351** | 100 µF / 50 V |
| C8 | Cerámico | 9011 | 100 nF / 50 V |
| C8 | Cerámico | **10352** | 100 nF / 35 V |
| C9 | Cerámico | 10072 | 100 nF / 35 V |
| D1 | Diodo Schottky 1N5817 | 9012 | |
| POT A/D/S/R/CUT/Q | Potenciómetro 9 mm | 10362–10382 | |
| SELECTOR filtro | Conmutador SPDT Taiway | 10386 | |
| OLED 0.96 I2C | OLED | 10390 | |
| JACK 3.5mm audio | Jack | 10395 | |

⚠️ **Hay rótulos duplicados**: dos juegos de `C4`–`C7` y dos `C8`. Son ocho
electrolíticos de 100 µF donde el diseño solo pedía cuatro de bulk más dos de filtro.
Casi seguro es un pegado accidental. **Primera tarea: abrir el fichero y comprobar si
las cuatro de `modelIndex` 10348–10351 están encima de las 9007–9010.** Si lo están, se
borran las cuatro y ya.

---

## 2. BORRAR

| Qué | Por qué |
|---|---|
| **R2 y R3** (idx 9004, 9005) | El filtro pasa de 3×10 Ω en paralelo a **una sola 3R3 de 1 W** |
| **C5, C6, C7** del juego de bulk (idx 9008, 9009, 9010) | El bulk pasa de 4×100 µF a **un solo 470 µF** |
| **El juego duplicado C4–C7** (idx 10348–10351) y el **C8 duplicado** (idx 10352) | Duplicados, si se confirma el §1 |

Al borrar en Fritzing se van también sus cables. **Antes de borrar, anota a qué estaba
conectado cada uno**, porque el 470 µF y la 3R3 tienen que heredar esas conexiones.

---

## 3. CAMBIAR valor

| Pieza | Antes | Ahora |
|---|---|---|
| **R1** (idx 9003) | 10 Ω | **3,3 Ω**, y rotularla `R1 — 3R3 1 W FUSIBLE` |
| **C4** del bulk (idx 9007) | 100 µF | **470 µF**, y rotularla `C_BULK — 470 µF` |
| C1, C2 (idx 9001, 9002) | 100 µF | *sin cambio* — son los dos del filtro del Daisy |

⚠️ El 470 µF real es un **Nichicon FW de ráster 5 mm** y va entre dos filas contiguas
(2,54 mm): hay que apretarle las patas hacia dentro. En el Fritzing da igual, pero
conviene que el rótulo lo recuerde.

---

## 4. AÑADIR

### a) Interruptor de red — la pieza nueva importante

- **Pieza:** un SPDT igual que el del selector de filtro (duplica el `Taiway`, idx
  10386). Se usan **solo el común y un extremo**; el otro extremo queda al aire.
- **Rótulo:** `SW1 — interruptor de red (PANEL)`
- **Colocación:** **fuera de la placa**, junto al resto de los mandos de panel.
- **Dos cables:**
  - común → **(tira 1, posición 4)** — lado sin conmutar, el del bulk
  - un extremo → **(tira 1, posición 6)** — lado conmutado, el que alimenta todo

### b) Los tres cortes de aislamiento nuevos

Fritzing dibuja los cortes de stripboard haciendo clic en el tramo de pista entre dos
agujeros. Los que faltan:

| Corte | Dónde | Para qué |
|---|---|---|
| **Raíl +5 V** | **tira 1, entre posiciones 5 y 6** | Poner el interruptor aguas abajo del bulk |
| **MIDI** | **tiras 34 y 35, entre posiciones 31 y 32** | 🔴 Aísla el +5 V y el GND del conector MIDI de `AUDIO IN L/R` (pines 16 y 17) |
| **`AGND local`** | **tira 30, entre posiciones 42 y 43** | Raíl de masa analógica para los seis 100 nF de los cursores |
| **`3V3D local`** | **tira 24, entre posiciones 32 y 33** | Lleva el 3V3 digital del lado B al conector del OLED, que está en el lado A |

### c) Puentes que alimentan esos tramos aislados

| Desde | Hasta |
|---|---|
| tira 1 (raíl +5 V, lado conmutado) | tira 34, posición ~29 → **+5 V del conector MIDI** |
| tira 39 (raíl GND) | tira 35, posición ~29 → **GND del conector MIDI** |
| tira 38 **lado A** (pin 20, `AGND`) | tira 30, posición ~44 → **`AGND local`** |
| tira 21 **lado B** (pin 38, `3V3D`) | tira 24, posición ~30 → **`3V3D local`** |

### d) Los seis 100 nF de los cursores

No están en el fichero. Seis cerámicos de 100 nF, cada uno de su tira de cursor a la
tira 30 (`AGND local`), **escalonados entre las posiciones 50 y 60** para que no se
estorben al soldar:

| Pote | Tira del cursor | A tira 30 |
|---|---|---|
| Attack | 37 | 7 tiras — formar patas |
| Decay | 36 | 6 tiras — formar patas |
| Sustain | 35 | 5 tiras |
| Release | 34 | 4 tiras |
| Cutoff | 33 | 3 tiras |
| Q | 32 | 2 tiras |

### e) Las dos 10 kΩ del divisor del selector

Tampoco están. Van **en la placa**, no en el panel:

- una de **tira 38** (`3V3A`) a **tira 31** (`SEL`)
- otra de **tira 31** (`SEL`) a **tira 30** (`AGND local`)

---

## 5. RECOLOCAR

El ESP32-S3 **se desplaza dos posiciones** para dejar sitio al bulk, al corte del raíl y
a los dos hilos del interruptor:

| Elemento | Antes | Ahora |
|---|---|---|
| S3 — fila sin uso (pines 23–44) | posición 6 | **posición 8** |
| S3 — línea de corte | posición 11 | **posición 13** |
| S3 — fila usada (pines 1–22) | posición 16 | **posición 18** |
| Conectores JST de la CYD | 19–24 | **20–24** |

El Daisy **no se mueve** (filas en 34 y 40, corte en 37).

---

## 6. DECIDIR antes de dibujar

**El diodo `D1` (1N5817) del diodo-OR de la CYD.** Con el rail medido a 4,40 V y la CYD
a 4,07 V, añadirle un Schottky en serie le quita otros ~0,35 V y la deja en **~3,7 V**,
por debajo de lo que su AMS1117 necesita para regular con holgura.

➡️ **El diodo-OR ya no sale gratis.** O se quita del diseño (y entonces hay que
desconectar el raíl para flashear la CYD por USB), o se mantiene y se acepta el margen.
**No dibujarlo hasta decidirlo.**

---

## 7. Comprobación final antes de dar el fichero por bueno

1. Que la **tira 39 (GND) no tiene ningún corte** en toda su longitud.
2. Que la **tira 1 tiene exactamente un corte**, el de la posición 5.
3. Que **no hay ningún componente ni puente bajo el cuerpo del Daisy ni del S3** — solo
   las líneas de corte.
4. Que el 470 µF y los dos 100 µF del filtro **no están pegados entre sí**.
5. Que los 20 cortes del Daisy, los 22 del S3 y los 5 de separación siguen ahí.
