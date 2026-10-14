/*
 * Construction de la vCard et composition de l'image finale
 * (photo, titre, description, QR code).
 * Tout est calcule dans le navigateur, aucune donnee n'est envoyee.
 */
(function (global) {
  "use strict";

  // Les accents (é, ç...) doivent etre encodes en UTF-8 dans le QR code.
  qrcode.stringToBytes = qrcode.stringToBytesFuncs["UTF-8"];

  // Couleurs et tailles de police de l'image generee.
  const CONFIG = {
    backgroundColor: "#ffffff",
    qrBackground: "#ffffff",
    titleFontSize: 32,
    descriptionFontSize: 28,
    minFontSize: 12,
    fontFamily: 'Arial, "Helvetica Neue", Helvetica, sans-serif',
  };

  // Mise en page de l'image, en pixels (avant mise a l'echelle).
  const LAYOUT = {
    padding: 50,
    titleHeight: 80,
    descHeight: 60,
    spacing: 30,
    profileSize: 120,
    profileSpacing: 20,
    minWidth: 400,
    boxSize: 8,
    border: 4,
  };

  // Photo integree a la vCard : au-dela de cette taille elle n'est pas
  // integree, sinon le QR code devient trop dense pour etre scanne.
  const VCARD_PHOTO = {
    maxBase64Length: 2000,
    sizes: [96, 72, 64, 48],
    qualities: [0.75, 0.6, 0.45, 0.3],
  };

  function escapeText(value) {
    return value.replace(/\\/g, "\\\\").replace(/\r?\n/g, "\\n").replace(/([,;])/g, "\\$1");
  }

  function buildVCard(contact, photoBase64) {
    const lines = ["BEGIN:VCARD", "VERSION:3.0", "FN:" + escapeText(contact.name)];

    if (contact.phone) lines.push("TEL;TYPE=CELL:" + contact.phone);
    if (contact.email) lines.push("EMAIL;TYPE=INTERNET:" + contact.email);
    if (contact.url) lines.push("URL:" + contact.url);
    if (photoBase64) lines.push("PHOTO;ENCODING=b;TYPE=JPEG:" + photoBase64);

    lines.push("END:VCARD");
    return lines.join("\n");
  }

  // Recadre la photo au centre en carre puis cherche la plus grande taille et
  // la meilleure qualite JPEG qui tiennent dans la limite de la vCard.
  function encodeVCardPhoto(image) {
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    const side = Math.min(image.naturalWidth, image.naturalHeight);
    const sx = (image.naturalWidth - side) / 2;
    const sy = (image.naturalHeight - side) / 2;

    for (const size of VCARD_PHOTO.sizes) {
      canvas.width = size;
      canvas.height = size;
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, size, size);
      ctx.imageSmoothingQuality = "high";
      ctx.drawImage(image, sx, sy, side, side, 0, 0, size, size);

      for (const quality of VCARD_PHOTO.qualities) {
        const data = canvas.toDataURL("image/jpeg", quality).split(",")[1];
        if (data.length <= VCARD_PHOTO.maxBase64Length) {
          return { data: data, size: size };
        }
      }
    }
    return null;
  }

  function createQr(data) {
    const qr = qrcode(0, "M");
    qr.addData(data, "Byte");
    qr.make();
    return qr;
  }

  function font(size) {
    return size + "px " + CONFIG.fontFamily;
  }

  function roundedRectPath(ctx, x, y, width, height, radius) {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.arcTo(x + width, y, x + width, y + height, radius);
    ctx.arcTo(x + width, y + height, x, y + height, radius);
    ctx.arcTo(x, y + height, x, y, radius);
    ctx.arcTo(x, y, x + width, y, radius);
    ctx.closePath();
  }

  function drawProfilePhoto(ctx, image, x, y, outlineColor) {
    const size = LAYOUT.profileSize;
    const ratio = Math.max(size / image.naturalWidth, size / image.naturalHeight);
    const drawWidth = image.naturalWidth * ratio;
    const drawHeight = image.naturalHeight * ratio;
    const center = size / 2;

    ctx.save();
    ctx.beginPath();
    ctx.arc(x + center, y + center, center, 0, Math.PI * 2);
    ctx.clip();
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(image, x + (size - drawWidth) / 2, y + (size - drawHeight) / 2, drawWidth, drawHeight);
    ctx.restore();

    ctx.beginPath();
    ctx.arc(x + center, y + center, center + 1, 0, Math.PI * 2);
    ctx.lineWidth = 2;
    ctx.strokeStyle = outlineColor;
    ctx.stroke();
  }

  // Le texte trop long est reduit pour rester dans l'image.
  function drawCenteredText(ctx, text, y, fontSize, color, width) {
    const maxWidth = width - LAYOUT.padding * 2;
    let size = fontSize;
    ctx.font = font(size);
    while (size > CONFIG.minFontSize && ctx.measureText(text).width > maxWidth) {
      size -= 1;
      ctx.font = font(size);
    }

    ctx.fillStyle = color;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillText(text, width / 2, y, maxWidth);
  }

  // QR code avec coins arrondis sur son bloc (marge comprise).
  function drawQr(ctx, qr, x, y, size, color) {
    const box = LAYOUT.boxSize;
    const offset = LAYOUT.border * box;
    const count = qr.getModuleCount();

    ctx.save();
    roundedRectPath(ctx, x, y, size, size, Math.floor(size / 20));
    ctx.clip();
    ctx.fillStyle = CONFIG.qrBackground;
    ctx.fillRect(x, y, size, size);

    ctx.fillStyle = color;
    for (let row = 0; row < count; row += 1) {
      for (let col = 0; col < count; col += 1) {
        if (qr.isDark(row, col)) {
          ctx.fillRect(x + offset + col * box, y + offset + row * box, box, box);
        }
      }
    }
    ctx.restore();
  }

  /*
   * Dessine la carte complete dans le canvas. Leve une erreur si les donnees
   * depassent la capacite d'un QR code.
   * options : { vcard, title, description, color, photo, scale }
   */
  function renderCard(canvas, options) {
    const qr = createQr(options.vcard);
    const qrSize = (qr.getModuleCount() + LAYOUT.border * 2) * LAYOUT.boxSize;
    const hasProfile = Boolean(options.photo);
    const extraHeight = hasProfile ? LAYOUT.profileSize + LAYOUT.profileSpacing : 0;

    const width = Math.max(qrSize + LAYOUT.padding * 2, LAYOUT.minWidth);
    const height =
      qrSize + LAYOUT.titleHeight + LAYOUT.descHeight + LAYOUT.spacing * 2 + LAYOUT.padding * 2 + extraHeight;
    const scale = options.scale || 1;

    canvas.width = width * scale;
    canvas.height = height * scale;
    const ctx = canvas.getContext("2d");
    ctx.setTransform(scale, 0, 0, scale, 0, 0);
    ctx.fillStyle = CONFIG.backgroundColor;
    ctx.fillRect(0, 0, width, height);

    let y = LAYOUT.padding;
    if (hasProfile) {
      drawProfilePhoto(ctx, options.photo, Math.floor((width - LAYOUT.profileSize) / 2), y, options.color);
      y += LAYOUT.profileSize + LAYOUT.profileSpacing;
    }

    drawCenteredText(ctx, options.title, y, CONFIG.titleFontSize, options.color, width);
    y += LAYOUT.titleHeight;

    drawCenteredText(ctx, options.description, y, CONFIG.descriptionFontSize, options.color, width);
    y += LAYOUT.descHeight + LAYOUT.spacing;

    drawQr(ctx, qr, Math.floor((width - qrSize) / 2), y, qrSize, options.color);

    return { width: width, height: height, moduleCount: qr.getModuleCount() };
  }

  global.QRContact = {
    buildVCard: buildVCard,
    encodeVCardPhoto: encodeVCardPhoto,
    renderCard: renderCard,
  };
})(window);
