import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from PIL import ImageTk, Image
import os

# Importer les fonctions principales de ton script (à placer dans un module séparé)
from qrcode_portfolio import generate_qr_contact_image  # Ton script renommé sans le main()

class QRContactApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Générateur de QR Code de Contact")
        self.geometry("600x700")
        self.configure(bg="white")

        self.contact_info = {
            'name': tk.StringVar(),
            'phone': tk.StringVar(),
            'email': tk.StringVar(),
            'organization': tk.StringVar(),
            'url': tk.StringVar()
        }

        self.config = {
            'title': tk.StringVar(value="Name"),
            'description': tk.StringVar(value="Description"),
            'profile_image_path': tk.StringVar(),
            'qr_color': "black",
            'qr_background': "white",
            'background_color': "white",
            'title_color': "black",
            'description_color': "gray",
            'output_filename': "contact_qr.png",
            'title_font_size': 32,
            'description_font_size': 28,
            'qr_style': "rounded",
            'include_photo_in_qr': tk.BooleanVar(value=False),
            'title_bold': tk.BooleanVar(),
            'title_italic': tk.BooleanVar(),
            'title_underline': tk.BooleanVar(),
            'description_bold': tk.BooleanVar(),
            'description_italic': tk.BooleanVar(),
            'description_underline': tk.BooleanVar()
        }

        self.build_gui()

    def build_gui(self):
        frame = tk.Frame(self, bg="white")
        frame.pack(pady=10)

        for field, var in self.contact_info.items():
            tk.Label(frame, text=field.capitalize(), bg="white").pack()
            tk.Entry(frame, textvariable=var, width=50).pack()

        tk.Label(frame, text="Titre", bg="white").pack()
        tk.Entry(frame, textvariable=self.config['title'], width=50).pack()

        tk.Label(frame, text="Description", bg="white").pack()
        tk.Entry(frame, textvariable=self.config['description'], width=50).pack()

        # Styles
        tk.Label(frame, text="Styles Titre", bg="white").pack()
        for style in ['title_bold', 'title_italic', 'title_underline']:
            tk.Checkbutton(frame, text=style.split('_')[1], variable=self.config[style], bg="white").pack(anchor='w')

        tk.Label(frame, text="Styles Description", bg="white").pack()
        for style in ['description_bold', 'description_italic', 'description_underline']:
            tk.Checkbutton(frame, text=style.split('_')[1], variable=self.config[style], bg="white").pack(anchor='w')

        tk.Checkbutton(frame, text="Inclure photo dans le QR", variable=self.config['include_photo_in_qr'], bg="white").pack()

        tk.Button(frame, text="Choisir une photo de profil", command=self.select_image).pack(pady=5)
        tk.Button(frame, text="Choisir les couleurs", command=self.choose_colors).pack(pady=5)
        tk.Button(frame, text="Générer", command=self.generate_image).pack(pady=10)

    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.jpeg")])
        if path:
            self.config['profile_image_path'].set(path)

    def choose_colors(self):
        self.config['qr_color'] = colorchooser.askcolor(title="Couleur QR")[1]
        self.config['title_color'] = colorchooser.askcolor(title="Couleur Titre")[1]
        self.config['description_color'] = colorchooser.askcolor(title="Couleur Description")[1]

    def generate_image(self):
        args = {key: var.get() if isinstance(var, tk.Variable) else var
                for key, var in {**self.contact_info, **self.config}.items()}
        try:
            img = generate_qr_contact_image(**args)
            if img:
                img.show()
                messagebox.showinfo("Succès", "QR Code généré avec succès !")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la génération : {e}")

if __name__ == "__main__":
    app = QRContactApp()
    app.mainloop()
