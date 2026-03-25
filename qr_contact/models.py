from dataclasses import dataclass
from typing import Optional


@dataclass
class ContactInfo:
    name: str
    phone: str = ""
    email: str = ""
    url: str = ""


@dataclass
class ImageConfig:
    title: str = "Mon Contact"
    description: str = "Scannez ce QR code"
    output_filename: str = "contact_qr.png"
    profile_image_path: Optional[str] = None
    include_photo_in_qr: bool = False
    qr_style: str = "rounded"
    qr_color: str = "black"
    qr_background: str = "white"
    background_color: str = "white"
    title_color: str = "black"
    description_color: str = "gray"
    title_font_size: int = 32
    description_font_size: int = 28
