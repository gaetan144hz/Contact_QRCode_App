/*
 * Portage web de qr_contact/ui.py : formulaire, previsualisation en direct
 * et telechargement de l'image.
 */
(function () {
  "use strict";

  const DEFAULT_TITLE = "Mon Contact";
  const DEFAULT_DESCRIPTION = "Scannez ce QR code";
  const DEFAULT_COLOR = "#000000";
  const OUTPUT_FILENAME = "contact_qr";
  // Rendu en double resolution : apercu net sur ecran haute densite et
  // image exportee mieux adaptee a l'impression.
  const EXPORT_SCALE = 2;
  const MIN_CONTRAST = 3;

  const $ = (id) => document.getElementById(id);

  const form = $("contact-form");
  const fields = {
    name: $("name"),
    phone: $("phone"),
    email: $("email"),
    url: $("url"),
    title: $("title"),
    description: $("description"),
  };
  const photoInput = $("photo");
  const photoButton = $("photo-button");
  const photoClear = $("photo-clear");
  const photoName = $("photo-name");
  const includePhoto = $("include-photo");
  const colorPicker = $("color");
  const colorHex = $("color-hex");
  const colorWarning = $("color-warning");
  const canvas = $("qr-canvas");
  const placeholder = $("preview-placeholder");
  const status = $("status");
  const downloadPng = $("download-png");
  const downloadJpg = $("download-jpg");

  const state = {
    color: DEFAULT_COLOR,
    photo: null,
    vcardPhoto: null,
    hasResult: false,
  };

  // Regroupe les modifications rapides (frappe au clavier) en un seul rendu.
  const RENDER_DELAY_MS = 50;
  let renderTimer = null;

  function scheduleRender() {
    clearTimeout(renderTimer);
    renderTimer = setTimeout(render, RENDER_DELAY_MS);
  }

  function setStatus(message, tone) {
    status.textContent = message || "";
    status.dataset.tone = tone || "";
  }

  function setResultAvailable(available) {
    state.hasResult = available;
    canvas.hidden = !available;
    placeholder.hidden = available;
    downloadPng.disabled = !available;
    downloadJpg.disabled = !available;
  }

  function photoStatus() {
    if (!includePhoto.checked || !state.photo) return null;
    if (!state.vcardPhoto) {
      return {
        tone: "warning",
        message: "Photo trop lourde pour être intégrée au QR code : elle reste affichée au-dessus du code.",
      };
    }
    return {
      tone: "info",
      message:
        "Photo intégrée au QR code (" + state.vcardPhoto.size + "×" + state.vcardPhoto.size + " px). " +
        "Le code est plus dense : testez-le avant de l'imprimer.",
    };
  }

  function render() {
    const name = fields.name.value.trim();
    if (!name) {
      placeholder.textContent = "Saisissez au moins un nom pour voir apparaître le QR code.";
      setResultAvailable(false);
      setStatus("");
      return;
    }

    const embedPhoto = includePhoto.checked && state.vcardPhoto;
    const vcard = QRContact.buildVCard(
      {
        name: name,
        phone: fields.phone.value.trim(),
        email: fields.email.value.trim(),
        url: fields.url.value.trim(),
      },
      embedPhoto ? state.vcardPhoto.data : null
    );

    try {
      QRContact.renderCard(canvas, {
        vcard: vcard,
        title: fields.title.value.trim() || DEFAULT_TITLE,
        description: fields.description.value.trim() || DEFAULT_DESCRIPTION,
        color: state.color,
        photo: state.photo,
        scale: EXPORT_SCALE,
      });
    } catch (err) {
      placeholder.textContent =
        "Trop de données pour un seul QR code. Retirez la photo du QR code ou raccourcissez certains champs.";
      setResultAvailable(false);
      setStatus("");
      return;
    }

    canvas.setAttribute("aria-label", "QR code de contact pour " + name);
    setResultAvailable(true);
    const info = photoStatus();
    setStatus(info ? info.message : "", info ? info.tone : "");
  }

  // --- Photo de profil -----------------------------------------------------

  function updatePhotoUi() {
    const hasPhoto = Boolean(state.photo);
    photoClear.hidden = !hasPhoto;
    includePhoto.disabled = !hasPhoto;
    if (!hasPhoto) includePhoto.checked = false;
    photoButton.textContent = hasPhoto ? "Changer" : "Choisir";
  }

  function releasePhoto() {
    state.photo = null;
    state.vcardPhoto = null;
  }

  function rejectPhoto() {
    photoInput.value = "";
    setStatus("Impossible de lire cette image. Choisissez un fichier PNG, JPEG, GIF ou WebP.", "error");
  }

  // Lecture en data: URL plutot qu'en blob: pour que le canvas reste
  // exportable meme quand la page est ouverte directement depuis le disque.
  function loadPhoto(file) {
    const reader = new FileReader();
    reader.onerror = rejectPhoto;
    reader.onload = () => {
      const image = new Image();
      image.onload = () => {
        state.photo = image;
        state.vcardPhoto = QRContact.encodeVCardPhoto(image);
        photoName.textContent = "✓ " + file.name;
        updatePhotoUi();
        scheduleRender();
      };
      image.onerror = rejectPhoto;
      image.src = reader.result;
    };
    reader.readAsDataURL(file);
  }

  photoButton.addEventListener("click", () => photoInput.click());

  photoInput.addEventListener("change", () => {
    const file = photoInput.files && photoInput.files[0];
    if (file) loadPhoto(file);
  });

  photoClear.addEventListener("click", () => {
    releasePhoto();
    photoInput.value = "";
    photoName.textContent = "Aucune photo";
    updatePhotoUi();
    photoButton.focus();
    scheduleRender();
  });

  // --- Couleur ---------------------------------------------------------------

  function normalizeHex(value) {
    const match = /^#?([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(value.trim());
    if (!match) return null;
    let hex = match[1].toLowerCase();
    if (hex.length === 3) hex = hex.replace(/./g, (c) => c + c);
    return "#" + hex;
  }

  function contrastWithWhite(hex) {
    const channels = [1, 3, 5].map((i) => {
      const c = parseInt(hex.slice(i, i + 2), 16) / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    const luminance = 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
    return 1.05 / (luminance + 0.05);
  }

  function setColor(hex) {
    state.color = hex;
    colorPicker.value = hex;
    colorWarning.hidden = contrastWithWhite(hex) >= MIN_CONTRAST;
    scheduleRender();
  }

  colorPicker.addEventListener("input", () => {
    colorHex.value = colorPicker.value;
    colorHex.removeAttribute("aria-invalid");
    setColor(colorPicker.value);
  });

  colorHex.addEventListener("input", () => {
    const hex = normalizeHex(colorHex.value);
    if (hex) {
      colorHex.removeAttribute("aria-invalid");
      setColor(hex);
    } else {
      colorHex.setAttribute("aria-invalid", "true");
    }
  });

  colorHex.addEventListener("blur", () => {
    colorHex.value = state.color;
    colorHex.removeAttribute("aria-invalid");
  });

  // --- Formulaire et telechargement -----------------------------------------

  form.addEventListener("input", (event) => {
    if (event.target === colorHex || event.target === colorPicker) return;
    scheduleRender();
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    render();
  });

  function download(type, extension) {
    if (!state.hasResult) return;
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          setStatus("Le téléchargement a échoué. Réessayez.", "error");
          return;
        }
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = OUTPUT_FILENAME + "." + extension;
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(link.href), 1000);
      },
      type,
      0.95
    );
  }

  downloadPng.addEventListener("click", () => download("image/png", "png"));
  downloadJpg.addEventListener("click", () => download("image/jpeg", "jpg"));

  // Le navigateur peut restaurer les champs (retour arriere, rechargement).
  const restoredColor = normalizeHex(colorHex.value);
  colorHex.value = restoredColor || DEFAULT_COLOR;
  setColor(restoredColor || DEFAULT_COLOR);
  updatePhotoUi();
})();
