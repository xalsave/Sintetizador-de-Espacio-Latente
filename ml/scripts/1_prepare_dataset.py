import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile

# Ruta a la carpeta principal donde has guardado todas las subcarpetas de AKWF
DATASET_PATH = "./AKWF"

def cargar_ondas(ruta_principal, num_muestras=512, limite=4):
    ondas = []
    nombres = []
    
    # os.walk recorre la carpeta principal y entra automáticamente en cada subcarpeta
    for directorio_raiz, carpetas, archivos in os.walk(ruta_principal):
        for archivo in archivos:
            if archivo.endswith(".wav"):
                ruta_completa = os.path.join(directorio_raiz, archivo)
                
                sample_rate, data = wavfile.read(ruta_completa)
                
                # 1. Normalización de amplitud (pasar de enteros a floats de -1.0 a 1.0)
                if data.dtype == np.int16:
                    data = data / 32768.0
                elif data.dtype == np.int32: # Por si hay algún archivo de 32 bits
                    data = data / 2147483648.0
                    
                # 2. Control de dimensión (queremos exactamente 512 muestras)
                if len(data) >= num_muestras:
                    ondas.append(data[:num_muestras])
                    
                    # Guardamos el nombre de la subcarpeta y del archivo para identificarlos
                    nombre_carpeta = os.path.basename(directorio_raiz)
                    nombres.append(f"{nombre_carpeta}/{archivo}")
                    
                # 3. Paramos cuando tengamos el número de ondas que hemos pedido
                if len(ondas) >= limite:
                    return np.array(ondas), nombres
                
    return np.array(ondas), nombres

ondas_prueba, nombres_prueba = cargar_ondas(DATASET_PATH, limite=4)

print(f"Forma de la matriz de datos: {ondas_prueba.shape}")
print("Generando gráfico...")

plt.figure(figsize=(10, 6))
for i in range(len(ondas_prueba)):
    plt.plot(ondas_prueba[i], label=nombres_prueba[i], linewidth=2)

plt.title("Visualización del Dataset AKWF (Clasificado por carpetas)")
plt.xlabel("Tiempo (Índice de la muestra)")
plt.ylabel("Amplitud (-1.0 a 1.0)")
plt.axhline(0, color='black', linewidth=0.5, linestyle='--')
plt.legend(loc='upper right', fontsize='small')
plt.grid(True, alpha=0.3)
plt.show()