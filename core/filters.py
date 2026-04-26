"""
core/filters.py
===============
Implementación de los cuatro filtros de procesamiento de imágenes
del curso MA475 (UPC), usando cv2 y scipy internamente.

Filtros disponibles:
    - Filtro de la Media      → suavizado por promedio de vecindad
    - Filtro de la Mediana    → suavizado resistente a ruido impulsivo
    - Operador Laplaciano     → agudizamiento por 2ª derivada digital
    - Operador Sobel          → agudizamiento por gradiente (1ª derivada)

Convención de datos:
    - Entrada:  np.ndarray uint8, 2D (H, W), escala de grises [0, 255]
    - Salida:   np.ndarray uint8, 2D (H, W), escala de grises [0, 255]
"""

import cv2
import numpy as np
from scipy.ndimage import median_filter as scipy_median
from dataclasses import dataclass
from enum import Enum


# ══════════════════════════════════════════════════════════
#  Enumeraciones de opciones
# ══════════════════════════════════════════════════════════

class MeanKernelSize(Enum):
    K3x3 = 3
    K5x5 = 5
    K7x7 = 7

class MeanKernelShape(Enum):
    UNIFORM  = "Uniforme (igual peso)"
    GAUSSIAN = "Gaussiana (pesos suaves)"

class MedianKernelSize(Enum):
    K3x3 = 3
    K5x5 = 5
    K7x7 = 7

class LaplacianVariant(Enum):
    CROSS     = "Cruz (4-vecinos, −4)"
    CROSS_INV = "Cruz invertida (+4)"
    FULL      = "Completo (8-vecinos, −8)"
    FULL_INV  = "Completo invertido (+8)"

class SobelOutput(Enum):
    MAGNITUDE = "Magnitud  |fx| + |fy|"
    GRAD_X    = "Solo fx  (bordes verticales)"
    GRAD_Y    = "Solo fy  (bordes horizontales)"

class NormMode(Enum):
    RESCALE = "Re-escalamiento lineal"
    CLIP    = "Recorte (clip)"
    MODULO  = "Módulo L"


# ══════════════════════════════════════════════════════════
#  Resultado de un filtro (estructura de datos limpia)
# ══════════════════════════════════════════════════════════

@dataclass
class FilterResult:
    """Encapsula la salida de cualquier filtro aplicado."""
    image:      np.ndarray          # imagen filtrada principal (uint8)
    extras:     dict                # imágenes adicionales (ej. Sobel fx, fy)
    label:      str                 # descripción del resultado
    stats:      dict                # estadísticas útiles (min, max, mean)

    @classmethod
    def from_array(cls, arr: np.ndarray, label: str, extras: dict = None) -> "FilterResult":
        stats = {
            "min":  int(arr.min()),
            "max":  int(arr.max()),
            "mean": round(float(arr.mean()), 2),
            "std":  round(float(arr.std()), 2),
        }
        return cls(image=arr, extras=extras or {}, label=label, stats=stats)


# ══════════════════════════════════════════════════════════
#  Utilidades internas
# ══════════════════════════════════════════════════════════

def _normalize(raw: np.ndarray, mode: NormMode, L: int = 256) -> np.ndarray:
    """
    Lleva un array float de valores arbitrarios al rango uint8 [0, L-1].

    Métodos (según PDF MA475):
        RESCALE → mapeo lineal [min,max] → [0, L-1]  (más suave, recomendado)
        CLIP    → recorta valores fuera del rango      (más rápido)
        MODULO  → aplica mod L, tal como dice el PDF   (puede crear artefactos)
    """
    if mode == NormMode.RESCALE:
        vmin, vmax = raw.min(), raw.max()
        if vmax == vmin:
            return np.zeros_like(raw, dtype=np.uint8)
        scaled = (raw - vmin) / (vmax - vmin) * (L - 1)
        return np.clip(np.round(scaled), 0, L - 1).astype(np.uint8)

    elif mode == NormMode.MODULO:
        return (np.round(raw).astype(np.int32) % L).astype(np.uint8)

    else:  # CLIP
        return np.clip(np.round(raw), 0, L - 1).astype(np.uint8)


