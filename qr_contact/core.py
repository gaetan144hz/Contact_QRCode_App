import base64
import io
import os
from typing import Optional

import qrcode
from PIL import Image, ImageColor, ImageDraw, ImageFont

from .models import ContactInfo, ImageConfig


class VCardGenerator:
    MAX_PHOTO_SIZE = 2000
    PHOTO_DIMENSIONS = (96, 96)

    @staticmethod
    def create(contact: ContactInfo, photo_path: Optional[str] = None, include_photo: bool = False) -> str:
        vcard_lines = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"FN:{contact.name}",
        ]

        if contact.phone:
            vcard_lines.append(f"TEL;TYPE=CELL:{contact.phone}")
        if contact.email:
            vcard_lines.append(f"EMAIL;TYPE=INTERNET:{contact.email}")
        if contact.url:
            vcard_lines.append(f"URL:{contact.url}")

        if include_photo and photo_path and os.path.exists(photo_path):
            photo_data = VCardGenerator._encode_photo(photo_path)
            if photo_data:
                vcard_lines.append(f"PHOTO;ENCODING=b;TYPE=JPEG:{photo_data}")

        vcard_lines.append("END:VCARD")
        return "\n".join(vcard_lines)

    @staticmethod
    def _encode_photo(photo_path: str) -> Optional[str]:
        try:
            with Image.open(photo_path) as img:
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                img.thumbnail(VCardGenerator.PHOTO_DIMENSIONS, Image.Resampling.LANCZOS)
                width, height = img.size

                if width != height:
                    size = min(width, height)
                    left = (width - size) // 2
                    top = (height - size) // 2
                    img = img.crop((left, top, left + size, top + size))
                    img = img.resize(VCardGenerator.PHOTO_DIMENSIONS, Image.Resampling.LANCZOS)

                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=75, optimize=True)
                photo_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

                if len(photo_base64) > VCardGenerator.MAX_PHOTO_SIZE:
                    return None

                return photo_base64
        except Exception:
            return None


