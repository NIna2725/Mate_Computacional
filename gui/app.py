"""
gui/app.py
==========
Ventana principal de la aplicación.

Responsabilidades:
    - Crear y configurar la ventana raíz de Tkinter
    - Mostrar la barra de herramientas (cargar imagen, info)
    - Gestionar el Notebook con las 4 pestañas de filtros
    - Distribuir la imagen cargada a todos los paneles
    - Manejar el StatusBar global
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core import load_grayscale, image_stats
from gui.widgets import C, F, StatusBar
from gui.panels import MeanPanel, MedianPanel, LaplacianPanel, SobelPanel


# ══════════════════════════════════════════════════════════
#  Ventana principal
# ══════════════════════════════════════════════════════════

class App(tk.Tk):
    """
    Ventana raíz de la aplicación de filtrado de imágenes.

    Organización visual:
        ┌────────────────────────────────────────────┐
        │  Toolbar  (carga de imagen + info rápida)  │
        ├────────────────────────────────────────────┤
        │  Notebook:  Media | Mediana | Lap | Sobel  │
        ├────────────────────────────────────────────┤
        │  StatusBar                                 │
        └────────────────────────────────────────────┘
    """

    TITLE   = "Filtros de Imagen — MA475 UPC"
    MIN_W   = 960
    MIN_H   = 740

    def __init__(self):
        super().__init__()
        self.title(self.TITLE)
        self.minsize(self.MIN_W, self.MIN_H)
        self.configure(bg=C["bg"])

        # Estado de la imagen actualmente cargada
        self._gray_image  = None
        self._image_path  = None

        self._apply_ttk_style()
        self._build_toolbar()
        self._build_notebook()
        self._build_statusbar()

        # Centrar ventana en la pantalla al iniciar
        self.update_idletasks()
        self._center_window()

    # ── Estilos ttk ──────────────────────────────────────

    def _apply_ttk_style(self):
        """Aplica estilos al Notebook de ttk para coincidir con la paleta oscura."""
        style = ttk.Style(self)
        style.theme_use("default")

        style.configure("TNotebook",
                        background=C["bg"],
                        borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=C["bg_card"],
                        foreground=C["text_dim"],
                        font=F["h3"],
                        padding=(14, 6),
                        borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", C["bg_panel"]),
                               ("active",   C["bg_input"])],
                  foreground=[("selected", C["text_hi"]),
                               ("active",   C["text"])])

    # ── Toolbar ──────────────────────────────────────────

    def _build_toolbar(self):
        """Barra superior con logo, controles de carga e información de imagen."""
        bar = tk.Frame(self, bg=C["bg_card"], pady=0)
        bar.pack(fill="x")

        # Logo / nombre de la app
        tk.Label(bar, text="🔬 Filtros de Imagen",
                 font=F["h2"], fg=C["text_hi"],
                 bg=C["bg_card"]).pack(side="left", padx=14, pady=10)

        tk.Frame(bar, bg=C["border"], width=1).pack(
            side="left", fill="y", pady=6, padx=8)

        # Botón de carga
        btn_load = tk.Button(
            bar, text="📂  Cargar imagen",
            command=self._load_image,
            font=F["h3"], fg=C["text_hi"],
            bg=C["mean"], activebackground="#2563EB",
            activeforeground=C["text_hi"],
            relief="flat", bd=0, cursor="hand2",
            padx=12, pady=6,
        )
        btn_load.pack(side="left", padx=6)
        btn_load.bind("<Enter>", lambda _: btn_load.config(bg="#2563EB"))
        btn_load.bind("<Leave>", lambda _: btn_load.config(bg=C["mean"]))

        # Info rápida de la imagen cargada
        tk.Frame(bar, bg=C["border"], width=1).pack(
            side="left", fill="y", pady=6, padx=8)

        self._info_var = tk.StringVar(value="Sin imagen cargada")
        tk.Label(bar, textvariable=self._info_var,
                 font=F["small"], fg=C["text_dim"],
                 bg=C["bg_card"]).pack(side="left", padx=6)

        # Separador inferior del toolbar
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")

    # ── Notebook ─────────────────────────────────────────

    def _build_notebook(self):
        """Crea el Notebook con una pestaña por filtro."""
        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True, padx=0, pady=0)

        # Instanciamos cada panel y lo añadimos como pestaña
        panels_config = [
            ("Media",       MeanPanel),
            ("Mediana",     MedianPanel),
            ("Laplaciano",  LaplacianPanel),
            ("Sobel",       SobelPanel),
        ]

        self._panels: dict[str, "BasePanel"] = {}

        for name, PanelClass in panels_config:
            frame = tk.Frame(self._nb, bg=C["bg_panel"])
            panel = PanelClass(frame, on_status=self._set_status)
            panel.pack(fill="both", expand=True)
            self._nb.add(frame, text=f"  {name}  ")
            self._panels[name] = panel

    # ── Status bar ───────────────────────────────────────

    def _build_statusbar(self):
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")
        self._status = StatusBar(self)
        self._status.pack(fill="x", side="bottom")

    def _set_status(self, msg: str, level: str = "info"):
        self._status.set(msg, level)

    # ── Carga de imagen ──────────────────────────────────

    def _load_image(self):
        """Abre el diálogo de selección de archivo y distribuye la imagen."""
        path = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not path:
            return  # usuario canceló

        try:
            gray = load_grayscale(path)
            self._gray_image = gray
            self._image_path = path

            # Actualiza el info de la toolbar
            st = image_stats(gray)
            self._info_var.set(
                f"📄 {path.split('/')[-1].split(chr(92))[-1]}   "
                f"│  {st['width']}×{st['height']} px   "
                f"│  Grises  │  Rango: {st['min']}–{st['max']}"
            )

            # Distribuye la imagen a TODOS los paneles
            for panel in self._panels.values():
                panel.load_image(gray)

            self._set_status(
                f"Imagen cargada: {path}  ({st['width']}×{st['height']} px)",
                "success"
            )

        except (FileNotFoundError, ValueError) as exc:
            messagebox.showerror("Error al cargar",
                                 f"No se pudo cargar la imagen:\n{exc}")
            self._set_status(f"Error al cargar imagen: {exc}", "error")

    # ── Centrado de ventana ──────────────────────────────

    def _center_window(self):
        """Centra la ventana en la pantalla del usuario."""
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w  = max(self.MIN_W, self.winfo_width())
        h  = max(self.MIN_H, self.winfo_height())
        x  = (sw - w) // 2
        y  = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
