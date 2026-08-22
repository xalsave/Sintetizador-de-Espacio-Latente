# Cotas del panel — bloque C

> Rellenar la columna **MEDIDO** antes de modelar. Lo que está en "típico" son valores
> de catálogo que **varían según el proveedor**: si se modela sobre ellos sin comprobar,
> el panel sale con los agujeros del tamaño equivocado y hay que reimprimirlo.

## 1. Medidas a tomar con el pie de rey

| # | Qué | Típico | MEDIDO |
|---|---|---|---|
| 1 | Rosca del potenciómetro (Ø) | 7,0 mm (M7×0,75) | |
| 2 | Longitud del eje del pote desde el panel | 15–20 mm | |
| 3 | ¿Patilla antigiro? Distancia al centro | sí, ~6,9 mm | |
| 4 | Rosca del interruptor `ON-OFF-ON` (Ø) | 6,0 mm (M6×0,75) | |
| 5 | Rosca del jack de audio (Ø) | 6,0 mm | |
| 6 | Rosca de la entrada de alimentación (Ø) | 8,0 mm | |
| 7 | OLED: PCB completo | 27 × 27 mm | |
| 8 | OLED: separación entre taladros de montaje | ~23 × 23 mm | |
| 9 | OLED: rectángulo de cristal visible | ~26 × 15 mm | |
| 10 | CYD: área táctil visible | ~50 × 69 mm | |
| 11 | CYD: posición de sus 4 taladros | — | |
| 12 | Shield MIDI: del borde del PCB al centro del DIN | — | |
| 13 | Shield MIDI: cuánto sobresale el DIN del PCB | — | |
| 14 | **Cama de la impresora** | — | |

## 2. Cotas ya conocidas (no hace falta medir)

| Pieza | Cota |
|---|---|
| Veroboard | 100 × 160 mm, 1,5 mm de grosor |
| Altura del conjunto de la placa | **~28 mm** (zócalos 8,5 + Daisy ~5 + bulk 20 por encima, y ~3 de hilos por la cara de cobre) |
| CYD, PCB | 86 × 50 mm, ~13 mm de fondo |
| Shield MIDI | formato Arduino, 68,6 × 53,4 mm |
| Potenciómetro, cuerpo | 9,5 × 11 × 8 mm por detrás del panel |

## 3. Disposición propuesta

Carcasa **en cuña estilo Moog** (decidido el 15 ago, `veroboard.md` §6bis).

**Cara inclinada (frontal)** — lo que se toca y se mira:
- **CYD** arriba a la izquierda: es el elemento principal, el mapa latente
- **OLED** arriba a la derecha, junto al selector
- **Seis potes en fila** abajo: Attack · Decay · Sustain · Release · Cutoff · Q
- **Selector LPF/HPF/BPF** a la derecha de los potes
- **Interruptor de red** arriba a la derecha del todo

**Cara trasera (vertical)** — lo que se enchufa y no se toca:
- Entrada de alimentación 2,1 mm
- DIN‑5 del MIDI (el shield sujeto por dentro con separadores de nylon)
- Jack de audio 3,5 mm, **de plástico y aislado del panel**

Motivo del reparto: los mandos y la pantalla al frente, los cables por detrás para que no
crucen por delante en las fotos ni en la defensa. El interruptor de red al frente porque
es de uso, no de instalación.

## 4. Estrategia de impresión

⚠️ Una carcasa completa para una placa de 100×160 sale de unos **210 × 180 mm de planta**
y son **8–15 h de impresión**. No cabe en una sesión.

**Orden que desbloquea el hardware antes:**

1. **Imprimir primero el PANEL solo** — plancha de 3–4 mm con todos los agujeros. 2–3 h.
   Es lo único que hace falta para fijar la longitud de los 39 hilos del mazo.
2. Montar los mandos en el panel, **medir y cortar el mazo**, terminar de soldar la placa.
3. El cuerpo de la caja, después. El instrumento funciona, se mide y se fotografía con el
   panel sobre una base provisional.

**Plan B si el panel tampoco sale a tiempo:** maqueta del panel **en cartón** con los
agujeros reales, mandos pinchados en ella. Da las mismas longitudes en veinte minutos y
no bloquea nada.

## 5. Herramienta

**OpenSCAD** ([openscad.org](https://openscad.org), gratis, ~30 MB). CAD por texto: el
modelo se escribe como código y es paramétrico, así que corregir una cota es cambiar un
número. `F5` previsualiza, `F6` renderiza, *Export as STL*.

Descartado **Blender**: es una herramienta de modelado orgánico, no mecánico; poner un
agujero a una cota exacta es incómodo y no hay parámetros.
