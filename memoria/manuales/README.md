# manuales/ — documentación técnica citada en la memoria

Igual que `memoria/papers/` guarda los artículos, esta carpeta guarda las hojas
de características y las librerías de terceros que cita la memoria, para poder
comprobar de dónde sale cada dato sin volver a buscarlo.

Descargado el 28 ago 2026, al cerrar el capítulo 5.

| Archivo | Clave en `referencias.bib` | Qué dato de la memoria sostiene |
|---|---|---|
| `ESP32-S3 Series Datasheet v2.2 (Espressif).pdf` | `EspressifS3` | SPI0 y SPI1 quedan dedicados al flash y la PSRAM del encapsulado; SPI2 y SPI3 son de propósito general (§5.4) |
| `ESP32 Series Datasheet v5.3 (Espressif).pdf` | `EspressifESP32` | Tabla IO MUX: GPIO12 a 15 son HSPIQ / HSPID / HSPICLK / HSPICS0, es decir los pines nativos del HSPI (§5.1) |
| `XPT2046 Touch Screen Controller Data Sheet (XPTEK).pdf` | `XPT2046` | Convertidor SAR de 12 bits a 125 kHz, de donde sale el rango crudo 0..4095 de la calibración (§5.1) |
| `TFT_eSPI v2.5.43 (Bodmer).zip` | `TFTeSPI` | Librería de la pantalla. La versión es la que clava `firmware/cyd_ui/platformio.ini` |
| `XPT2046_Touchscreen v1.4 (Stoffregen).zip` | `XPT2046Touchscreen` | Librería del táctil. En `XPT2046_Touchscreen.cpp`, `update()` aplica la rotación: la rama del giro de 180° está escrita como `default: // 3` y hace `xraw = 4095 - x; yraw = 4095 - y`, espejo exacto del `case 1`. Es el hallazgo del §5.1.1, verificado sobre el código y no de memoria |
| `XPT2046_Touchscreen.cpp (copia de lo instalado y flasheado).cpp` | (ver nota abajo) | Copia del fichero tal y como está en `firmware/cyd_ui/.pio/libdeps/`, es decir el código que corre en la placa |
| `ESP32-Cheap-Yellow-Display (witnessmenow).zip` | `CYDrepo` | Documentación comunitaria de la ESP32-2432S028R |
| `ESP32-Cheap-Yellow-Display - PINS.md` | (parte del anterior) | Extraído del zip para poder leerlo sin descomprimir. Confirma los tres GPIO libres de la placa: IO35 solo entrada, IO22 e IO27, y que IO21 es la retroiluminación |

## Notas

- **La CYD no tiene manual de fabricante.** Es una placa genérica y su
  documentación es comunitaria, así que ese repositorio se cita como recurso
  web y nunca como hoja de características. No confundirlo con las tres
  primeras entradas, que sí son documentos oficiales del fabricante del chip.
- **Faltan por descargar**, para cuando se escriban los capítulos 6 y 7: Daisy
  Seed, SSD1306, 6N138 y la especificación MIDI.
- Los dos PDF de Espressif se bajaron de `documentation.espressif.com`, que es
  el sitio oficial. El del XPT2046 no lo publica el fabricante en abierto y se
  tomó de un distribuidor (Grobotronics); la portada dice «XPT2046 Data Sheet,
  2007.5, Copyright 2007 Shenzhen XPTEK Technology Co., Ltd.», que es lo que
  figura en la entrada bibliográfica.
- **La librería del táctil se cita como 1.4 y así se queda** (decisión del
  autor, 28 ago 2026), porque es la versión que hay instalada y flasheada.
  Comprobado en su `library.properties` dentro de
  `firmware/cyd_ui/.pio/libdeps/`, que declara `version=1.4`.
- **Detalle anotado para que nadie lo redescubra.** El `.cpp` instalado no es
  idéntico al de la etiqueta `v1.4` de GitHub: se diferencian en **una sola
  línea**, `Z_THRESHOLD`, que vale 400 en la etiqueta y 300 en lo instalado. Es
  el umbral de presión por debajo del cual la librería no da un toque por
  bueno. Ocurre porque el autor de la librería tocó esa línea después de
  publicar la 1.4 sin subir el número de versión. **No afecta a nada de lo
  escrito en el capítulo 5**, que no depende de ese valor. Por eso se guardan
  las dos cosas: el comprimido de la etiqueta, que es lo que se cita, y una
  copia del fichero tal y como está instalado, que es lo que corre en la placa.
- **No se toca el `platformio.ini` para clavar la versión.** El firmware está
  congelado y validado; el sitio de esta anotación es este índice, no el código.
