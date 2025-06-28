#!/usr/bin/env python3
"""
Générateur de QR Code pour contact - Version avec formatage de texte
Crée une image avec titre, description et QR code contenant les données de contact
Nouvelles options: gras, italique, souligné pour le titre et la description
"""

import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageColor
import io
import os

def create_vcard(name, phone="", email="", organization="", url="", include_photo_in_qr=False, photo_path=None):
    """
    Crée une vCard (format standard pour les contacts)
    Option pour inclure ou non la photo dans le QR code
    """
    vcard = f"""BEGIN:VCARD
VERSION:3.0
FN:{name}"""
    
    # Ajouter les champs seulement s'ils ne sont pas vides
    if organization:
        vcard += f"\nORG:{organization}"
    if phone:
        vcard += f"\nTEL;TYPE=CELL:{phone}"  # Spécifier le type de téléphone
    if email:
        vcard += f"\nEMAIL;TYPE=INTERNET:{email}"  # Spécifier le type d'email
    if url:
        vcard += f"\nURL:{url}"
    
    # Ajouter la photo seulement si explicitement demandé ET si le fichier existe
    if include_photo_in_qr and photo_path and os.path.exists(photo_path):
        try:
            import base64
            
            # Optimiser l'image pour la compatibilité maximale
            with Image.open(photo_path) as img:
                # Convertir en RGB si nécessaire
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Redimensionner à une taille optimale pour vCard (96x96 recommandé)
                img.thumbnail((96, 96), Image.Resampling.LANCZOS)
                
                # Créer une image carrée si nécessaire
                width, height = img.size
                if width != height:
                    size = min(width, height)
                    left = (width - size) // 2
                    top = (height - size) // 2
                    img = img.crop((left, top, left + size, top + size))
                    img = img.resize((96, 96), Image.Resampling.LANCZOS)
                
                # Sauvegarder en JPEG avec qualité optimisée
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='JPEG', quality=75, optimize=True)
                img_buffer.seek(0)
                
                photo_data = img_buffer.getvalue()
                photo_base64 = base64.b64encode(photo_data).decode('utf-8')
                
                # Limite plus stricte pour la compatibilité
                if len(photo_base64) > 2000:  # Limite augmentée mais raisonnable
                    print(f"⚠️  Photo trop volumineuse pour le QR code ({len(photo_base64)} caractères)")
                    print("   Pour une meilleure compatibilité, utilisez une image plus petite")
                    print("   La photo sera affichée sur l'image mais pas dans le QR code")
                else:
                    # Format vCard 3.0 standard pour la photo
                    vcard += f"\nPHOTO;ENCODING=b;TYPE=JPEG:{photo_base64}"
                    print(f"✅ Photo ajoutée au QR code ({len(photo_base64)} caractères)")
                    print("📱 Note: La compatibilité des photos varie selon les applications")
                
        except Exception as e:
            print(f"⚠️  Impossible d'encoder la photo dans le QR code: {e}")
            print("   La photo sera affichée sur l'image mais pas dans le QR code")
    
    vcard += "\nEND:VCARD"
    return vcard

