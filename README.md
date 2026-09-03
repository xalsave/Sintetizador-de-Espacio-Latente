# Sintetizador de Espacio Latente

> Sintetizador digital embebido que genera timbres mediante interpolación
> neuronal de wavetables. Trabajo de Final de Grado, Grado en Ingeniería de
> Sistemas de Telecomunicación (GITST), Universitat Politècnica de València.

---

## Resumen

Este proyecto desarrolla un instrumento musical electrónico autónomo que
utiliza un **autoencoder variacional (VAE)** para organizar un corpus de
formas de onda de un ciclo en un **espacio latente bidimensional continuo**.
El intérprete navega por ese espacio tocando un punto en una pantalla táctil;
el sistema sintetiza en tiempo real una wavetable interpolada entre las
formas de onda aprendidas y la reproduce con control MIDI desde un teclado.

A diferencia de los sintetizadores wavetable tradicionales, donde el intérprete
selecciona una de N tablas predefinidas, este sistema permite explorar de
forma continua un mapa de timbres donde **cada punto produce una onda nueva**,
sintetizada por el decoder del modelo aprendido.

---

## Demostración del concepto

```
   Usuario toca (x, y)              Espacio latente 2D
   en pantalla táctil      ───►     aprendido por VAE
                                            │
                                            ▼
                                    Wavetable de 1024
                                    muestras (1 ciclo)
                                            │
                                            ▼
                                    Síntesis wavetable
                                    + filtro + ADSR + MIDI
                                            │
                                            ▼
                                       Audio out
```

El intérprete recorre el plano con el dedo y oye el timbre transformarse de
forma continua entre todas las familias del dataset (cuerdas, vientos,
sintéticos, ruidos, etc.) sin saltos perceptibles.

---

## Arquitectura del sistema

Tres microcontroladores con roles especializados, comunicados por buses
serie estándar:

| Subsistema       | Hardware                    | Función                                       |
|------------------|-----------------------------|-----------------------------------------------|
| Interfaz táctil  | CYD (ESP32-2432S028R)       | Pantalla TFT 2.8" + táctil resistivo XPT2046  |
| Cerebro          | ESP32-S3 N16R8              | Grid 16×16 en flash, interpolación bilineal   |
| Motor de audio   | Daisy Seed (STM32H750)      | Síntesis, filtro, envolvente, MIDI, audio out |
| Control MIDI     | Arturia Keystep MK2         | Teclado controlador por DIN                   |
| Panel analógico  | 6 potenciómetros + selector | ADSR, corte, resonancia y tipo de filtro      |
| Display          | OLED SSD1306 128×64         | Parámetro en edición y curva correspondiente  |

**Flujo de datos:**

```
[CYD]──UART(460800)──►[ESP32-S3]──SPI(10 MHz)──►[Daisy Seed]──audio──► jack 3.5
   ▲                                                  ▲
   └────── onda diezmada, para dibujarla ─────┘       │ MIDI DIN (6N138 → USART1)
                                                 [Keystep MK2]
```

El enlace con la CYD es full-duplex: la coordenada táctil sube al ESP32-S3 en
una trama de 6 bytes, y el ESP32-S3 devuelve la onda resultante diezmada a 256
puntos de 8 bits para que la pantalla la dibuje. Esa onda de vuelta es dato de
representación, no de audio: la wavetable real de 1024 muestras solo viaja por
el SPI hacia el Daisy, en tramas de 2054 bytes protegidas con CRC16-CCITT.

---

## Cómo funciona

### Fase offline (preparación, en PC)

1. **Preprocesado del dataset.** Se cargan las ~4000 wavetables del corpus AKWF
   (Adventure Kid Waveforms), se remuestrean de 600 a 1024 muestras por FFT, se
   elimina la componente continua, se alinea el armónico fundamental a fase 0 y
   se normaliza por pico.
2. **Entrenamiento del VAE.** Autoencoder variacional totalmente conectado en
   PyTorch, con encoder 1024 → 512 → 128 → latente 2D y decoder espejo. La
   pérdida combina error cuadrático de reconstrucción y divergencia KL con un
   peso pequeño y rampa de calentamiento.
3. **Horneado del grid.** Se acota la zona poblada del latente por percentiles,
   se muestrea una rejilla regular de 16×16 = 256 puntos, se decodifica una
   wavetable en cada nodo y se exporta el banco como header de C en formato Q15,
   unos 512 KB en la flash del ESP32-S3.

La red **no se ejecuta en el instrumento**. Toda la inferencia ocurre en esta
fase, de modo que en vivo no hay latencia de modelo.

### Fase en vivo (en el instrumento)

1. La CYD lee el punto tocado, lo normaliza al rango completo de 16 bits y envía
   la coordenada por UART al ESP32-S3.
2. El ESP32-S3 localiza la celda del grid e **interpola bilinealmente** entre
   las cuatro wavetables vecinas, produciendo una onda suave para cualquier
   coordenada continua.
3. La wavetable resultante viaja por SPI al Daisy Seed.
4. El Daisy mantiene un **doble buffer** y aplica un **crossfade de 20 ms** al
   recibir una tabla nueva, lo que elimina los clicks de cambio.
5. Un acumulador de fase con interpolación lineal entre muestras reproduce la
   tabla a la frecuencia que indica el MIDI entrante del Keystep. La señal pasa
   por un filtro variable de estado y una envolvente ADSR, y sale por el códec
   del Daisy a un jack de 3.5 mm.

### Panel de control

