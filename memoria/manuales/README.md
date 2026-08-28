# manuales/ — documentación técnica citada en la memoria

Igual que `memoria/papers/` guarda los artículos, esta carpeta guarda las hojas
de características y las librerías de terceros que cita la memoria, para poder
comprobar de dónde sale cada dato sin volver a buscarlo.

Descargado el 28 ago 2026: primero las seis fuentes del capítulo 5 y
después las seis del capítulo 6 (Daisy Seed, STM32H750, SSD1306, la
especificación MIDI y las dos bibliotecas de la plataforma Daisy).

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
| `Daisy Seed Datasheet v1.2.0 (Electrosmith).pdf` | `DaisySeed` | Cortex-M7 a 480 MHz y audio de 96 kHz/24 bit; tabla de pines (D7-D10 = SPI1, D13/D14 = USART1, D11/D12 = I2C1); GPIO tolerantes a 5 V salvo los pines 24, 25, 28, 29 y 30, de donde sale que el 6N138 se conecte a D14 sin adaptar niveles; impedancia de salida de audio 100 ohmios; códec PCM3060 en formato left-justified de 24 bits (capítulo 6) |
| `STM32H750 Datasheet DS12556 Rev 7 (STMicroelectronics).pdf` | `STM32H750` | **Un solo dato, y por eso está**: el Cortex-M7 lleva FPU de doble precisión e instrucciones DSP hasta 480 MHz. La hoja del Daisy da el núcleo y la frecuencia pero **no menciona la FPU**, y es lo que justifica que toda la cadena de audio trabaje en coma flotante (§6.1). Aporta también los 3 ADC de hasta 16 bits |
| `SSD1306 Datasheet Rev 1.1 (Solomon Systech).pdf` | `SSD1306` | Pantalla de 128x64; dirección de esclavo I2C `0111100` o `0111101` según SA0 (0x3C y 0x3D); byte de control con los bits Co y D/C#; comando `AEh` = display off, que es el que manda el sondeo de presencia del arranque (§6.6) |
| `MIDI 1.0 Detailed Specification v4.2.1 (MMA).pdf` | `MIDI1` | 31,25 kbaud ±1 %, asíncrono, 10 bits por byte y LSB primero; lazo de corriente de 5 mA con optoacoplador obligatorio, y **la propia norma nombra el 6N138** como aceptable; do central = nota 60; Note On con velocity 0 equivale a Note Off, y por qué (running status) (§6.4) |
| `libDaisy v5.4.0+22 (commit 85172e2b, Electrosmith).zip` | `libDaisy` | Recepción SPI por DMA con NSS por hardware; `MidiUartHandler` fija 31 250 baudios y recibe por DMA en su propio búfer; ADC1 a 16 bits con sobremuestreo x32 y `GetFloat()` dividiendo por 65536; las tres velocidades de I2C y la nota de los 886 kHz reales; 48 kHz por defecto (capítulo 6) |
| `DaisySP V1.0.0 (Electrosmith).zip` | `DaisySP` | `Adsr`; `Svf` doble-muestreado acreditado a Andrew Simper, con las cuatro salidas calculadas a la vez, límite `f < sr/3` y `damp = 2(1-Q^0,25)`, de donde sale la compensación de ganancia de resonancia (§6.5) |

## Notas

- **La CYD no tiene manual de fabricante.** Es una placa genérica y su
  documentación es comunitaria, así que ese repositorio se cita como recurso
  web y nunca como hoja de características. No confundirlo con las tres
  primeras entradas, que sí son documentos oficiales del fabricante del chip.
- **Falta por descargar**, si el capítulo 7 acaba citándola: la hoja del
  **6N138**. No se descargó para el capítulo 6 a propósito, porque la
  especificación MIDI ya sostiene el aislamiento óptico y hasta nombra ese
  componente; el dato de los 4,5 V mínimos de alimentación del optoacoplador
  es eléctrico y pertenece al capítulo de hardware. Tampoco se descargó la
  del **PCM3060**: el códec lo configura el hardware de la placa y no se
  toca desde el código.
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

## Procedencia de las fuentes del capítulo 6 (anotado el 28 ago 2026)

Dos de los cuatro PDF **no vienen del sitio del fabricante**, y conviene que
conste por si alguna vez hay que rehacer la descarga:

- **STM32H750.** `st.com` no responde desde este equipo (conexión rechazada,
  probado con y sin cabecera de navegador). El PDF es el que sirve
  `cdn.sparkfun.com`, que es el documento oficial de ST íntegro, **DS12556
  Rev 7, marzo de 2023**. Existe una Rev 8 de enero de 2026 que no se ha podido
  bajar; el dato que sostiene esta entrada, la FPU de doble precisión, no cambia
  entre revisiones. La entrada de `referencias.bib` cita a ST como editor, que
  es lo correcto.
- **Especificación MIDI.** `midi.org` exige registro para descargarla. El PDF
  procede de la copia que sirve CCRMA (Stanford) con fines docentes, y es el
  documento de la MMA, **versión 4.2.1, febrero de 1996**. La entrada cita a la
  MMA.

Los otros dos sí son de origen oficial: la hoja del Daisy Seed viene del CDN de
Electrosmith enlazado desde `docs.daisy.audio`, y los dos comprimidos de las
bibliotecas, de las etiquetas y revisiones correspondientes de GitHub.

**La versión de `libDaisy` no es una etiqueta limpia**, y se cita así a
propósito. El árbol que compila el firmware está 22 commits por delante de
`v5.4.0`, en la revisión `85172e2b` del 8 de enero de 2024, comprobado con
`git describe --tags` sobre el propio directorio de trabajo. Se guarda el
comprimido de esa revisión exacta, no el de la etiqueta, siguiendo el mismo
criterio que con la librería del táctil: se cita lo que está compilado y
flasheado. `DaisySP` sí está exactamente en la etiqueta `V1.0.0`.
