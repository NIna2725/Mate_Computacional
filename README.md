# Aplicación de Filtros de Imagen — MA475 UPC

Aplicación de escritorio en Python con interfaz gráfica Tkinter para aplicar
los cuatro filtros de procesamiento de imágenes estudiados en el curso MA475.

## Filtros implementados

| Filtro | Tipo | Uso principal |
|---|---|---|
| **Media** | Suavizado | Reduce ruido gaussiano |
| **Mediana** | Suavizado | Elimina ruido sal y pimienta |
| **Laplaciano** | Agudizamiento | Detecta bordes (2ª derivada) |
| **Sobel** | Agudizamiento | Detecta bordes con dirección (gradiente) |

## Estructura del proyecto

```
filtros_app/
├── main.py               # Punto de entrada
├── core/
│   ├── filters.py        # Algoritmos de filtrado (cv2, scipy)
│   └── image_utils.py    # Carga, conversión, ruido sintético
└── gui/
    ├── app.py            # Ventana principal y Notebook
    ├── panels.py         # Un panel por filtro
    └── widgets.py        # Widgets reutilizables y paleta de colores
```

## Instalación

```bash
pip install numpy opencv-python scipy Pillow
```

En Linux también puede ser necesario:
```bash
sudo apt install python3-tk
```

## Uso

```bash
python main.py
```

1. Haz clic en **Cargar imagen** (barra superior).
2. Selecciona cualquier imagen (PNG, JPG, BMP, TIFF, WEBP).
   La imagen se convierte a escala de grises automáticamente.
3. Navega entre las pestañas (**Media**, **Mediana**, **Laplaciano**, **Sobel**).
4. Configura los parámetros del filtro en el panel izquierdo.
5. Opcionalmente, agrega **ruido sintético** para ver el efecto del filtro.
6. Haz clic en **▶ Aplicar filtro**.
7. Usa **💾 Guardar resultado** para exportar la imagen filtrada.

## Opciones por filtro

### Filtro de la Media
- Tamaño de ventana: 3×3, 5×5, 7×7
- Tipo de kernel: Uniforme (todos los pesos iguales) o Gaussiana (pesos suaves)

### Filtro de la Mediana
- Tamaño de ventana: 3×3, 5×5, 7×7

### Operador Laplaciano
- Variantes de máscara: Cruz (−4), Cruz invertida (+4), Completo (−8), Completo invertido (+8)
- Normalización: Re-escalamiento lineal, Recorte (clip) o Módulo L

### Operador Sobel
- Salida: Magnitud |fx|+|fy|, Solo fx (bordes verticales) o Solo fy (bordes horizontales)
- Normalización: Re-escalamiento lineal, Recorte (clip) o Módulo L
- Muestra 4 imágenes simultáneas: original, magnitud, fx y fy

## Requisitos del sistema
- Python 3.10+
- numpy, opencv-python, scipy, Pillow
- Tkinter (incluido en Python en Windows/macOS; en Linux: `python3-tk`)
