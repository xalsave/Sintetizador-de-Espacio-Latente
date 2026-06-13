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
                                    + envolvente + MIDI
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

| Subsistema       | Hardware                    | Función                                     |
|------------------|-----------------------------|---------------------------------------------|
| Interfaz táctil  | CYD (ESP32-2432S028R)       | Pantalla TFT 2.8" + táctil resistivo        |
| Cerebro          | ESP32-S3 N16R8 (8 MB PSRAM) | Mapeo coordenada → wavetable, decoder       |
| Motor de audio   | Daisy Seed (STM32H750)      | Síntesis, MIDI, salida analógica            |
| Control MIDI     | Arturia Keystep MK2         | Teclado controlador                         |

**Flujo de datos:**

```
[CYD]──UART(115200)──►[ESP32-S3]──SPI(10MHz)──►[Daisy Seed]──audio──► jack 3.5
                                                     ▲
                                                     │ MIDI
                                                [Keystep MK2]
```

---

## Cómo funciona

### Fase offline (preparación, en PC)

1. **Preprocesado del dataset.** Se cargan ~4000 wavetables del corpus AKWF
   (Adventure Kid Waveforms), se remuestrean a 1024 muestras, se eliminan
   componentes DC, se alinean en fase mediante FFT y se normalizan.
2. **Entrenamiento del VAE.** Se entrena en PyTorch un autoencoder variacional
   con espacio latente bidimensional. El encoder mapea las ondas al plano
   latente; el decoder reconstruye una onda a partir de cualquier coordenada.
3. **Horneado del grid.** Se muestrea el plano latente en una rejilla regular
   (16×16 = 256 puntos), se decodifica una wavetable en cada nodo, y se
   exporta el banco como header de C para el firmware.

### Fase en vivo (en el instrumento)

1. La CYD lee el punto tocado en la pantalla y envía la coordenada (x, y)
   por UART al ESP32-S3.
2. El ESP32-S3 localiza la celda del grid correspondiente e **interpola
   bilinealmente** entre las cuatro wavetables vecinas, produciendo una
   wavetable suave para cualquier coordenada continua.
3. La wavetable resultante se envía por SPI al Daisy Seed.
4. El Daisy mantiene un **doble buffer** y aplica un **crossfade corto**
   al recibir una tabla nueva, eliminando clicks de cambio.
5. Un acumulador de fase con interpolación lineal entre muestras reproduce
   la tabla a la frecuencia indicada por el MIDI entrante del Keystep,
   modulada por una envolvente ADSR. La salida sale por el códec del Daisy
   a un jack 3.5mm.

### Ampliación (opcional, según tiempo)

Como extensión, se contempla embarcar el propio decoder neuronal cuantizado
a int8 en el ESP32-S3 mediante **TensorFlow Lite Micro**, sustituyendo la
interpolación bilineal sobre grid por inferencia neuronal directa para
cualquier punto del plano latente.

---

## Stack tecnológico

- **Machine Learning:** Python 3.10+, PyTorch, NumPy, SciPy, Matplotlib
- **Firmware Daisy:** C++ con libDaisy + DaisySP, ARM GCC, flasheo DFU
- **Firmware ESP32-S3 y CYD:** C++ con ESP-IDF o PlatformIO,
  TensorFlow Lite Micro (stretch goal)
- **Comunicación:** UART 8N1 a 115200 baud (CYD↔S3), SPI 10 MHz modo 0 (S3↔Daisy)
- **Audio:** códec interno del Daisy (24-bit, 48 kHz), señal mono replicada estéreo

---

## Estructura del repositorio

```
Sintetizador-de-Espacio-Latente/
├── ml/                       # Entorno Python: dataset, entrenamiento, exportación
│   ├── dataset/              # AKWF original + dataset procesado .npy
│   ├── scripts/              # 1_…, 2_…, 3_… numerados por orden de ejecución
│   └── exports/              # Modelos .tflite y headers .h para el firmware
├── firmware/                 # Código embebido
│   ├── esp32_control/        # Firmware del ESP32-S3
│   └── daisy_dsp/            # Firmware del Daisy Seed
├── hardware/
│   ├── cad/                  # Modelos 3D de la carcasa
│   └── schematics/           # Esquemas de cableado y alimentación
├── docs/               # Documentación técnica por subsistema
├── DISENO.md                 # Mapa maestro del proyecto
├── PROJECT.md                # Estado vivo, decisiones tomadas, planificación
└── README.md                 # Este archivo
```

---

## Estado del proyecto

🚧 **En desarrollo activo.** Inicio: junio 2026. Entrega prevista: agosto 2026.

Ver `PROJECT.md` para el plan detallado de las 11 sesiones de trabajo y el
estado actual de cada subsistema.

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
neuronal (ya explorada en plugins de DAW) sino en su **integración embebida
completa en tiempo real**, sobre hardware de bajo coste y con interfaz física
táctil y MIDI, llevando la idea de plugin de software a instrumento físico
autónomo.

---

## Autor

**Saúl Salvà** — saulsalva@…
Grado en Ingeniería de Sistemas de Telecomunicación
Universitat Politècnica de València

Tutor del TFG: *por confirmar*

---

## Licencia

Código fuente bajo licencia MIT. Ver `LICENSE`.

El dataset AKWF (Adventure Kid Waveforms) se distribuye bajo Creative Commons
Zero (CC0) y no está incluido en este repositorio; se descarga aparte desde
[la web del autor](https://www.adventurekid.se/).
