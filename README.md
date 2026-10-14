# Générateur de QR Code Contact

Site web qui crée un QR code de contact : une fois scanné avec un téléphone, il propose d'ajouter vos coordonnées au carnet d'adresses.

L'image générée contient une photo de profil (facultative), un titre, une description et le QR code, dans la couleur de votre choix. Elle se télécharge en PNG ou en JPEG.

> [!NOTE]
> Tout est calculé dans le navigateur : aucune donnée n'est envoyée à un serveur.

## Fonctionnalités

- **Contact** : nom (obligatoire), téléphone, email, site web, encodés au format vCard 3.0
- **Personnalisation** : titre, description, photo de profil ronde, couleur du QR code et du texte
- **Photo dans le QR code** (option) : la photo est compressée pour tenir dans le QR code, qui devient alors plus dense
- **Aperçu en direct** pendant la saisie
- **Export** en PNG ou JPEG, en double résolution pour l'impression
- **Avertissement** si la couleur est trop claire pour être scannée de façon fiable

## Lancer le site en local

Aucune installation n'est nécessaire, il suffit d'ouvrir `web/index.html` dans un navigateur.

Pour le servir comme en production, avec n'importe quel serveur de fichiers statiques :

```bash
python -m http.server 8000 --directory web
```

Puis ouvrir http://localhost:8000.

## Mise en ligne

Le site est entièrement statique : le dossier `web/` peut être publié tel quel sur n'importe quel hébergeur (Vercel, GitHub Pages, Netlify, OVH…).

Pour Vercel, `vercel.json` est déjà configuré : il publie le dossier `web/` et ajoute quelques en-têtes de sécurité. Il suffit d'importer le dépôt dans Vercel, sans commande de build.

## Structure

```
web/
├── index.html         page et formulaire
├── css/style.css      styles (clair et sombre, adapté au mobile)
├── js/generator.js    vCard et dessin de l'image
├── js/app.js          interface : formulaire, aperçu, téléchargement
├── vendor/qrcode.js   encodage du QR code
└── favicon.svg
```

## Crédits

L'encodage du QR code repose sur [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) 2.0.4 de Kazuhiko Arase (licence MIT), copié dans `web/vendor/`.