# ══════════════════════════════════════════════════════════
#  Filtro 1: Media
# ══════════════════════════════════════════════════════════

def apply_mean_filter(
    image:        np.ndarray,
    kernel_size:  MeanKernelSize  = MeanKernelSize.K3x3,
    kernel_shape: MeanKernelShape = MeanKernelShape.UNIFORM,
) -> FilterResult:
    """
    Filtro de suavizado por media aritmética (o gaussiana ponderada).

    Principio (PDF): reemplaza cada píxel por el promedio ponderado de su
    vecindad N×N. Reduce ruido gaussiano a costa de difuminar bordes.

    Implementación:
        - Uniforme  → cv2.blur  (convolución con todos los pesos = 1/N²)
        - Gaussiana → cv2.GaussianBlur  (pesos según distribución normal)

    Args:
        image:        Array 2D uint8.
        kernel_size:  Tamaño de la ventana (3, 5 o 7).
        kernel_shape: Tipo de ponderación (uniforme o gaussiana).

    Returns:
        FilterResult con la imagen suavizada.
    """
    k = kernel_size.value
    ksize = (k, k)

    if kernel_shape == MeanKernelShape.UNIFORM:
        # cv2.blur calcula el promedio aritmético exacto sobre la vecindad
        result = cv2.blur(image, ksize)
        label  = f"Media uniforme {k}×{k}"
    else:
        # GaussianBlur usa sigma automático óptimo para el tamaño dado
        result = cv2.GaussianBlur(image, ksize, sigmaX=0)
        label  = f"Media gaussiana {k}×{k}"

    return FilterResult.from_array(result, label)


# ══════════════════════════════════════════════════════════
#  Filtro 2: Mediana
# ══════════════════════════════════════════════════════════

def apply_median_filter(
    image:       np.ndarray,
    kernel_size: MedianKernelSize = MedianKernelSize.K3x3,
) -> FilterResult:
    """
    Filtro de suavizado por mediana.

    Principio (PDF): ordena los píxeles de la vecindad de menor a mayor
    y toma el valor central. Muy eficaz contra ruido "sal y pimienta"
    porque los valores extremos (0 ó 255) quedan en los bordes del arreglo
    ordenado y nunca llegan a ser la mediana.

    A diferencia de la media, NO crea nuevas intensidades de grises.

    Implementación:
        scipy.ndimage.median_filter → implementación en C, altamente optimizada.

    Args:
        image:       Array 2D uint8.
        kernel_size: Tamaño de la ventana (3, 5 o 7).

    Returns:
        FilterResult con la imagen filtrada.
    """
    k      = kernel_size.value
    result = scipy_median(image, size=k).astype(np.uint8)
    label  = f"Mediana {k}×{k}"
    return FilterResult.from_array(result, label)


# ══════════════════════════════════════════════════════════
#  Filtro 3: Laplaciano
# ══════════════════════════════════════════════════════════

# Máscaras Laplacianas (del PDF MA475, p.13-14)
_LAPLACIAN_MASKS = {
    LaplacianVariant.CROSS:     np.array([[ 0,  1,  0],
                                          [ 1, -4,  1],
                                          [ 0,  1,  0]], dtype=np.float32),

    LaplacianVariant.CROSS_INV: np.array([[ 0, -1,  0],
                                          [-1,  4, -1],
                                          [ 0, -1,  0]], dtype=np.float32),

    LaplacianVariant.FULL:      np.array([[ 1,  1,  1],
                                          [ 1, -8,  1],
                                          [ 1,  1,  1]], dtype=np.float32),

    LaplacianVariant.FULL_INV:  np.array([[-1, -1, -1],
                                          [-1,  8, -1],
                                          [-1, -1, -1]], dtype=np.float32),
}

