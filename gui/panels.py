"""
gui/panels.py
=============
Un panel por cada filtro. Cada uno hereda de BasePanel y es
completamente independiente: gestiona sus propios controles,
estado y visualización.

Paneles:
    MeanPanel       → Filtro de la Media
    MedianPanel     → Filtro de la Mediana
    LaplacianPanel  → Operador Laplaciano
    SobelPanel      → Operador Sobel
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import numpy as np

from core import (
    apply_mean_filter, apply_median_filter,
    apply_laplacian_filter, apply_sobel_filter,
    MeanKernelSize, MeanKernelShape,
    MedianKernelSize, LaplacianVariant,
    SobelOutput, NormMode,
    array_to_photoimage, image_stats,
    add_gaussian_noise, add_salt_and_pepper,
)
from gui.widgets import (
    C, F, ImageCanvas, FlatButton,
    SectionTitle, RadioGroup, StatBar,
)


# ══════════════════════════════════════════════════════════
#  BasePanel: lógica y layout compartidos
# ══════════════════════════════════════════════════════════

class BasePanel(tk.Frame):
    """
    Clase base para todos los paneles de filtro.

    Layout estándar:
        ┌─────────────────────────────────────────────┐
        │  Header  (color de acento + nombre)          │
        ├──────────────┬──────────────────────────────┤
        │  Controles   │  Imágenes (original | result) │
        │  (izquierda) │  + StatBar                   │
        └──────────────┴──────────────────────────────┘

    Subclases deben implementar:
        _build_controls(frame)  → construye los widgets de configuración
        _run_filter()           → ejecuta el filtro y retorna FilterResult
    """

    NAME:  str = "Filtro"
    COLOR: str = C["info"]
    DESC:  str = ""

    def __init__(self, parent, on_status=None, **kw):
        super().__init__(parent, bg=C["bg_panel"], **kw)
        self._gray:   np.ndarray | None = None   # imagen en grises activa
        self._result: np.ndarray | None = None   # último resultado
        self._status = on_status or (lambda m, l="info": None)
        self._build_ui()

    # ── UI ───────────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=self.COLOR, pady=8)
        hdr.pack(fill="x")
        tk.Label(hdr, text=self.NAME, font=F["h1"],
                 fg="white", bg=self.COLOR).pack(side="left", padx=14)
        tk.Label(hdr, text=self.DESC, font=F["small"],
                 fg="#DDDDFF", bg=self.COLOR,
                 wraplength=480, justify="left").pack(side="left", padx=6)

        # Cuerpo: controles | visualización
        body = tk.Frame(self, bg=C["bg_panel"])
        body.pack(fill="both", expand=True, padx=10, pady=8)

        # Columna izquierda: controles
        ctrl = tk.Frame(body, bg=C["bg_panel"], width=230)
        ctrl.pack(side="left", fill="y", padx=(0, 10))
        ctrl.pack_propagate(False)
        self._build_controls(ctrl)

        # Columna derecha: imágenes + estadísticas
        vis = tk.Frame(body, bg=C["bg_panel"])
        vis.pack(side="left", fill="both", expand=True)
        self._build_image_area(vis)

    def _build_image_area(self, parent):
        """Layout de imagen original | imagen resultado + StatBar."""
        row = tk.Frame(parent, bg=C["bg_panel"])
        row.pack(fill="both", expand=True)

        # Original
        lf = tk.Frame(row, bg=C["bg_panel"])
        lf.pack(side="left", expand=True, fill="both")
        self._cv_orig = ImageCanvas(lf, "Imagen original", w=310, h=260)
        self._cv_orig.pack(expand=True)

        tk.Frame(row, bg=C["border"], width=1).pack(
            side="left", fill="y", pady=8, padx=4)

        # Resultado
        rf = tk.Frame(row, bg=C["bg_panel"])
        rf.pack(side="left", expand=True, fill="both")
        self._cv_res = ImageCanvas(rf, "Resultado", w=310, h=260)
        self._cv_res.pack(expand=True)

        # Estadísticas del resultado
        SectionTitle(parent, "Estadísticas del resultado",
                     color=self.COLOR).pack(fill="x", pady=(6, 2))
        self._statbar = StatBar(parent)
        self._statbar.pack(fill="x")

    # ── API pública ──────────────────────────────────────

    def load_image(self, gray: np.ndarray):
        """Recibe la imagen en grises desde la ventana principal."""
        self._gray   = gray
        self._result = None
        self._cv_orig.show(array_to_photoimage(gray, 310, 260))
        self._cv_res.clear()
        self._statbar.clear()

    def apply(self):
        """Ejecuta el filtro y actualiza la visualización."""
        if self._gray is None:
            messagebox.showwarning("Sin imagen",
                                   "Carga una imagen antes de aplicar el filtro.")
            return
        try:
            self._status(f"Aplicando {self.NAME}…", "info")
            self.update_idletasks()
            fr = self._run_filter()
            self._result = fr.image
            self._cv_res.show(array_to_photoimage(fr.image, 310, 260))
            self._statbar.update({**image_stats(fr.image)})
            self._status(f"{self.NAME} aplicado correctamente.", "success")
        except Exception as exc:
            self._status(f"Error: {exc}", "error")
            messagebox.showerror("Error al filtrar",
                                 f"Ocurrió un error:\n{exc}")

    def save(self):
        """Guarda el resultado en disco."""
        if self._result is None:
            self._status("No hay resultado que guardar.", "warning")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp")],
            title="Guardar imagen filtrada",
        )
        if path:
            Image.fromarray(self._result, mode="L").save(path)
            self._status(f"Guardado en: {path}", "success")

    def clear(self):
        """Restablece el panel."""
        self._gray = self._result = None
        self._cv_orig.clear()
        self._cv_res.clear()
        self._statbar.clear()
        self._status("Panel limpiado.", "info")

    # ── Controles de ruido (compartidos) ─────────────────

    def _noise_section(self, parent):
        SectionTitle(parent, "Ruido sintético", color=self.COLOR).pack(
            fill="x", pady=(10, 4))
        tk.Label(parent,
                 text="Agrega ruido a la imagen cargada\npara probar el filtro:",
                 font=F["small"], fg=C["text_dim"], bg=C["bg_panel"],
                 justify="left").pack(anchor="w", padx=6)
        row = tk.Frame(parent, bg=C["bg_panel"])
        row.pack(fill="x", pady=4)
        FlatButton(row, "Gaussiano", cmd=self._noise_gaussian,
                   style="ghost").pack(side="left", padx=(0, 4))
        FlatButton(row, "Sal/pimienta", cmd=self._noise_sp,
                   style="ghost").pack(side="left")

    def _noise_gaussian(self):
        if not self._check_loaded(): return
        self._gray = add_gaussian_noise(self._gray, sigma=22.0)
        self._cv_orig.show(array_to_photoimage(self._gray, 310, 260))
        self._status("Ruido gaussiano agregado.", "info")

    def _noise_sp(self):
        if not self._check_loaded(): return
        self._gray = add_salt_and_pepper(self._gray, density=0.05)
        self._cv_orig.show(array_to_photoimage(self._gray, 310, 260))
        self._status("Ruido sal y pimienta agregado.", "info")

    def _check_loaded(self) -> bool:
        if self._gray is None:
            self._status("Carga una imagen primero.", "warning")
            return False
        return True

    # ── Botones de acción (compartidos) ──────────────────

    def _action_buttons(self, parent, apply_style="primary"):
        tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", pady=(12, 6))
        FlatButton(parent, "▶  Aplicar filtro",
                   cmd=self.apply, style=apply_style).pack(fill="x", pady=2)
        FlatButton(parent, "💾  Guardar resultado",
                   cmd=self.save, style="ghost").pack(fill="x", pady=2)
        FlatButton(parent, "✕  Limpiar panel",
                   cmd=self.clear, style="ghost").pack(fill="x", pady=2)

    # ── Abstractos ───────────────────────────────────────

    def _build_controls(self, parent): raise NotImplementedError
    def _run_filter(self): raise NotImplementedError


# ══════════════════════════════════════════════════════════
#  Panel 1: Filtro de la Media
# ══════════════════════════════════════════════════════════

class MeanPanel(BasePanel):

    NAME  = "Filtro de la Media"
    COLOR = C["mean"]
    DESC  = ("Reduce ruido reemplazando cada píxel "
             "por el promedio de su vecindad N×N.")

    def _build_controls(self, p):
        # Tamaño del kernel
        self._ksize = tk.IntVar(value=3)
        SectionTitle(p, "Tamaño de ventana", color=self.COLOR).pack(fill="x")
        RadioGroup(p, [(3,"3×3  (9 vecinos)"),
                       (5,"5×5  (25 vecinos)"),
                       (7,"7×7  (49 vecinos)")],
                   self._ksize).pack(anchor="w", pady=4)

        # Tipo de kernel
        self._kshape = tk.StringVar(value=MeanKernelShape.UNIFORM.value)
        SectionTitle(p, "Tipo de ponderación", color=self.COLOR).pack(fill="x", pady=(8,0))
        RadioGroup(p, [(MeanKernelShape.UNIFORM.value,  "Uniforme  (igual peso)"),
                       (MeanKernelShape.GAUSSIAN.value, "Gaussiana (pesos suaves)")],
                   self._kshape).pack(anchor="w", pady=4)

        # Vista previa de máscara
        SectionTitle(p, "Máscara activa", color=self.COLOR).pack(fill="x", pady=(8,0))
        self._mask_lbl = tk.Label(p, text=self._mask_text(),
                                  font=F["mono"], fg=C["text"],
                                  bg=C["bg_card"], justify="center",
                                  pady=6, padx=8)
        self._mask_lbl.pack(fill="x", pady=4)
        self._ksize.trace_add("write", lambda *_: self._mask_lbl.config(
            text=self._mask_text()))
        self._kshape.trace_add("write", lambda *_: self._mask_lbl.config(
            text=self._mask_text()))

        self._noise_section(p)
        self._action_buttons(p, apply_style="primary")

    def _mask_text(self) -> str:
        k = self._ksize.get()
        if self._kshape.get() == MeanKernelShape.GAUSSIAN.value and k == 3:
            return ("1/16 ×\n"
                    "⎡1 2 1⎤\n"
                    "⎢2 4 2⎥\n"
                    "⎣1 2 1⎦")
        n = k * k
        row = " ".join(["1"] * k)
        rows = "\n".join([f"⎢{row}⎥"] * k)
        rows = f"⎡{row}⎤\n" + rows[2:-2] + f"\n⎣{row}⎦"
        return f"1/{n} ×\n{rows}"

    def _run_filter(self):
        ks = next(e for e in MeanKernelSize if e.value == self._ksize.get())
        ksh = next(e for e in MeanKernelShape if e.value == self._kshape.get())
        return apply_mean_filter(self._gray, ks, ksh)


# ══════════════════════════════════════════════════════════
#  Panel 2: Filtro de la Mediana
# ══════════════════════════════════════════════════════════

class MedianPanel(BasePanel):

    NAME  = "Filtro de la Mediana"
    COLOR = C["median"]
    DESC  = ("Elimina ruido 'sal y pimienta' usando el valor central "
             "del arreglo ordenado de la vecindad. No crea nuevas intensidades.")

    def _build_controls(self, p):
        self._ksize = tk.IntVar(value=3)
        SectionTitle(p, "Tamaño de ventana", color=self.COLOR).pack(fill="x")
        RadioGroup(p, [(3,"3×3  (9 vecinos)"),
                       (5,"5×5  (25 vecinos)"),
                       (7,"7×7  (49 vecinos)")],
                   self._ksize).pack(anchor="w", pady=4)

        # Descripción del algoritmo
        SectionTitle(p, "Algoritmo", color=self.COLOR).pack(fill="x", pady=(8,0))
        tk.Label(p,
                 text=("① Extrae vecindad N×N\n"
                       "② Ordena valores ↑\n"
                       "③ Toma el valor central\n"
                       "④ Reemplaza el píxel"),
                 font=F["small"], fg=C["text_dim"],
                 bg=C["bg_panel"], justify="left").pack(anchor="w", padx=8, pady=4)

        self._noise_section(p)
        self._action_buttons(p, apply_style="green")

    def _run_filter(self):
        ks = next(e for e in MedianKernelSize if e.value == self._ksize.get())
        return apply_median_filter(self._gray, ks)


# ══════════════════════════════════════════════════════════
#  Panel 3: Operador Laplaciano
# ══════════════════════════════════════════════════════════

_LAP_MASKS_TEXT = {
    LaplacianVariant.CROSS:     "⎡ 0  1  0⎤\n⎢ 1 -4  1⎥\n⎣ 0  1  0⎦",
    LaplacianVariant.CROSS_INV: "⎡ 0 -1  0⎤\n⎢-1  4 -1⎥\n⎣ 0 -1  0⎦",
    LaplacianVariant.FULL:      "⎡ 1  1  1⎤\n⎢ 1 -8  1⎥\n⎣ 1  1  1⎦",
    LaplacianVariant.FULL_INV:  "⎡-1 -1 -1⎤\n⎢-1  8 -1⎥\n⎣-1 -1 -1⎦",
}

class LaplacianPanel(BasePanel):

    NAME  = "Operador Laplaciano"
    COLOR = C["laplacian"]
    DESC  = ("Agudizamiento por 2ª derivada: ∇²f = ∂²f/∂x² + ∂²f/∂y². "
             "Detecta bordes en todas las direcciones (isotrópico).")

    def _build_controls(self, p):
        # Variante de máscara
        self._variant = tk.StringVar(value=LaplacianVariant.CROSS.value)
        SectionTitle(p, "Variante de máscara", color=self.COLOR).pack(fill="x")
        RadioGroup(p, [(v.value, v.value) for v in LaplacianVariant],
                   self._variant).pack(anchor="w", pady=4)

        # Vista previa de máscara
        SectionTitle(p, "Máscara seleccionada", color=self.COLOR).pack(fill="x", pady=(8,0))
        self._mask_lbl = tk.Label(p, text=_LAP_MASKS_TEXT[LaplacianVariant.CROSS],
                                  font=F["mono"], fg=C["text"],
                                  bg=C["bg_card"], justify="center",
                                  pady=6, padx=10)
        self._mask_lbl.pack(fill="x", pady=4)
        self._variant.trace_add("write", self._update_mask_preview)

        # Normalización
        self._norm = tk.StringVar(value=NormMode.RESCALE.value)
        SectionTitle(p, "Normalización al rango [0,255]",
                     color=self.COLOR).pack(fill="x", pady=(8,0))
        RadioGroup(p, [(n.value, n.value) for n in NormMode],
                   self._norm).pack(anchor="w", pady=4)

        self._action_buttons(p, apply_style="purple")

    def _update_mask_preview(self, *_):
        v = next((e for e in LaplacianVariant if e.value == self._variant.get()), None)
        if v:
            self._mask_lbl.config(text=_LAP_MASKS_TEXT[v])

    def _run_filter(self):
        v = next(e for e in LaplacianVariant if e.value == self._variant.get())
        n = next(e for e in NormMode if e.value == self._norm.get())
        return apply_laplacian_filter(self._gray, v, n)


# ══════════════════════════════════════════════════════════
#  Panel 4: Operador Sobel
# ══════════════════════════════════════════════════════════

class SobelPanel(BasePanel):
    """
    Panel Sobel con layout extendido de 4 imágenes:
        original  |  magnitud
        grad fx   |  grad fy
    """

    NAME  = "Operador Sobel"
    COLOR = C["sobel"]
    DESC  = ("Agudizamiento por gradiente: M = |fx| + |fy|. "
             "Detecta bordes verticales (fx), horizontales (fy) y su combinación.")

    def _build_image_area(self, parent):
        """Sobrescribe el layout para mostrar 4 imágenes."""
        # Fila 1: original + magnitud
        r1 = tk.Frame(parent, bg=C["bg_panel"])
        r1.pack(fill="both", expand=True)

        lf = tk.Frame(r1, bg=C["bg_panel"])
        lf.pack(side="left", expand=True, fill="both")
        self._cv_orig = ImageCanvas(lf, "Original", w=295, h=220)
        self._cv_orig.pack(expand=True)

        tk.Frame(r1, bg=C["border"], width=1).pack(
            side="left", fill="y", pady=6, padx=3)

        rf = tk.Frame(r1, bg=C["bg_panel"])
        rf.pack(side="left", expand=True, fill="both")
        self._cv_res = ImageCanvas(rf, "Magnitud  |fx| + |fy|", w=295, h=220)
        self._cv_res.pack(expand=True)

        tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", pady=4)

        # Fila 2: fx + fy
        r2 = tk.Frame(parent, bg=C["bg_panel"])
        r2.pack(fill="both", expand=True)

        gxf = tk.Frame(r2, bg=C["bg_panel"])
        gxf.pack(side="left", expand=True, fill="both")
        self._cv_fx = ImageCanvas(gxf, "Gradiente fx  (bordes verticales)",
                                  w=295, h=200)
        self._cv_fx.pack(expand=True)

        tk.Frame(r2, bg=C["border"], width=1).pack(
            side="left", fill="y", pady=6, padx=3)

        gyf = tk.Frame(r2, bg=C["bg_panel"])
        gyf.pack(side="left", expand=True, fill="both")
        self._cv_fy = ImageCanvas(gyf, "Gradiente fy  (bordes horizontales)",
                                  w=295, h=200)
        self._cv_fy.pack(expand=True)

        # Estadísticas
        SectionTitle(parent, "Estadísticas de la magnitud",
                     color=self.COLOR).pack(fill="x", pady=(6, 2))
        self._statbar = StatBar(parent)
        self._statbar.pack(fill="x")

    def _build_controls(self, p):
        # Salida principal
        self._output = tk.StringVar(value=SobelOutput.MAGNITUDE.value)
        SectionTitle(p, "Salida principal", color=self.COLOR).pack(fill="x")
        RadioGroup(p, [(o.value, o.value) for o in SobelOutput],
                   self._output).pack(anchor="w", pady=4)

        # Normalización
        self._norm = tk.StringVar(value=NormMode.RESCALE.value)
        SectionTitle(p, "Normalización", color=self.COLOR).pack(fill="x", pady=(8,0))
        RadioGroup(p, [(n.value, n.value) for n in NormMode],
                   self._norm).pack(anchor="w", pady=4)

        # Referencia de máscaras
        SectionTitle(p, "Máscaras de Sobel", color=self.COLOR).pack(fill="x", pady=(8,0))
        tk.Label(p,
                 text=("fx:\n⎡-1  0  1⎤\n⎢-2  0  2⎥\n⎣-1  0  1⎦\n\n"
                       "fy:\n⎡-1 -2 -1⎤\n⎢ 0  0  0⎥\n⎣ 1  2  1⎦"),
                 font=F["mono_s"], fg=C["text"], bg=C["bg_card"],
                 justify="left", pady=6, padx=8).pack(fill="x", pady=4)

        self._action_buttons(p, apply_style="orange")

    def apply(self):
        """Sobrescribimos para actualizar las 4 imágenes."""
        if self._gray is None:
            messagebox.showwarning("Sin imagen",
                                   "Carga una imagen antes de aplicar el filtro.")
            return
        try:
            self._status("Aplicando Operador Sobel…", "info")
            self.update_idletasks()

            out = next(e for e in SobelOutput if e.value == self._output.get())
            nrm = next(e for e in NormMode    if e.value == self._norm.get())
            fr  = apply_sobel_filter(self._gray, out, nrm)

            self._result = fr.image
            self._cv_res.show(array_to_photoimage(fr.image, 295, 220))
            self._cv_fx.show(array_to_photoimage(fr.extras["fx"], 295, 200))
            self._cv_fy.show(array_to_photoimage(fr.extras["fy"], 295, 200))
            self._statbar.update({**image_stats(fr.image)})
            self._status("Operador Sobel aplicado correctamente.", "success")
        except Exception as exc:
            self._status(f"Error: {exc}", "error")
            messagebox.showerror("Error al filtrar", f"Error:\n{exc}")

    def clear(self):
        super().clear()
        self._cv_fx.clear()
        self._cv_fy.clear()

    def _run_filter(self):   # no se usa directamente (apply() está sobrescrito)
        pass
