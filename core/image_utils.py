"""
core/image_utils.py
===================
Utilidades para manejo de imágenes: carga, conversión,
ruido sintético y helpers para Tkinter.
"""

import cv2
import numpy as np
from PIL import Image, ImageTk
from pathlib import Path


# ── Formatos soportados ───────────────────────────────────
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}


def load_grayscale(filepath: str) -> np.ndarray:
    """
    Carga una imagen desde disco y la convierte a escala de grises.

    Si la imagen ya es en grises, se retorna sin modificar.
    Si es color (RGB/RGBA), se convierte usando la fórmula estándar
    de luminancia: Y = 0.299R + 0.587G + 0.114B

    Args:
        filepath: Ruta al archivo de imagen.

    Returns:
        Array 2D uint8, escala de grises, rango [0, 255].

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError:        Si el formato no es soportado o la imagen es inválida.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {filepath}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Formato no soportado: {path.suffix}")

    # cv2.IMREAD_GRAYSCALE hace la conversión de color automáticamente
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"No se pudo leer la imagen: {filepath}")

    return image


def array_to_photoimage(
    array:      np.ndarray,
    max_width:  int = 340,
    max_height: int = 280,
) -> ImageTk.PhotoImage:
    """
    Convierte un array NumPy 2D (uint8) a PhotoImage de Tkinter,
    ajustando el tamaño para que quepa en el área de visualización.

    Args:
        array:      Array 2D uint8 (escala de grises).
        max_width:  Ancho máximo en píxeles.
        max_height: Alto máximo en píxeles.

    Returns:
        Objeto PhotoImage listo para usar en Canvas o Label de Tkinter.
    """
    pil_img = Image.fromarray(array, mode='L')
    pil_img = _resize_fit(pil_img, max_width, max_height)
    return ImageTk.PhotoImage(pil_img)


def _resize_fit(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    """Redimensiona manteniendo relación de aspecto (no amplía)."""
    w, h   = img.size
    scale  = min(max_w / w, max_h / h, 1.0)
    new_w  = max(1, int(w * scale))
    new_h  = max(1, int(h * scale))
    return img.resize((new_w, new_h), Image.LANCZOS)


def image_stats(array: np.ndarray) -> dict:
    """
    Calcula estadísticas básicas de una imagen.

    Returns:
        dict con keys: width, height, min, max, mean, std.
    """
    return {
        "width":  array.shape[1],
        "height": array.shape[0],
        "min":    int(array.min()),
        "max":    int(array.max()),
        "mean":   round(float(array.mean()), 1),
        "std":    round(float(array.std()), 1),
    }


# ── Generadores de ruido sintético ───────────────────────

def add_gaussian_noise(image: np.ndarray, sigma: float = 20.0) -> np.ndarray:
    """
    Agrega ruido gaussiano aditivo (útil para demostrar el filtro de media).

    Args:
        image: Array 2D uint8.
        sigma: Desviación estándar del ruido (más alto = más visible).

    Returns:
        Array 2D uint8 con ruido, recortado a [0, 255].
    """
    noise  = np.random.normal(0.0, sigma, image.shape)
    noisy  = image.astype(np.float64) + noise
    return np.clip(np.round(noisy), 0, 255).astype(np.uint8)


def add_salt_and_pepper(image: np.ndarray, density: float = 0.05) -> np.ndarray:
    """
    Agrega ruido 'sal y pimienta' (ideal para demostrar el filtro de mediana).

    Reemplaza aleatoriamente una fracción de los píxeles con 0 (pimienta)
    o 255 (sal).

    Args:
        image:   Array 2D uint8.
        density: Fracción de píxeles afectados (0.0 – 1.0).

    Returns:
        Array 2D uint8 con ruido impulsivo.
    """
    noisy      = image.copy()
    n_pixels   = image.size
    n_noise    = int(density * n_pixels)
    rng        = np.random.default_rng()

    indices    = rng.choice(n_pixels, n_noise, replace=False)
    rows, cols = np.unravel_index(indices, image.shape)

    half = n_noise // 2
    noisy[rows[:half], cols[:half]] = 0    # pimienta (negro)
    noisy[rows[half:], cols[half:]] = 255  # sal (blanco)

    return noisy
