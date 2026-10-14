# Générateur de QR Code Contact

**🌐 Site en ligne : [contact-qr-app-lovat.vercel.app](https://contact-qr-app-lovat.vercel.app/)**
· Code source : [github.com/gaetan144hz/Contact_QRCode_App](https://github.com/gaetan144hz/Contact_QRCode_App)

Site web qui crée un QR code de contact : une fois scanné avec un téléphone, il propose d'ajouter vos coordonnées au carnet d'adresses.

L'image générée contient une photo de profil (facultative), un titre, une description et le QR code, dans la couleur de votre choix. Elle se télécharge en PNG ou en JPEG.

> [!NOTE]
> Tout est calculé dans le navigateur : aucune donnée n'est envoyée à un serveur.

## Fonctionnalités

- **Contact** : nom (obligatoire), téléphone, email, site web, encodés au format vCard 3.0
- **Personnalisation** : titre, description, photo de profil ronde (par glisser-déposer ou parcourir), couleur choisie parmi des pastilles ou personnalisée
- **Photo dans le QR code** (option) : la photo est compressée pour tenir dans le QR code, qui devient alors plus dense
- **Aperçu en direct** pendant la saisie, avec un indicateur de densité du QR code
- **Export** en PNG ou JPEG, en double résolution pour l'impression, copie dans le presse-papiers et partage sur mobile (selon le navigateur)
- **Thème clair ou sombre**, interface adaptée au mobile, animations désactivées si le système le demande
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

Il est hébergé sur Vercel, qui le republie automatiquement à chaque push sur `main`. `vercel.json` publie le dossier `web/` sans commande de build et ajoute quelques en-têtes de sécurité.

## Structure

```
web/
├── index.html         page, formulaire et icônes
├── css/style.css      styles (clair et sombre, adapté au mobile, animations)
├── js/generator.js    vCard et dessin de l'image
├── js/app.js          interface : formulaire, aperçu, export, thème
├── vendor/qrcode.js   encodage du QR code
├── fonts/             police Plus Jakarta Sans
└── favicon.svg
```

## Crédits

- Encodage du QR code : [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) 2.0.4 de Kazuhiko Arase (licence MIT), copié dans `web/vendor/`
- Police : [Plus Jakarta Sans](https://github.com/tokotype/PlusJakartaSans) (licence SIL Open Font License 1.1, voir `web/fonts/OFL.txt`), hébergée avec le site
