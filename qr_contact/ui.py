import os
import threading
from tkinter import colorchooser, filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageColor, ImageTk

from .core import ContactQRGenerator
from .models import ContactInfo, ImageConfig


class QRContactApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("QR Contact Generator")
        self.geometry("900x800")

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.profile_image_path = None
        self.generated_qr = None

        self.color_primary = "#e0f2fe"
        self.color_secondary = "#f0f9ff"
        self.color_accent = "#7dd3fc"
        self.color_accent_dark = "#38bdf8"
        self.color_bg = "#f8fafc"
        self.color_card = "#ffffff"
        self.color_text = "#0f172a"
        self.color_text_secondary = "#475569"
        self.color_border = "#e2e8f0"
        self.color_success = "#86efac"
        self.color_success_dark = "#22c55e"

        self.configure(fg_color=self.color_bg)
        self.create_widgets()

    def create_widgets(self):
        main_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        title_frame = ctk.CTkFrame(
            main_container,
            fg_color=self.color_card,
            corner_radius=15,
            border_width=2,
            border_color=self.color_border,
        )
        title_frame.pack(fill="x", pady=(0, 20))

        title_label = ctk.CTkLabel(
            title_frame,
            text="Generateur de QR Code Contact",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.color_text,
        )
        title_label.pack(pady=20)

        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        left_frame = ctk.CTkFrame(
            content_frame,
            fg_color=self.color_card,
            corner_radius=15,
            border_width=2,
            border_color=self.color_border,
        )
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.create_form(left_frame)

        right_frame = ctk.CTkFrame(
            content_frame,
            fg_color=self.color_card,
            corner_radius=15,
            border_width=2,
            border_color=self.color_border,
        )
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        self.create_preview(right_frame)

    def create_form(self, parent):
        form_inner = ctk.CTkFrame(parent, fg_color="transparent")
        form_inner.pack(fill="both", expand=True, padx=20, pady=20)

        section_label = ctk.CTkLabel(
            form_inner,
            text="Informations de Contact",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.color_text,
        )
        section_label.pack(anchor="w", pady=(0, 15))

        self.name_entry = self.create_input(form_inner, "Nom complet *", "Jean Dupont")
        self.phone_entry = self.create_input(form_inner, "Telephone", "+33 6 12 34 56 78")
        self.email_entry = self.create_input(form_inner, "Email", "email@exemple.com")
        self.url_entry = self.create_input(form_inner, "Site web", "https://exemple.com")

        ctk.CTkLabel(
            form_inner,
            text="Personnalisation",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.color_text,
        ).pack(anchor="w", pady=(20, 15))

        self.title_entry = self.create_input(form_inner, "Titre", "Mon Contact")
        self.desc_entry = self.create_input(form_inner, "Description", "Scannez pour ajouter")

        photo_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        photo_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            photo_frame,
            text="Photo de profil",
            font=ctk.CTkFont(size=14),
            text_color=self.color_text,
        ).pack(side="left")

        self.photo_btn = ctk.CTkButton(
            photo_frame,
            text="Choisir",
            command=self.select_photo,
            width=100,
            fg_color=self.color_accent_dark,
            hover_color=self.color_accent,
            text_color="white",
        )
        self.photo_btn.pack(side="right")

        self.photo_label = ctk.CTkLabel(
            form_inner,
            text="Aucune photo",
            font=ctk.CTkFont(size=11),
            text_color=self.color_text_secondary,
        )
        self.photo_label.pack(anchor="w", pady=(0, 10))

        self.include_photo_var = ctk.BooleanVar(value=False)
        self.include_photo_check = ctk.CTkCheckBox(
            form_inner,
            text="Inclure la photo dans le QR code",
            variable=self.include_photo_var,
            font=ctk.CTkFont(size=12),
            text_color=self.color_text,
            fg_color=self.color_accent_dark,
            hover_color=self.color_accent,
        )
        self.include_photo_check.pack(anchor="w", pady=(0, 10))

        style_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        style_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            style_frame,
            text="Style QR",
            font=ctk.CTkFont(size=14),
            text_color=self.color_text,
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
            text_color="white",
        )
        style_menu.pack(side="right")

        color_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        color_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            color_frame,
            text="Couleur QR",
            font=ctk.CTkFont(size=14),
            text_color=self.color_text,
        ).pack(side="left")

        self.color_var = ctk.StringVar(value="#000000")
        self.color_var.trace_add("write", self._on_color_var_change)

        self.color_swatch = ctk.CTkFrame(
            color_frame,
            width=24,
            height=24,
            corner_radius=6,
            fg_color=self.color_var.get(),
        )
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
            text_color=self.color_text,
        )
        self.color_hex_entry.pack(side="right", padx=(10, 0))

        self.color_btn = ctk.CTkButton(
            color_frame,
            text="Choisir...",
            command=self.select_qr_color,
            width=100,
            fg_color=self.color_accent_dark,
            hover_color=self.color_accent,
            text_color="white",
        )
        self.color_btn.pack(side="right")
        self._update_color_swatch()

        btn_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(30, 0))

        self.generate_btn = ctk.CTkButton(
            btn_frame,
            text="Generer le QR Code",
            command=self.generate_qr,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=self.color_success_dark,
            hover_color=self.color_success,
            text_color="white",
        )
        self.generate_btn.pack(fill="x", pady=(0, 10))

        self.save_btn = ctk.CTkButton(
            btn_frame,
            text="Sauvegarder",
            command=self.save_qr,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color=self.color_accent_dark,
            hover_color=self.color_accent,
            text_color="white",
            state="disabled",
        )
        self.save_btn.pack(fill="x")

    def create_input(self, parent, label, placeholder):
        label_widget = ctk.CTkLabel(
            parent,
            text=label,
            font=ctk.CTkFont(size=14),
            text_color=self.color_text,
            anchor="w",
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
            text_color=self.color_text,
        )
        entry.pack(fill="x", pady=(0, 5))
        return entry

    def create_preview(self, parent):
        preview_inner = ctk.CTkFrame(parent, fg_color="transparent")
        preview_inner.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            preview_inner,
            text="Previsualisation",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.color_text,
        ).pack(pady=(0, 20))

        self.preview_frame = ctk.CTkFrame(
            preview_inner,
            fg_color=self.color_secondary,
            corner_radius=10,
            border_width=2,
            border_color=self.color_border,
            height=500,
        )
        self.preview_frame.pack(fill="both", expand=True)

        self.preview_label = ctk.CTkLabel(
            self.preview_frame,
            text="Le QR code apparaitra ici",
            font=ctk.CTkFont(size=16),
            text_color=self.color_text_secondary,
        )
        self.preview_label.pack(expand=True)

    def select_photo(self):
        filepath = filedialog.askopenfilename(
            title="Choisir une photo",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp"), ("Tous les fichiers", "*.*")],
        )
        if filepath:
            self.profile_image_path = filepath
            self.photo_label.configure(text=f"OK {os.path.basename(filepath)}")

    def select_qr_color(self):
        try:
            color = colorchooser.askcolor(title="Choisir la couleur du QR")
            if color and color[1]:
                self.color_var.set(color[1])
                self._update_color_swatch()
        except Exception:
            pass

    def _on_color_var_change(self, *_):
        self._update_color_swatch()

    def _update_color_swatch(self):
        color_hex = self.color_var.get() or "#000000"
        try:
            ImageColor.getrgb(color_hex)
            self.color_swatch.configure(fg_color=color_hex)
        except Exception:
            self.color_swatch.configure(fg_color=self.color_secondary)

    def generate_qr(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Erreur", "Le nom est obligatoire")
            return

        self.generate_btn.configure(state="disabled", text="Generation...")
        thread = threading.Thread(target=self._generate_qr_thread, args=(name,), daemon=True)
        thread.start()

    def _generate_qr_thread(self, name):
        try:
            contact = ContactInfo(
                name=name,
                phone=self.phone_entry.get().strip(),
                email=self.email_entry.get().strip(),
                url=self.url_entry.get().strip(),
            )
            config = ImageConfig(
                title=self.title_entry.get().strip() or "Mon Contact",
                description=self.desc_entry.get().strip() or "Scannez ce QR code",
                profile_image_path=self.profile_image_path,
                include_photo_in_qr=self.include_photo_var.get(),
                qr_style=self.style_var.get(),
                qr_color=self.color_var.get(),
                title_color=self.color_var.get(),
                description_color=self.color_var.get(),
            )
            result = ContactQRGenerator(contact, config).generate()

            if result:
                self.generated_qr = result
                self.after(0, lambda: self._update_preview(result))
                self.after(0, lambda: self._generation_complete(True))
            else:
                self.after(0, lambda: self._generation_complete(False))
        except Exception as err:
            self.after(0, lambda: messagebox.showerror("Erreur", f"Erreur: {err}"))
            self.after(0, lambda: self._generation_complete(False))

    def _update_preview(self, img: Image.Image):
        display_img = img.copy()
        display_img.thumbnail((450, 450), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(display_img)
        self.preview_label.configure(image=photo, text="")
        self.preview_label.image = photo

    def _generation_complete(self, success: bool):
        self.generate_btn.configure(state="normal", text="Generer le QR Code")
        if success:
            self.save_btn.configure(state="normal")
            messagebox.showinfo("Succes", "QR code genere avec succes")
        else:
            messagebox.showerror("Erreur", "Echec de la generation")

    def save_qr(self):
        if not self.generated_qr:
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("Tous", "*.*")],
            initialfile="contact_qr.png",
        )
        if filepath:
            try:
                self.generated_qr.save(filepath, quality=95)
                messagebox.showinfo("Succes", f"Image sauvegardee:\n{filepath}")
            except Exception as err:
                messagebox.showerror("Erreur", f"Erreur de sauvegarde: {err}")