El Daisy lee siete canales analógicos: los cuatro tiempos y niveles del ADSR,
la frecuencia de corte, la resonancia y un selector de tres posiciones que
escoge entre filtro paso bajo, paso banda y paso alto. El OLED muestra el
último mando movido con su valor en unidades reales y la curva correspondiente,
la envolvente o la respuesta del filtro.

---

## Estructura del repositorio

```
Sintetizador-de-Espacio-Latente/
├── ml/
│   ├── dataset/              # Corpus AKWF (.wav) y dataset procesado (.npy)
│   ├── scripts/              # Pipeline numerado por orden de ejecución
│   └── exports/              # vae.pt, grid.npy, grid.h y figuras del modelo
├── firmware/
│   ├── cyd_ui/               # PlatformIO — pantalla táctil (ESP32-WROOM)
│   ├── esp32_control/        # PlatformIO — grid e interpolación (ESP32-S3)
│   └── daisy_dsp/            # libDaisy — síntesis, MIDI y panel (STM32H750)
├── hardware/
│   ├── cad/                  # Carcasa y panel en OpenSCAD
│   └── schematics/           # Cableado y veroboard en Fritzing
├── memoria/
│   ├── plantilla latex/      # Fuentes LaTeX del documento y capítulos
│   ├── figuras/              # Guiones de Python que generan las figuras
│   └── resumen_sesiones/     # Cuaderno de laboratorio, sesión a sesión
├── docs/               # Notas técnicas por subsistema
├── LICENSE
└── README.md
```

El firmware del Daisy se compila desde el árbol de DaisyExamples; la copia de
`firmware/daisy_dsp/` es la fuente de referencia versionada.

---

## Reproducir el pipeline

Los scripts de `ml/scripts/` están numerados por orden de ejecución y se lanzan
desde la raíz del repositorio:

```bash
python ml/scripts/2_build_dataset.py    # AKWF -> akwf_processed.npy
```

```bash
python ml/scripts/3_train_vae.py        # entrena el VAE -> vae.pt
```

```bash
python ml/scripts/4_bake_grid.py        # decodifica el grid -> grid.npy y grid.h
```

```bash
python ml/scripts/5_demo_morph.py       # demo del morphing con ratón, en PC
```

Requiere Python 3.10 o superior con PyTorch, NumPy, SciPy, Matplotlib y
`sounddevice` para la demo. El entrenamiento aprovecha CUDA si está disponible.

### Validación cruzada

Cada enlace de la cadena se comprueba contra una referencia calculada en NumPy,
en lugar de fiarlo al oído:

- `6_validate_s3.py` recalcula en el PC la wavetable que el ESP32-S3 volcó por
  serie y las compara muestra a muestra.
- `7_validate_spi.py` comprueba que lo que reproduce el Daisy es exactamente lo
  que el ESP32-S3 envió por SPI.
- `8_validate_midi.py` contrasta la tabla de conversión de nota MIDI a
  frecuencia y a incremento de fase del firmware con la fórmula teórica.
- `8b_monitor_midi.py` muestra en vivo los eventos que procesa el Daisy.

---

## Stack tecnológico

- **Machine learning:** Python 3.10+, PyTorch, NumPy, SciPy, Matplotlib
- **Firmware Daisy:** C++ con libDaisy y DaisySP, ARM GCC, flasheo por DFU
- **Firmware ESP32-S3 y CYD:** C++ sobre Arduino con PlatformIO
- **Comunicación:** UART 8N1 a 460800 baud entre CYD y ESP32-S3; SPI a 10 MHz
  en modo 0 entre ESP32-S3 y Daisy; MIDI DIN por USART1 con optoacoplador 6N138
- **Audio:** códec del Daisy a 48 kHz, señal mono replicada en ambos canales
- **Hardware:** veroboard, carcasa impresa en 3D modelada en OpenSCAD

---

## Estado del proyecto

**Completado.** El instrumento está montado, flasheado y verificado como
unidad, con los tres microcontroladores, el panel analógico, el display y la
carcasa definitiva. El documento del TFG se encuentra en `memoria/`.

El decoder neuronal embarcado en el ESP32-S3 mediante TensorFlow Lite Micro se
estudió como ampliación y queda documentado como línea de trabajo futuro: la
versión final resuelve el timbre por interpolación bilineal sobre el grid
precalculado, que era el camino crítico del proyecto.

---

## Referencias

El proyecto se apoya en literatura previa de síntesis neuronal de audio:

- **Hantrakul & Yang (2018).** *Neural Wavetable: a playable wavetable
  synthesizer using neural networks.*
- **Engel et al. (Magenta, 2020).** *DDSP: Differentiable Digital Signal
  Processing.*
- **Caillon & Esling (IRCAM, 2021).** *RAVE: A variational autoencoder
  for fast and high-quality neural audio synthesis.*
- **Wavespace (2024).** *VAE-based wavetable generation with factorized
  latent space.*

La aportación diferencial de este TFG no reside en la técnica de interpolación
neuronal, ya explorada en plugins de DAW, sino en su **integración embebida
completa en tiempo real**, sobre hardware de bajo coste y con interfaz física
táctil y MIDI, llevando la idea de plugin de software a instrumento físico
autónomo.

---

## Autor

**Alejandro Saez Vega**
Grado en Ingeniería de Sistemas de Telecomunicación
Universitat Politècnica de València

Tutor del TFG: Jose Javier López Monfort

---

## Licencia

Código fuente bajo licencia MIT. Ver `LICENSE`.

El dataset AKWF (Adventure Kid Waveforms) se distribuye bajo Creative Commons
Zero (CC0) y se incluye en `ml/dataset/` para que el pipeline sea reproducible
tal cual. Su origen es [la web del autor](https://www.adventurekid.se/).
