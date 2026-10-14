> [!WARNING]
> Requiert [Python 3.14 or higher](https://www.python.org/downloads/)

# Basic Installation

- Double Click on "install_prerequisites.bat"
- After prerequisite install double click on generator_contact_qr.pyw
- Interface appear !

> [!IMPORTANT]
> prerequisite pip package like qrcode, image, customtkinter (you can double click on requiremetents.txt if you want to see all package include), by default pip package are install in youre appdata "C:\Users\USERNAME\AppData\Local\Programs\Python\Python314\Lib\site-packages" 

# Virtual Environnement Installation
> [!NOTE]
> if you don't want to install pip package in you're appdata user

In Contact_QRCode_App folder open terminal

`python -m venv venv`

`.\venv\Scripts\activate`

`pip install -r requirements.txt`

# Web Version

The `web/` folder is a port of the application as a static website: no Python, no server, no installation. The QR code is generated directly in the browser, so contact details are never sent anywhere.

- **Try it locally**: double click on `web/index.html`, or serve the folder with `python -m http.server 8000 --directory web` and open http://localhost:8000
- **Put it online**: upload the content of `web/` to any static host (GitHub Pages, Netlify, OVH, etc.)

Compared to the desktop app:
- the preview updates live as you type, and the image can be downloaded as PNG or JPEG
- the image is rendered at twice the resolution, for sharper prints
- when "Include photo in QR code" is checked, the photo is compressed until it fits in the QR code instead of being silently dropped
- a warning is shown when the chosen color is too light to scan reliably

The QR encoding uses [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) 2.0.4 (MIT), stored in `web/vendor/`.
