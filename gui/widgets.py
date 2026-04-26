"""
gui/widgets.py
==============
Widgets reutilizables y constantes de diseño (paleta, fuentes).

Principios UX aplicados:
    - Contraste suficiente entre texto y fondo (accesibilidad)
    - Retroalimentación visual en hover y estados activos
    - Jerarquía tipográfica clara (título > subtítulo > cuerpo > pequeño)
    - Uso consistente del color para categorías (azul=media, verde=mediana,
      violeta=laplaciano, naranja=sobel)
"""

import tkinter as tk
from tkinter import ttk


# ══════════════════════════════════════════════════════════
#  Paleta de colores y fuentes
# ══════════════════════════════════════════════════════════

C = {
    # Fondos
    "bg":        "#16161E",
    "bg_panel":  "#1E1E2A",
    "bg_card":   "#252533",
    "bg_input":  "#2C2C3E",

    # Bordes
    "border":    "#3A3A52",
    "border_hi": "#5A5A7A",

    # Texto
    "text":      "#E2E2F0",
    "text_dim":  "#8888A8",
    "text_hi":   "#FFFFFF",

    # Acentos por filtro
    "mean":      "#3B82F6",   # azul
    "median":    "#22C55E",   # verde
    "laplacian": "#A855F7",   # violeta
    "sobel":     "#F59E0B",   # naranja

    # Estados
    "success":   "#22C55E",
    "warning":   "#F59E0B",
    "error":     "#EF4444",
    "info":      "#60A5FA",
}

F = {
    "h1":    ("Segoe UI", 15, "bold"),
    "h2":    ("Segoe UI", 11, "bold"),
    "h3":    ("Segoe UI", 10, "bold"),
    "body":  ("Segoe UI", 10),
    "small": ("Segoe UI", 9),
    "mono":  ("Consolas", 10),
    "mono_s":("Consolas", 9),
}

# Colores de cada pestaña (para header del panel)
TAB_COLORS = {
    "Media":      C["mean"],
    "Mediana":    C["median"],
    "Laplaciano": C["laplacian"],
    "Sobel":      C["sobel"],
}


# ══════════════════════════════════════════════════════════
#  Widget: ImageCanvas
# ══════════════════════════════════════════════════════════

class ImageCanvas(tk.Frame):
    """
    Área de visualización de una imagen con título y placeholder.
    Muestra un ícono descriptivo cuando no hay imagen cargada.
    """

    def __init__(self, parent, title: str, w: int = 320, h: int = 260, **kw):
        super().__init__(parent, bg=C["bg_card"], **kw)
        self._w, self._h = w, h
        self._ref = None          # evita garbage-collection del PhotoImage

        # Título sobre el canvas
        tk.Label(self, text=title, font=F["small"], fg=C["text_dim"],
                 bg=C["bg_card"]).pack(pady=(6, 2))

        self.canvas = tk.Canvas(self, width=w, height=h, bg=C["bg"],
                                highlightthickness=1,
                                highlightbackground=C["border"])
        self.canvas.pack(padx=8, pady=(0, 8))
        self._placeholder()

    # ─────────────────────────────────────────
    def _placeholder(self):
        self.canvas.delete("all")
        cx, cy = self._w // 2, self._h // 2
        r = 28
        # Ícono simple de imagen
        self.canvas.create_rectangle(cx - r, cy - r, cx + r, cy + r,
                                     outline=C["border"], width=1)
        self.canvas.create_oval(cx - 10, cy - 18, cx + 2, cy - 8,
                                outline=C["text_dim"], width=1)
        self.canvas.create_polygon(cx - r + 4, cy + r - 4,
                                   cx - 6, cy - 4,
                                   cx + 10, cy + 10,
                                   cx + r - 4, cy + r - 4,
                                   outline=C["text_dim"], fill="", width=1)
        self.canvas.create_text(cx, cy + r + 14, text="Sin imagen",
                                fill=C["text_dim"], font=F["small"])

    def show(self, photo):
        """Muestra un PhotoImage centrado en el canvas."""
        self._ref = photo
        self.canvas.delete("all")
        self.canvas.create_image(self._w // 2, self._h // 2,
                                 anchor="center", image=photo)

    def clear(self):
        self._ref = None
        self._placeholder()


# ══════════════════════════════════════════════════════════
#  Widget: FlatButton
# ══════════════════════════════════════════════════════════