def apply_qr_style(qr_img, style="rounded", qr_color="black", qr_background="white"):
    """
    Applique un style personnalisé au QR code
    """
    if style == "square":
        return qr_img
    
    # Convertir en mode RGBA pour les manipulations
    if qr_img.mode != 'RGBA':
        qr_img = qr_img.convert('RGBA')
    
    width, height = qr_img.size
    
    if style == "rounded":
        # Créer un QR code avec coins arrondis
        mask = Image.new('L', (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)
        
        # Coins arrondis pour l'ensemble
        corner_radius = min(width, height) // 20
        mask_draw.rounded_rectangle(
            [0, 0, width-1, height-1], 
            radius=corner_radius, 
            fill=255
        )
        
        # Appliquer le masque
        qr_styled = Image.new('RGBA', (width, height), (*ImageColor.getrgb(qr_background), 255))
        qr_styled.paste(qr_img, (0, 0))
        qr_styled.putalpha(mask)
        
        return qr_styled
    
    elif style == "dots":
        # Effet pointillé (simplifié)
        return qr_img
    
    elif style == "gradient":
        # Effet dégradé (simplifié)
        return qr_img
    
    return qr_img

def get_font_with_style(base_font_path, size, bold=False, italic=False):
    """
    Tente de charger une police avec le style demandé (gras, italique)
    """
    font_variations = []
    
    # Essayer différentes polices selon le style
    if bold and italic:
        font_variations = [
            "arialbi.ttf",  # Arial Bold Italic
            "/System/Library/Fonts/Arial Bold Italic.ttf",
            "/System/Library/Fonts/Helvetica Bold Oblique.ttc",
            "times.ttf"
        ]
    elif bold:
        font_variations = [
            "arialbd.ttf",  # Arial Bold
            "/System/Library/Fonts/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica Bold.ttc",
            "timesbd.ttf"
        ]
    elif italic:
        font_variations = [
            "ariali.ttf",  # Arial Italic
            "/System/Library/Fonts/Arial Italic.ttf",
            "/System/Library/Fonts/Helvetica Oblique.ttc",
            "timesi.ttf"
        ]
    else:
        font_variations = [
            "arial.ttf",
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "times.ttf"
        ]
    
    # Essayer de charger les polices
    for font_path in font_variations:
        try:
            return ImageFont.truetype(font_path, size)
        except:
            continue
    
    # Fallback vers la police par défaut
    print(f"⚠️  Impossible de charger la police avec le style demandé, utilisation de la police par défaut")
    return ImageFont.load_default()

def draw_text_with_effects(draw, text, position, font, color, underline=False, background_color="white"):
    """
    Dessine du texte avec des effets optionnels (souligné)
    """
    x, y = position
    
    # Dessiner le texte
    draw.text((x, y), text, fill=color, font=font)
    
    # Ajouter un soulignement si demandé
    if underline:
        # Calculer les dimensions du texte
        bbox = draw.textbbox((x, y), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Dessiner la ligne de soulignement
        underline_y = y + text_height + 2
        draw.line([(x, underline_y), (x + text_width, underline_y)], fill=color, width=2)

def generate_qr_contact_image(
    name,
    phone="",
    email="",
    organization="",
    url="",
    title="Mon Contact",
    description="Scannez ce QR code pour ajouter mes informations de contact",
    output_filename="contact_qr.png",
    qr_color="black",
    qr_background="white",
    background_color="white",
    title_color="black",
    description_color="gray",
    profile_image_path=None,
    title_font_size=24,
    description_font_size=16,
    qr_style="rounded",
    include_photo_in_qr=False,
    # NOUVELLES OPTIONS DE FORMATAGE
    title_bold=False,
    title_italic=False,
    title_underline=False,
    description_bold=False,
    description_italic=False,
    description_underline=False
):
    """
    Génère une image complète avec titre, description et QR code de contact
    Nouvelles options de formatage pour le titre et la description
    """
    
    print(f"Génération du QR code pour: {name}")
    
    # Afficher les options de formatage
    title_styles = []
    if title_bold: title_styles.append("gras")
    if title_italic: title_styles.append("italique")
    if title_underline: title_styles.append("souligné")
    
    desc_styles = []
    if description_bold: desc_styles.append("gras")
    if description_italic: desc_styles.append("italique")
    if description_underline: desc_styles.append("souligné")
    
    if title_styles:
        print(f"🎨 Style du titre: {', '.join(title_styles)}")
    if desc_styles:
        print(f"🎨 Style de la description: {', '.join(desc_styles)}")
    
    # Créer la vCard
    vcard_data = create_vcard(
        name, phone, email, organization, url, 
        include_photo_in_qr=include_photo_in_qr,
        photo_path=profile_image_path
    )
    
    print(f"Taille des données vCard: {len(vcard_data)} caractères")
    
    # Générer le QR code avec gestion d'erreur améliorée
    try:
        qr = qrcode.QRCode(
            version=1,  # Commencer avec la version 1
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=4,
        )
        qr.add_data(vcard_data)
        
        # Essayer de générer avec fit=True
        try:
            qr.make(fit=True)
        except ValueError as e:
            if "Invalid version" in str(e):
                print("⚠️  Données trop volumineuses pour un QR code standard")
                print("   Génération sans photo dans le QR code...")
                
                # Recréer la vCard sans photo
                vcard_data = create_vcard(
                    name, phone, email, organization, url, 
                    include_photo_in_qr=False,
                    photo_path=None
                )
                
                # Recréer le QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_M,
                    box_size=8,
                    border=4,
                )
                qr.add_data(vcard_data)
                qr.make(fit=True)
            else:
                raise e
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du QR code: {e}")
        return None
    
    # Créer l'image du QR code
    qr_img = qr.make_image(fill_color=qr_color, back_color=qr_background)
    
    # Appliquer le style si demandé
    if qr_style != "square":
        qr_img = apply_qr_style(qr_img, qr_style, qr_color, qr_background)
    
    qr_size = qr_img.size[0]
    
    # Dimensions de l'image finale
    padding = 50
    title_height = 80
    desc_height = 60
    spacing = 30
    profile_size = 120
    profile_spacing = 20
    
    # Calculer les dimensions
    has_profile = profile_image_path is not None and os.path.exists(profile_image_path)
    extra_height = (profile_size + profile_spacing) if has_profile else 0
    
    # Ajouter de l'espace pour les soulignements
    title_underline_space = 10 if title_underline else 0
    desc_underline_space = 10 if description_underline else 0
    
    total_width = max(qr_size + (padding * 2), profile_size + (padding * 2), 400)
    total_height = qr_size + title_height + desc_height + (spacing * 2) + (padding * 2) + extra_height + title_underline_space + desc_underline_space
    
    # Créer l'image finale
    final_img = Image.new('RGB', (total_width, total_height), background_color)
    draw = ImageDraw.Draw(final_img)
    
    # Charger les polices avec les styles appropriés
    title_font = get_font_with_style("arial.ttf", title_font_size, title_bold, title_italic)
    desc_font = get_font_with_style("arial.ttf", description_font_size, description_bold, description_italic)
    
    current_y = padding
    
    # Afficher la photo de profil si fournie
    if has_profile:
        try:
            profile_img = Image.open(profile_image_path)
            
            # Redimensionner en gardant les proportions et en remplissant tout l'espace
            # Calculer le ratio pour remplir complètement le cercle
            img_width, img_height = profile_img.size
            ratio = max(profile_size / img_width, profile_size / img_height)
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            
            # Redimensionner l'image
            profile_img = profile_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Créer une image carrée et centrer la photo redimensionnée
            square_img = Image.new('RGB', (profile_size, profile_size), background_color)
            
            # Centrer l'image (crop si nécessaire)
            x_offset = (profile_size - new_width) // 2
            y_offset = (profile_size - new_height) // 2
            
            # Si l'image est plus grande que le carré, on la recadre
            if new_width > profile_size or new_height > profile_size:
                left = max(0, (new_width - profile_size) // 2)
                top = max(0, (new_height - profile_size) // 2)
                right = left + profile_size
                bottom = top + profile_size
                profile_img = profile_img.crop((left, top, right, bottom))
                x_offset = 0
                y_offset = 0
            
            square_img.paste(profile_img, (x_offset, y_offset))
            
            # Créer le masque circulaire
            mask = Image.new('L', (profile_size, profile_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, profile_size, profile_size), fill=255)
            
            # Appliquer le masque circulaire
            square_img.putalpha(mask)
            
            # Positionner la photo
            profile_x = (total_width - profile_size) // 2
            profile_y = current_y
            
            # Créer une image temporaire avec le fond pour bien coller la photo avec transparence
            temp_img = Image.new('RGB', (profile_size, profile_size), background_color)
            if square_img.mode == 'RGBA':
                temp_img.paste(square_img, (0, 0), square_img)
            else:
                temp_img.paste(square_img, (0, 0))
            
            # Coller la photo circulaire
            final_img.paste(temp_img, (profile_x, profile_y))
            
            # Optionnel : Dessiner un cercle de bordure pour un effet plus net
            circle_draw = ImageDraw.Draw(final_img)
            circle_draw.ellipse(
                [profile_x-1, profile_y-1, profile_x + profile_size+1, profile_y + profile_size+1],
                outline=title_color, width=2
            )
            
            current_y += profile_size + profile_spacing
            
        except Exception as e:
            print(f"⚠️  Erreur lors du chargement de la photo: {e}")
    
    # Dessiner le titre avec effets
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (total_width - title_width) // 2
    draw_text_with_effects(draw, title, (title_x, current_y), title_font, title_color, title_underline, background_color)
    current_y += title_height + title_underline_space
    
    # Dessiner la description avec effets
    desc_bbox = draw.textbbox((0, 0), description, font=desc_font)
    desc_width = desc_bbox[2] - desc_bbox[0]
    desc_x = (total_width - desc_width) // 2
    draw_text_with_effects(draw, description, (desc_x, current_y), desc_font, description_color, description_underline, background_color)
    current_y += desc_height + spacing + desc_underline_space
    
    # Coller le QR code
    qr_x = (total_width - qr_size) // 2
    qr_y = current_y
    
    # Convertir le QR code au bon format si nécessaire
    if qr_img.mode == 'RGBA':
        qr_with_bg = Image.new('RGB', qr_img.size, qr_background)
        qr_with_bg.paste(qr_img, (0, 0), qr_img)
        qr_img = qr_with_bg
    elif qr_img.mode != 'RGB':
        qr_img = qr_img.convert('RGB')
    
    final_img.paste(qr_img, (qr_x, qr_y))
    
    # Sauvegarder l'image
    final_img.save(output_filename, 'PNG', quality=95)
    print(f"✅ Image sauvegardée: {output_filename}")
    
    return final_img

def main():
    """
    Fonction principale - configurez vos informations ici
    """
    
    # ========== CONFIGUREZ VOS INFORMATIONS ICI ==========
    contact_info = {
        'name': 'Gaétan DUMAS',
        'phone': '+33 6 33 38 17 90',
        'email': 'gaetan.dumas.3d@gmail.com',
        'organization': 'Technial Artist - 3D Generalist',
        'url': 'https://linktr.ee/g144hz'
    }
    
    image_config = {
        'title': 'Gaétan DUMAS',
        'description': 'Technical Artist - 3D Generalist',
        'output_filename': 'mon_contact_qr.png',
        # ===== PHOTO DE PROFIL =====
        'profile_image_path': r'C:\Users\gaeta\Documents\Repos\Portfolio_QRCode\Kodim17_noisy.jpg',
        'include_photo_in_qr': True,  # NOUVEAU: Contrôle si la photo est dans le QR code
        # ===== TAILLES DE POLICE =====
        'title_font_size': 32,
        'description_font_size': 28,
        # ===== STYLE DU QR CODE =====
        'qr_style': 'dots',
        # ===== COULEURS =====
        'qr_color': 'green',
        'qr_background': 'white',
        'background_color': 'white',
        'title_color': 'green',
        'description_color': 'green',
        # ===== NOUVELLES OPTIONS DE FORMATAGE DE TEXTE =====
        'title_bold': True,          # Titre en gras
        'title_italic': False,       # Titre en italique
        'title_underline': False,     # Titre souligné
        'description_bold': False,   # Description en gras
        'description_italic': True,  # Description en italique
        'description_underline': False  # Description soulignée
    }
    # =====================================================
    
    print("🔄 Génération du QR code de contact...")
    print(f"📇 Nom: {contact_info['name']}")
    print(f"📞 Téléphone: {contact_info['phone']}")
    print(f"📧 Email: {contact_info['email']}")
    print(f"🏢 Organisation: {contact_info['organization']}")
    print(f"🌐 Site web: {contact_info['url']}")
    
    # Vérifier la photo
    profile_path = image_config.get('profile_image_path')
    if profile_path and os.path.exists(profile_path):
        print(f"📷 Photo de profil: {profile_path}")
        if image_config.get('include_photo_in_qr'):
            print("   ⚠️  Photo sera incluse dans le QR code (peut augmenter la complexité)")
        else:
            print("   ℹ️  Photo sera affichée sur l'image uniquement")
    else:
        print("📷 Aucune photo de profil valide")
    
    print("-" * 60)
    
    # Générer l'image
    result = generate_qr_contact_image(
        **contact_info,
        **image_config
    )
    
    if result:
        print("\n✅ QR code généré avec succès !")
        print("📱 Fonctionnalités du QR code :")
        print("   • Ajoute automatiquement le contact")
        print("   • Inclut toutes les informations de contact")
        print("   • Compatible avec tous les smartphones")
        print("   • Formatage personnalisé du texte (gras, italique, souligné)")
        
        if image_config.get('include_photo_in_qr'):
            print("\n📷 À propos de la photo dans les contacts :")
            print("   ⚠️  La photo peut ne pas s'afficher selon l'application :")
            print("       • iPhone/iOS : Généralement supporté")
            print("       • Android : Varie selon la version et l'app")
            print("       • WhatsApp, Gmail : Support limité")
            print("   💡 Solutions alternatives :")
            print("       • Ajouter manuellement la photo après import")
            print("       • Utiliser un format d'image plus petit")
            print("       • Tester avec différentes apps de contacts")
        
        print("\n🎨 Options de formatage ajoutées :")
        print("   • title_bold: Met le titre en gras")
        print("   • title_italic: Met le titre en italique")
        print("   • title_underline: Souligne le titre")
        print("   • description_bold: Met la description en gras")
        print("   • description_italic: Met la description en italique")
        print("   • description_underline: Souligne la description")
        
        print("\n💡 Conseils d'utilisation :")
        print("   • Testez le QR code avec votre téléphone")
        print("   • Partagez l'image sur vos réseaux sociaux")
        print("   • Imprimez-la sur vos cartes de visite")
        print("   • Combinez les effets pour un style unique")
        print("   • Si la police stylée ne charge pas, la police par défaut sera utilisée")
    else:
        print("❌ Échec de la génération du QR code")

if __name__ == "__main__":
    # Vérifier les dépendances
    try:
        import qrcode
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as e:
        print("❌ Dépendances manquantes !")
        print("Installez les packages requis avec :")
        print("pip install qrcode[pil] pillow")
        exit(1)
    
    main()