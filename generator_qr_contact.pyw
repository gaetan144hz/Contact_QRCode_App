#!/usr/bin/env python3
"""
Interface GUI pour le générateur de QR Code contact
Utilise customtkinter avec un thème gradient bleu-violet
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox, colorchooser
from PIL import Image, ImageTk
import qrcode
from PIL import ImageDraw, ImageFont, ImageColor
import io
import os
import base64
from dataclasses import dataclass
from typing import Optional
import threading


# ===== CLASSES DU GÉNÉRATEUR (simplifiées) =====

@dataclass
class ContactInfo:
    name: str
    phone: str = ""
    email: str = ""
    #organization: str = ""
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


class VCardGenerator:
    MAX_PHOTO_SIZE = 2000
    PHOTO_DIMENSIONS = (96, 96)
    
    @staticmethod
    def create(contact: ContactInfo, photo_path: Optional[str] = None, 
               include_photo: bool = False) -> str:
        vcard_lines = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"FN:{contact.name}"
        ]
        
        #if contact.organization:
        #    vcard_lines.append(f"ORG:{contact.organization}")
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
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                img.thumbnail(VCardGenerator.PHOTO_DIMENSIONS, Image.Resampling.LANCZOS)
                width, height = img.size
                
                if width != height:
                    size = min(width, height)
                    left = (width - size) // 2
                    top = (height - size) // 2
                    img = img.crop((left, top, left + size, top + size))
                    img = img.resize(VCardGenerator.PHOTO_DIMENSIONS, Image.Resampling.LANCZOS)
                
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=75, optimize=True)
                photo_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                if len(photo_base64) > VCardGenerator.MAX_PHOTO_SIZE:
                    return None
                
                return photo_base64
                
        except Exception:
            return None


class QRStyler:
    @staticmethod
    def apply(qr_img: Image, style: str, bg_color: str) -> Image:
        if style == "square":
            return qr_img
        
        if style == "rounded":
            return QRStyler._apply_rounded(qr_img, bg_color)
        
        return qr_img
    
    @staticmethod
    def _apply_rounded(qr_img: Image, bg_color: str) -> Image:
        if qr_img.mode != 'RGBA':
            qr_img = qr_img.convert('RGBA')
        
        width, height = qr_img.size
        mask = Image.new('L', (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)
        
        radius = min(width, height) // 20
        mask_draw.rounded_rectangle([0, 0, width-1, height-1], radius=radius, fill=255)
        
        styled = Image.new('RGBA', (width, height), (*ImageColor.getrgb(bg_color), 255))
        styled.paste(qr_img, (0, 0))
        styled.putalpha(mask)
        
        return styled


class FontManager:
    FONT_PATHS = [
        "arial.ttf",
        "/System/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    
    @staticmethod
    def load(size: int) -> ImageFont:
        for path in FontManager.FONT_PATHS:
            try:
                return ImageFont.truetype(path, size)
            except:
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
            self.contact,
            self.config.profile_image_path,
            self.config.include_photo_in_qr
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
            
            qr_img = qr.make_image(
                fill_color=self.config.qr_color,
                back_color=self.config.qr_background
            )
            
            return QRStyler.apply(qr_img, self.config.qr_style, self.config.qr_background)
            
        except Exception:
            return None
    
    def _compose_final_image(self, qr_img: Image) -> Image.Image:
        qr_size = qr_img.size[0]
        
        has_profile = (self.config.profile_image_path and 
                      os.path.exists(self.config.profile_image_path))
        extra_height = (self.PROFILE_SIZE + self.PROFILE_SPACING) if has_profile else 0
        
        width = max(qr_size + (self.PADDING * 2), 400)
        height = (qr_size + self.TITLE_HEIGHT + self.DESC_HEIGHT + 
                 (self.SPACING * 2) + (self.PADDING * 2) + extra_height)
        
        img = Image.new('RGB', (width, height), self.config.background_color)
        draw = ImageDraw.Draw(img)
        
        title_font = FontManager.load(self.config.title_font_size)
        desc_font = FontManager.load(self.config.description_font_size)
        
        current_y = self.PADDING
        
        if has_profile:
            current_y = self._add_profile_photo(img, current_y)
        
        current_y = self._add_centered_text(
            draw, self.config.title, current_y, 
            title_font, self.config.title_color, width
        )
        current_y += self.TITLE_HEIGHT
        
        current_y = self._add_centered_text(
            draw, self.config.description, current_y,
            desc_font, self.config.description_color, width
        )
        current_y += self.DESC_HEIGHT + self.SPACING
        
        self._add_qr_code(img, qr_img, current_y, width)
        
        return img
    
    def _add_profile_photo(self, img: Image, y_pos: int) -> int:
        try:
            profile = Image.open(self.config.profile_image_path)
            profile = self._prepare_circular_photo(profile)
            
            x_pos = (img.width - self.PROFILE_SIZE) // 2
            
            temp = Image.new('RGB', (self.PROFILE_SIZE, self.PROFILE_SIZE), 
                           self.config.background_color)
            if profile.mode == 'RGBA':
                temp.paste(profile, (0, 0), profile)
            else:
                temp.paste(profile, (0, 0))
            
            img.paste(temp, (x_pos, y_pos))
            
            draw = ImageDraw.Draw(img)
            draw.ellipse(
                [x_pos-1, y_pos-1, x_pos + self.PROFILE_SIZE+1, y_pos + self.PROFILE_SIZE+1],
                outline=self.config.title_color, width=2
            )
            
            return y_pos + self.PROFILE_SIZE + self.PROFILE_SPACING
            
        except Exception:
            return y_pos
    
    def _prepare_circular_photo(self, img: Image) -> Image:
        ratio = max(self.PROFILE_SIZE / img.width, self.PROFILE_SIZE / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        left = (img.width - self.PROFILE_SIZE) // 2
        top = (img.height - self.PROFILE_SIZE) // 2
        img = img.crop((left, top, left + self.PROFILE_SIZE, top + self.PROFILE_SIZE))
        
        mask = Image.new('L', (self.PROFILE_SIZE, self.PROFILE_SIZE), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, self.PROFILE_SIZE, self.PROFILE_SIZE), fill=255)
        img.putalpha(mask)
        
        return img
    
    def _add_centered_text(self, draw: ImageDraw, text: str, y_pos: int,
                          font: ImageFont, color: str, width: int) -> int:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x_pos = (width - text_width) // 2
        draw.text((x_pos, y_pos), text, fill=color, font=font)
        return y_pos
    
    def _add_qr_code(self, img: Image, qr_img: Image, y_pos: int, width: int):
        qr_size = qr_img.size[0]
        x_pos = (width - qr_size) // 2
        
        if qr_img.mode == 'RGBA':
            bg = Image.new('RGB', qr_img.size, self.config.qr_background)
            bg.paste(qr_img, (0, 0), qr_img)
            qr_img = bg
        elif qr_img.mode != 'RGB':
            qr_img = qr_img.convert('RGB')
        
        img.paste(qr_img, (x_pos, y_pos))


# ===== INTERFACE GUI =====

class GradientFrame(ctk.CTkFrame):
    """Frame avec gradient bleu-violet"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")


class QRContactApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuration de la fenêtre
        self.title("QR Contact Generator")
        self.geometry("900x800")
        
        # Thème customtkinter en mode clair
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Variables
        self.profile_image_path = None
        self.preview_image = None
        self.generated_qr = None
        
        # Palette harmonieuse de couleurs claires
        self.color_primary = "#e0f2fe"  # Bleu ciel très clair
        self.color_secondary = "#f0f9ff"  # Bleu glacier
        self.color_accent = "#7dd3fc"  # Bleu ciel
        self.color_accent_dark = "#38bdf8"  # Bleu vif
        self.color_bg = "#f8fafc"  # Gris très clair
        self.color_card = "#ffffff"  # Blanc
        self.color_text = "#0f172a"  # Gris très foncé
        self.color_text_secondary = "#475569"  # Gris moyen
        self.color_border = "#e2e8f0"  # Gris clair
        self.color_success = "#86efac"  # Vert clair
        self.color_success_dark = "#22c55e"  # Vert
        
        self.configure(fg_color=self.color_bg)
        
        self.create_widgets()
    
    def create_widgets(self):
        # Container principal avec scrollbar
        main_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Titre principal
        title_frame = ctk.CTkFrame(main_container, fg_color=self.color_card, corner_radius=15, border_width=2, border_color=self.color_border)
        title_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="🎨 Générateur de QR Code Contact",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.color_text
        )
        title_label.pack(pady=20)
        
        # Conteneur à deux colonnes
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        
        # Colonne gauche - Formulaire
        left_frame = ctk.CTkFrame(content_frame, fg_color=self.color_card, corner_radius=15, border_width=2, border_color=self.color_border)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.create_form(left_frame)
        
        # Colonne droite - Prévisualisation
        right_frame = ctk.CTkFrame(content_frame, fg_color=self.color_card, corner_radius=15, border_width=2, border_color=self.color_border)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        self.create_preview(right_frame)
    
    def create_form(self, parent):
        """Crée le formulaire de saisie"""
        form_inner = ctk.CTkFrame(parent, fg_color="transparent")
        form_inner.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Section Contact
        section_label = ctk.CTkLabel(
            form_inner,
            text="📇 Informations de Contact",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.color_text
        )
        section_label.pack(anchor="w", pady=(0, 15))
        
        # Nom
        self.name_entry = self.create_input(form_inner, "👤 Nom complet *", "Jean Dupont")
        
        # Téléphone
        self.phone_entry = self.create_input(form_inner, "📱 Téléphone", "+33 6 12 34 56 78")
        
        # Email
        self.email_entry = self.create_input(form_inner, "📧 Email", "email@exemple.com")
        
        # Organisation REWORK THIS PART FOR IPHONE BECAUSE IT DOESN'T SUPPORT ORG FIELD WELL
        #self.org_entry = self.create_input(form_inner, "🏢 Organisation", "Mon Entreprise")
        
        # URL
        self.url_entry = self.create_input(form_inner, "🌐 Site web", "https://exemple.com")
        
        # Section Personnalisation
        ctk.CTkLabel(
            form_inner,
            text="🎨 Personnalisation",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.color_text
        ).pack(anchor="w", pady=(20, 15))
        
        # Titre
        self.title_entry = self.create_input(form_inner, "✏️ Titre", "Mon Contact")
        
        # Description
        self.desc_entry = self.create_input(form_inner, "📝 Description", "Scannez pour ajouter")
        
        # Photo de profil
        photo_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        photo_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            photo_frame,
            text="📷 Photo de profil",
            font=ctk.CTkFont(size=14),
            text_color=self.color_text
        ).pack(side="left")
        
        self.photo_btn = ctk.CTkButton(
            photo_frame,
            text="Choisir",
            command=self.select_photo,
            width=100,
            fg_color=self.color_accent_dark,
            hover_color=self.color_accent,
            text_color="white"
        )
        self.photo_btn.pack(side="right")
        
        self.photo_label = ctk.CTkLabel(
            form_inner,
            text="Aucune photo",
            font=ctk.CTkFont(size=11),
            text_color=self.color_text_secondary
        )
        self.photo_label.pack(anchor="w", pady=(0, 10))
        
        # Inclure photo dans QR
        self.include_photo_var = ctk.BooleanVar(value=False)
        self.include_photo_check = ctk.CTkCheckBox(
            form_inner,
            text="Inclure la photo dans le QR code",
            variable=self.include_photo_var,
            font=ctk.CTkFont(size=12),
            text_color=self.color_text,
            fg_color=self.color_accent_dark,
            hover_color=self.color_accent
        )
        self.include_photo_check.pack(anchor="w", pady=(0, 10))
        
        # Style QR
        style_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        style_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            style_frame,
            text="🎭 Style QR",
            font=ctk.CTkFont(size=14),
            text_color=self.color_text
        ).pack(side="left")
        
        self.style_var = ctk.StringVar(value="rounded")
        style_menu = ctk.CTkOptionMenu(
            style_frame,
            values=["rounded", "square"],
            variable=self.style_var,
            width=120,
            fg_color=self.color_accent_dark,
            button_color=self.color_accent,
            button_hover_color=self.color_accent_dark,
            text_color="white"
        )
        style_menu.pack(side="right")
        
        # Couleur QR
        color_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        color_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            color_frame,
            text="🎨 Couleur QR",
            font=ctk.CTkFont(size=14),
            text_color=self.color_text
        ).pack(side="left")
        
        self.color_var = ctk.StringVar(value="#000000")
        # Mettre à jour le swatch quand la couleur change
        self.color_var.trace_add('write', self._on_color_var_change)

        # Bouton color chooser et swatch
        self.color_swatch = ctk.CTkFrame(color_frame, width=24, height=24, corner_radius=6, fg_color=self.color_var.get())
        self.color_swatch.pack(side="right", padx=(10, 0))

        self.color_hex_entry = ctk.CTkEntry(
            color_frame,
            placeholder_text="#000000",
            textvariable=self.color_var,
            width=120,
            height=36,
            font=ctk.CTkFont(size=13),
            fg_color=self.color_secondary,
            border_color=self.color_border,
            placeholder_text_color=self.color_text_secondary,
            text_color=self.color_text
        )
        self.color_hex_entry.pack(side="right", padx=(10, 0))

        self.color_btn = ctk.CTkButton(
            color_frame,
            text="Choisir...",
            command=self.select_qr_color,
            width=100,
            fg_color=self.color_accent_dark,
            hover_color=self.color_accent,
            text_color="white"
        )
        self.color_btn.pack(side="right")

        # Initialiser le swatch
        self._update_color_swatch()
        
        # Boutons d'action
        btn_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(30, 0))
        
        self.generate_btn = ctk.CTkButton(
            btn_frame,
            text="✨ Générer le QR Code",
            command=self.generate_qr,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=self.color_success_dark,
            hover_color=self.color_success,
            text_color="white"
        )
        self.generate_btn.pack(fill="x", pady=(0, 10))
        
        self.save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Sauvegarder",
            command=self.save_qr,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color=self.color_accent_dark,
            hover_color=self.color_accent,
            text_color="white",
            state="disabled"
        )
        self.save_btn.pack(fill="x")
    
    def create_input(self, parent, label, placeholder):
        """Crée un champ de saisie avec label"""
        label_widget = ctk.CTkLabel(
            parent,
            text=label,
            font=ctk.CTkFont(size=14),
            text_color=self.color_text,
            anchor="w"
        )
        label_widget.pack(fill="x", pady=(10, 5))
        
        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color=self.color_secondary,
            border_color=self.color_border,
            placeholder_text_color=self.color_text_secondary,
            text_color=self.color_text
        )
        entry.pack(fill="x", pady=(0, 5))
        
        return entry
    
    def create_preview(self, parent):
        """Crée la zone de prévisualisation"""
        preview_inner = ctk.CTkFrame(parent, fg_color="transparent")
        preview_inner.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            preview_inner,
            text="👁️ Prévisualisation",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.color_text
        ).pack(pady=(0, 20))
        
        # Zone d'affichage
        self.preview_frame = ctk.CTkFrame(
            preview_inner,
            fg_color=self.color_secondary,
            corner_radius=10,
            border_width=2,
            border_color=self.color_border,
            height=500
        )
        self.preview_frame.pack(fill="both", expand=True)
        
        self.preview_label = ctk.CTkLabel(
            self.preview_frame,
            text="Le QR code apparaîtra ici\n\n✨",
            font=ctk.CTkFont(size=16),
            text_color=self.color_text_secondary
        )
        self.preview_label.pack(expand=True)
    
    def select_photo(self):
        """Sélectionne une photo de profil"""
        filepath = filedialog.askopenfilename(
            title="Choisir une photo",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("Tous les fichiers", "*.*")
            ]
        )
        
        if filepath:
            self.profile_image_path = filepath
            filename = os.path.basename(filepath)
            self.photo_label.configure(text=f"✓ {filename}")

    def select_qr_color(self):
        """Ouvre le color chooser natif et met à jour la couleur choisie"""
        try:
            color = colorchooser.askcolor(title="Choisir la couleur du QR")
            if color and color[1]:
                self.color_var.set(color[1])
                self._update_color_swatch()
        except Exception:
            # Ignorer les erreurs du colorchooser
            pass

    def _on_color_var_change(self, *args):
        """Callback quand la variable de couleur change (entrée manuelle)."""
        self._update_color_swatch()

    def _update_color_swatch(self):
        """Met à jour le swatch de couleur pour refléter la couleur choisie."""
        color_hex = self.color_var.get() or "#000000"
        try:
            # Validate color by converting to rgb
            rgb = ImageColor.getrgb(color_hex)
            # If valid, update the swatch
            self.color_swatch.configure(fg_color=color_hex)
        except Exception:
            # Invalid color: use a neutral color and do nothing else
            self.color_swatch.configure(fg_color=self.color_secondary)
    
    def generate_qr(self):
        """Génère le QR code"""
        # Validation
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Erreur", "Le nom est obligatoire !")
            return
        
        # Désactiver le bouton pendant la génération
        self.generate_btn.configure(state="disabled", text="⏳ Génération...")
        
        # Générer dans un thread séparé
        thread = threading.Thread(target=self._generate_qr_thread, args=(name,))
        thread.start()
    
    def _generate_qr_thread(self, name):
        """Génère le QR code dans un thread"""
        try:
            # Créer la configuration
            contact = ContactInfo(
                name=name,
                phone=self.phone_entry.get().strip(),
                email=self.email_entry.get().strip(),
                #organization=self.org_entry.get().strip(),
                url=self.url_entry.get().strip()
            )
            
            config = ImageConfig(
                title=self.title_entry.get().strip() or "Mon Contact",
                description=self.desc_entry.get().strip() or "Scannez ce QR code",
                profile_image_path=self.profile_image_path,
                include_photo_in_qr=self.include_photo_var.get(),
                qr_style=self.style_var.get(),
                qr_color=self.color_var.get(),
                title_color=self.color_var.get(),
                description_color=self.color_var.get()
            )
            
            # Générer
            generator = ContactQRGenerator(contact, config)
            result = generator.generate()
            
            if result:
                self.generated_qr = result
                self._update_preview(result)
                self.after(0, lambda: self._generation_complete(True))
            else:
                self.after(0, lambda: self._generation_complete(False))
                
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erreur", f"Erreur: {str(e)}"))
            self.after(0, lambda: self._generation_complete(False))
    
    def _update_preview(self, img):
        """Met à jour la prévisualisation"""
        # Redimensionner pour l'affichage
        display_img = img.copy()
        display_img.thumbnail((450, 450), Image.Resampling.LANCZOS)
        
        # Convertir pour tkinter
        photo = ImageTk.PhotoImage(display_img)
        
        # Mettre à jour l'affichage
        self.preview_label.configure(image=photo, text="")
        self.preview_label.image = photo  # Garder une référence
    
    def _generation_complete(self, success):
        """Appelé après la génération"""
        if success:
            self.generate_btn.configure(state="normal", text="✨ Générer le QR Code")
            self.save_btn.configure(state="normal")
            messagebox.showinfo("Succès", "QR code généré avec succès ! ✅")
        else:
            self.generate_btn.configure(state="normal", text="✨ Générer le QR Code")
            messagebox.showerror("Erreur", "Échec de la génération")
    
    def save_qr(self):
        """Sauvegarde le QR code"""
        if not self.generated_qr:
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("Tous", "*.*")],
            initialfile="contact_qr.png"
        )
        
        if filepath:
            try:
                self.generated_qr.save(filepath, quality=95)
                messagebox.showinfo("Succès", f"Image sauvegardée :\n{filepath}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur de sauvegarde : {str(e)}")


def main():
    """Lance l'application"""
    try:
        import customtkinter
        import qrcode
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as e:
        print("❌ Dépendances manquantes !")
        print("Installez avec : pip install customtkinter qrcode[pil] pillow")
        return
    
    app = QRContactApp()
    app.mainloop()


if __name__ == "__main__":
    main()