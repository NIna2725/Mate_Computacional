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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
