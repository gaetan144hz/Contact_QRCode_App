#!/usr/bin/env python3
"""Point d'entree de l'application QR Contact."""

from qr_contact.ui import QRContactApp


def main() -> None:
    try:
        import customtkinter  # noqa: F401
        import qrcode  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError:
        print("Dependances manquantes. Installez: pip install customtkinter qrcode[pil] pillow")
        return

    app = QRContactApp()
    app.mainloop()


if __name__ == "__main__":
    main()
