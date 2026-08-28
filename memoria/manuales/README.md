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
| `XPT2046_Touchscreen - XPT2046_Touchscreen.cpp (rama principal).cpp` | (ver nota abajo) | El mismo fichero, pero de la rama que realmente compila el firmware |
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
- Las librerías se guardan como el archivo comprimido de la **etiqueta de
  versión** citada, no de la rama principal.
- **Matiz de la librería del táctil, comprobado al descargarla.**
  `firmware/cyd_ui/platformio.ini` la pide por la URL del repositorio sin fijar
  etiqueta, así que lo que compila de verdad es la **rama principal**, no la
  etiqueta `v1.4`. Las dos declaran versión 1.4 en su `library.properties`, y
  entre las dos hay **una sola línea de diferencia**: `Z_THRESHOLD` pasa de 400
  en la etiqueta a 300 en la rama, es decir el umbral de presión por debajo del
  cual la librería no da el toque por bueno. No afecta a nada de lo escrito en
  el capítulo 5, que no depende de ese valor, pero por eso se guarda también el
  `.cpp` de la rama principal, para que quede constancia de qué código se está
  ejecutando en realidad. Si alguna vez conviene clavar la versión, se hace
  añadiendo `#v1.4` al final de la URL del `lib_deps`.