class QRStyler:
    @staticmethod
    def apply(qr_img: Image.Image, style: str, bg_color: str) -> Image.Image:
        if style == "square":
            return qr_img
        if style == "rounded":
            return QRStyler._apply_rounded(qr_img, bg_color)
        return qr_img

    @staticmethod
    def _apply_rounded(qr_img: Image.Image, bg_color: str) -> Image.Image:
        if qr_img.mode != "RGBA":
            qr_img = qr_img.convert("RGBA")

        width, height = qr_img.size
        mask = Image.new("L", (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)

        radius = min(width, height) // 20
        mask_draw.rounded_rectangle([0, 0, width - 1, height - 1], radius=radius, fill=255)

        styled = Image.new("RGBA", (width, height), (*ImageColor.getrgb(bg_color), 255))
        styled.paste(qr_img, (0, 0))
        styled.putalpha(mask)
        return styled


class FontManager:
    FONT_PATHS = [
        "arial.ttf",
        "/System/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    @staticmethod
    def load(size: int) -> ImageFont.FreeTypeFont:
        for path in FontManager.FONT_PATHS:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
        return ImageFont.load_default()


class ContactQRGenerator:
    PADDING = 50
    TITLE_HEIGHT = 80
    DESC_HEIGHT = 60
    SPACING = 30
    PROFILE_SIZE = 120
    PROFILE_SPACING = 20

    def __init__(self, contact: ContactInfo, config: ImageConfig):
        self.contact = contact
        self.config = config

    def generate(self) -> Optional[Image.Image]:
        vcard_data = VCardGenerator.create(
            self.contact, self.config.profile_image_path, self.config.include_photo_in_qr
        )

        qr_img = self._create_qr_code(vcard_data)
        if not qr_img:
            return None

        return self._compose_final_image(qr_img)

    def _create_qr_code(self, data: str) -> Optional[Image.Image]:
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=8,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)

            qr_img = qr.make_image(fill_color=self.config.qr_color, back_color=self.config.qr_background)
            return QRStyler.apply(qr_img, self.config.qr_style, self.config.qr_background)
        except Exception:
            return None

    def _compose_final_image(self, qr_img: Image.Image) -> Image.Image:
        qr_size = qr_img.size[0]
        has_profile = self.config.profile_image_path and os.path.exists(self.config.profile_image_path)
        extra_height = (self.PROFILE_SIZE + self.PROFILE_SPACING) if has_profile else 0

        width = max(qr_size + (self.PADDING * 2), 400)
        height = qr_size + self.TITLE_HEIGHT + self.DESC_HEIGHT + (self.SPACING * 2) + (self.PADDING * 2) + extra_height

        img = Image.new("RGB", (width, height), self.config.background_color)
        draw = ImageDraw.Draw(img)

        title_font = FontManager.load(self.config.title_font_size)
        desc_font = FontManager.load(self.config.description_font_size)

        current_y = self.PADDING
        if has_profile:
            current_y = self._add_profile_photo(img, current_y)

        current_y = self._add_centered_text(draw, self.config.title, current_y, title_font, self.config.title_color, width)
        current_y += self.TITLE_HEIGHT

        current_y = self._add_centered_text(
            draw, self.config.description, current_y, desc_font, self.config.description_color, width
        )
        current_y += self.DESC_HEIGHT + self.SPACING

        self._add_qr_code(img, qr_img, current_y, width)
        return img

    def _add_profile_photo(self, img: Image.Image, y_pos: int) -> int:
        try:
            profile = Image.open(self.config.profile_image_path)
            profile = self._prepare_circular_photo(profile)
            x_pos = (img.width - self.PROFILE_SIZE) // 2

            temp = Image.new("RGB", (self.PROFILE_SIZE, self.PROFILE_SIZE), self.config.background_color)
            if profile.mode == "RGBA":
                temp.paste(profile, (0, 0), profile)
            else:
                temp.paste(profile, (0, 0))

            img.paste(temp, (x_pos, y_pos))
            draw = ImageDraw.Draw(img)
            draw.ellipse(
                [x_pos - 1, y_pos - 1, x_pos + self.PROFILE_SIZE + 1, y_pos + self.PROFILE_SIZE + 1],
                outline=self.config.title_color,
                width=2,
            )
            return y_pos + self.PROFILE_SIZE + self.PROFILE_SPACING
        except Exception:
            return y_pos

    def _prepare_circular_photo(self, img: Image.Image) -> Image.Image:
        ratio = max(self.PROFILE_SIZE / img.width, self.PROFILE_SIZE / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

        left = (img.width - self.PROFILE_SIZE) // 2
        top = (img.height - self.PROFILE_SIZE) // 2
        img = img.crop((left, top, left + self.PROFILE_SIZE, top + self.PROFILE_SIZE))

        mask = Image.new("L", (self.PROFILE_SIZE, self.PROFILE_SIZE), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, self.PROFILE_SIZE, self.PROFILE_SIZE), fill=255)
        img.putalpha(mask)
        return img

    def _add_centered_text(
        self, draw: ImageDraw.ImageDraw, text: str, y_pos: int, font: ImageFont.FreeTypeFont, color: str, width: int
    ) -> int:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x_pos = (width - text_width) // 2
        draw.text((x_pos, y_pos), text, fill=color, font=font)
        return y_pos

    def _add_qr_code(self, img: Image.Image, qr_img: Image.Image, y_pos: int, width: int) -> None:
        qr_size = qr_img.size[0]
        x_pos = (width - qr_size) // 2

        if qr_img.mode == "RGBA":
            bg = Image.new("RGB", qr_img.size, self.config.qr_background)
            bg.paste(qr_img, (0, 0), qr_img)
            qr_img = bg
        elif qr_img.mode != "RGB":
            qr_img = qr_img.convert("RGB")

        img.paste(qr_img, (x_pos, y_pos))
