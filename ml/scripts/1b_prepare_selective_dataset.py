import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
import tkinter as tk
from tkinter import ttk

DATASET_PATH = "./AKWF"

# Lee hasta 'limite' ondas .wav de una sola subcarpeta de AKWF.
def cargar_ondas(ruta_carpeta, num_muestras=512, limite=4):
    ondas = []
    nombres = []
    
    if not os.path.exists(ruta_carpeta):
        print(f"Error: No se encuentra la ruta {ruta_carpeta}")
        return np.array([]), []

    for archivo in os.listdir(ruta_carpeta):
        if archivo.endswith(".wav"):
            ruta_completa = os.path.join(ruta_carpeta, archivo)
            sample_rate, data = wavfile.read(ruta_completa)
            
            # Normalización a floats (-1.0 a 1.0)
            if data.dtype == np.int16:
                data = data / 32768.0
            elif data.dtype == np.int32:
                data = data / 2147483648.0
                
            # Control de dimensión (512 muestras)
            if len(data) >= num_muestras:
                ondas.append(data[:num_muestras])
                nombres.append(archivo)
                
            if len(ondas) >= limite:
                break
                
    return np.array(ondas), nombres

def graficar_seleccion():
    carpeta_seleccionada = combo_carpetas.get()
    
    if not carpeta_seleccionada:
        return
        
    ruta_completa = os.path.join(DATASET_PATH, carpeta_seleccionada)
    
    ondas_prueba, nombres_prueba = cargar_ondas(ruta_completa, limite=4)
    
    if len(ondas_prueba) == 0:
        print(f"No hay ondas .wav de 512 muestras en {carpeta_seleccionada}")
        return
        
    plt.close('all')
    
    plt.figure(figsize=(10, 6))
    for i in range(len(ondas_prueba)):
        plt.plot(ondas_prueba[i], label=nombres_prueba[i], linewidth=2)
        
    plt.title(f"Explorando Dataset: {carpeta_seleccionada}")
    plt.xlabel("Tiempo (Índice de la muestra)")
    plt.ylabel("Amplitud (-1.0 a 1.0)")
    plt.axhline(0, color='black', linewidth=0.5, linestyle='--')
    plt.legend(loc='upper right', fontsize='small')
    plt.grid(True, alpha=0.3)
    plt.show()

# --- Interfaz grafica ---

ventana = tk.Tk()
ventana.title("Panel de Control: Dataset AKWF")
ventana.geometry("350x150")
ventana.eval('tk::PlaceWindow . center')

# Subcarpetas de ./AKWF para llenar el desplegable
if os.path.exists(DATASET_PATH):
    subcarpetas = [d for d in os.listdir(DATASET_PATH) if os.path.isdir(os.path.join(DATASET_PATH, d))]
    subcarpetas.sort()
else:
    subcarpetas = []
    print("¡Aviso! No se ha encontrado la carpeta ./AKWF")

etiqueta = tk.Label(ventana, text="Selecciona una familia de ondas:", font=("Arial", 10))
etiqueta.pack(pady=(15, 5))

combo_carpetas = ttk.Combobox(ventana, values=subcarpetas, state="readonly", width=30)
combo_carpetas.pack(pady=5)

if subcarpetas:
    combo_carpetas.current(0)

boton = tk.Button(ventana, text="Cargar y Graficar", command=graficar_seleccion, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
boton.pack(pady=10)

ventana.mainloop()