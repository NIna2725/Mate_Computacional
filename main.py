"""
main.py
=======
Punto de entrada de la aplicación de filtrado de imágenes.

Uso:
    python main.py

Requisitos:
    pip install numpy opencv-python scipy Pillow
"""

import sys
import os

# Añade el directorio raíz del proyecto al sys.path para que los imports
# absolutos (core.*, gui.*) funcionen correctamente sin importar desde
# qué directorio se ejecute el script.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