class FlatButton(tk.Button):
    """Botón plano con retroalimentación de hover y estados."""

    _STYLES = {
        "primary": (C["mean"],    "#2563EB"),
        "green":   (C["median"],  "#16A34A"),
        "purple":  (C["laplacian"], "#9333EA"),
        "orange":  (C["sobel"],   "#D97706"),
        "ghost":   (C["bg_card"], C["bg_input"]),
        "danger":  (C["error"],   "#DC2626"),
    }

    def __init__(self, parent, text, cmd=None, style="primary", width=None, **kw):
        bg, hov = self._STYLES.get(style, self._STYLES["primary"])
        opts = dict(
            text=text, command=cmd,
            font=F["h3"], fg=C["text_hi"],
            bg=bg, activebackground=hov, activeforeground=C["text_hi"],
            relief="flat", bd=0, cursor="hand2",
            padx=12, pady=6,
        )
        if width:
            opts["width"] = width
        super().__init__(parent, **opts, **kw)
        self.bind("<Enter>", lambda _: self.config(bg=hov))
        self.bind("<Leave>", lambda _: self.config(bg=bg))


# ══════════════════════════════════════════════════════════
#  Widget: SectionTitle
# ══════════════════════════════════════════════════════════

class SectionTitle(tk.Frame):
    """Título de sección con acento de color izquierdo."""

    def __init__(self, parent, text: str, color: str = C["info"], **kw):
        super().__init__(parent, bg=C["bg_panel"], **kw)
        # Barra de color
        tk.Frame(self, bg=color, width=3).pack(side="left", fill="y", padx=(0, 6))
        tk.Label(self, text=text, font=F["h3"], fg=C["text"],
                 bg=C["bg_panel"]).pack(side="left", pady=4)


# ══════════════════════════════════════════════════════════
#  Widget: RadioGroup
# ══════════════════════════════════════════════════════════

class RadioGroup(tk.Frame):
    """Grupo de radio buttons con estilo oscuro."""

    def __init__(self, parent, options: list[tuple], variable: tk.Variable, **kw):
        """
        Args:
            options:  Lista de (valor, etiqueta_visible).
            variable: tk.StringVar o tk.IntVar que almacena la selección.
        """
        super().__init__(parent, bg=C["bg_panel"], **kw)
        for value, label in options:
            tk.Radiobutton(
                self, text=label, variable=variable, value=value,
                font=F["small"], fg=C["text"], bg=C["bg_panel"],
                selectcolor=C["bg"], activebackground=C["bg_panel"],
                activeforeground=C["text"], relief="flat", cursor="hand2",
            ).pack(anchor="w", padx=6, pady=1)


# ══════════════════════════════════════════════════════════
#  Widget: StatBar
# ══════════════════════════════════════════════════════════

class StatBar(tk.Frame):
    """Barra horizontal con estadísticas de la imagen resultante."""

    _FIELDS = [
        ("size",  "Tamaño"),
        ("min",   "Mín"),
        ("max",   "Máx"),
        ("mean",  "Media"),
        ("std",   "Desv. est."),
    ]

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["bg_card"], **kw)
        self._vars = {}
        for key, label in self._FIELDS:
            col = tk.Frame(self, bg=C["bg_card"])
            col.pack(side="left", padx=14, pady=6)
            tk.Label(col, text=label, font=F["small"], fg=C["text_dim"],
                     bg=C["bg_card"]).pack()
            var = tk.StringVar(value="—")
            self._vars[key] = var
            tk.Label(col, textvariable=var, font=F["h3"], fg=C["text"],
                     bg=C["bg_card"]).pack()

    def update(self, stats: dict):
        """Actualiza con un dict de image_stats() + label del FilterResult."""
        self._vars["size"].set(f"{stats['width']}×{stats['height']}")
        self._vars["min"].set(str(stats["min"]))
        self._vars["max"].set(str(stats["max"]))
        self._vars["mean"].set(str(stats["mean"]))
        self._vars["std"].set(str(stats["std"]))

    def clear(self):
        for v in self._vars.values():
            v.set("—")


# ══════════════════════════════════════════════════════════
#  Widget: StatusBar
# ══════════════════════════════════════════════════════════

class StatusBar(tk.Frame):
    """Barra de estado persistente en la parte inferior de la ventana."""

    _COLOR = {
        "info":    C["text_dim"],
        "success": C["success"],
        "warning": C["warning"],
        "error":   C["error"],
    }

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["bg"], height=28, **kw)
        self._var = tk.StringVar(value="  Listo. Carga una imagen para comenzar.")
        self._lbl = tk.Label(self, textvariable=self._var,
                             font=F["small"], fg=C["text_dim"],
                             bg=C["bg"], anchor="w")
        self._lbl.pack(fill="x", padx=8)

    def set(self, msg: str, level: str = "info"):
        self._var.set(f"  {msg}")
        self._lbl.config(fg=self._COLOR.get(level, C["text_dim"]))