def apply_laplacian_filter(
    image:    np.ndarray,
    variant:  LaplacianVariant = LaplacianVariant.CROSS,
    norm:     NormMode         = NormMode.RESCALE,
) -> FilterResult:
    """
    Filtro de agudizamiento basado en el Laplaciano (2ª derivada digital).

    Principio (PDF):
        ∇²f = ∂²f/∂x² + ∂²f/∂y²
            = f(x+1,y) + f(x−1,y) + f(x,y+1) + f(x,y−1) − 4·f(x,y)

    El Laplaciano resalta cambios bruscos de intensidad (bordes) en todas
    las direcciones (operador isotrópico). Al ser la 2ª derivada, produce
    bordes de 1 píxel de ancho y valores tanto positivos como negativos,
    por lo que se requiere normalización antes de visualizar.

    Implementación:
        cv2.filter2D con la máscara exacta del PDF (convolución 2D directa).

    Args:
        image:   Array 2D uint8.
        variant: Variante de máscara (ver LaplacianVariant).
        norm:    Método de normalización al rango [0, 255].

    Returns:
        FilterResult con la imagen de bordes detectados.
    """
    mask   = _LAPLACIAN_MASKS[variant]

    # cv2.filter2D aplica la convolución 2D. ddepth=-1 conserva el tipo de entrada,
    # pero necesitamos float32 para capturar valores negativos
    raw    = cv2.filter2D(image.astype(np.float32), ddepth=cv2.CV_32F, kernel=mask)
    result = _normalize(raw, norm)
    label  = f"Laplaciano — {variant.value}"
    return FilterResult.from_array(result, label)


# ══════════════════════════════════════════════════════════
#  Filtro 4: Sobel
# ══════════════════════════════════════════════════════════

def apply_sobel_filter(
    image:  np.ndarray,
    output: SobelOutput = SobelOutput.MAGNITUDE,
    norm:   NormMode    = NormMode.RESCALE,
) -> FilterResult:
    """
    Filtro de agudizamiento basado en el operador Sobel (1ª derivada — gradiente).

    Principio (PDF):
        fx = derivada parcial en x  → detecta bordes verticales
        fy = derivada parcial en y  → detecta bordes horizontales
        M  = |fx| + |fy|            → magnitud total del gradiente

    Las máscaras de Sobel del PDF:
        fx:  ⎡-1  0  1⎤      fy:  ⎡-1 -2 -1⎤
             ⎢-2  0  2⎥           ⎢ 0  0  0⎥
             ⎣-1  0  1⎦           ⎣ 1  2  1⎦

    A diferencia del Laplaciano, el Sobel incluye suavizado implícito en
    las direcciones perpendiculares, lo que lo hace más robusto al ruido.

    Implementación:
        cv2.Sobel con ksize=3, que usa exactamente las máscaras del PDF.

    Args:
        image:  Array 2D uint8.
        output: Qué imagen retornar (magnitud, fx o fy).
        norm:   Método de normalización al rango [0, 255].

    Returns:
        FilterResult con la imagen principal y extras {'fx', 'fy', 'magnitude'}.
    """
    # Calculamos ambas derivadas siempre (las necesitamos para la magnitud
    # y para guardarlas como extras aunque el usuario pida solo una)
    raw_fx = cv2.Sobel(image, cv2.CV_32F, dx=1, dy=0, ksize=3)
    raw_fy = cv2.Sobel(image, cv2.CV_32F, dx=0, dy=1, ksize=3)
    raw_m  = np.abs(raw_fx) + np.abs(raw_fy)

    # Normalizamos las tres salidas
    img_fx = _normalize(np.abs(raw_fx), norm)
    img_fy = _normalize(np.abs(raw_fy), norm)
    img_m  = _normalize(raw_m, norm)

    # Elegimos la imagen principal según la opción del usuario
    primary_map = {
        SobelOutput.MAGNITUDE: (img_m,  "Sobel — Magnitud |fx| + |fy|"),
        SobelOutput.GRAD_X:    (img_fx, "Sobel — Gradiente fx (bordes vert.)"),
        SobelOutput.GRAD_Y:    (img_fy, "Sobel — Gradiente fy (bordes horiz.)"),
    }
    primary_img, label = primary_map[output]

    extras = {"fx": img_fx, "fy": img_fy, "magnitude": img_m}
    return FilterResult.from_array(primary_img, label, extras)
