/*
 * Interface : formulaire, apercu en direct, telechargement, copie, partage
 * et petites animations.
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
  // Regroupe les modifications rapides (frappe au clavier) en un seul rendu.
  const RENDER_DELAY_MS = 50;
  const TOAST_DURATION_MS = 2600;
  const TOAST_EXIT_MS = 250;
  const MAX_TOASTS = 3;
  const MAX_TILT_DEG = 7;

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
  const dropzone = $("dropzone");
  const photoInput = $("photo");
  const photoThumb = $("photo-thumb");
  const photoIcon = $("photo-icon");
  const photoTitle = $("photo-title");
  const photoSubtitle = $("photo-subtitle");
  const photoClear = $("photo-clear");
  const includePhoto = $("include-photo");
  const presetInputs = Array.from(document.querySelectorAll('input[name="color-preset"]'));
  const customSwatch = $("custom-swatch");
  const colorPicker = $("color");
  const colorHex = $("color-hex");
  const colorWarning = $("color-warning");
  const previewColumn = $("preview-column");
  const stage = $("stage");
  const tilt = $("tilt");
  const canvas = $("qr-canvas");
  const placeholder = $("preview-placeholder");
  const placeholderText = $("placeholder-text");
  const meta = $("qr-meta");
  const density = $("density");
  const metaText = $("meta-text");
  const status = $("status");
  const downloadPng = $("download-png");
  const downloadJpg = $("download-jpg");
  const copyButton = $("copy-image");
  const shareButton = $("share-image");
  const mobileBar = $("mobile-bar");
  const mobilePreview = $("mobile-preview");
  const mobileDownload = $("mobile-download");
  const themeToggle = $("theme-toggle");
  const toasts = $("toasts");

  const resultButtons = [downloadPng, downloadJpg, copyButton, shareButton];

  const state = {
    color: DEFAULT_COLOR,
    photo: null,
    photoName: "",
    vcardPhoto: null,
    hasResult: false,
    previewVisible: true,
  };

  // --- Notifications -------------------------------------------------------

  function toast(message, tone) {
    const element = document.createElement("div");
    element.className = "toast";
    if (tone) element.dataset.tone = tone;
    element.innerHTML = '<svg class="icon"><use href="#i-' + (tone === "error" ? "alert" : "check") + '" /></svg>';
    element.append(message);
    toasts.append(element);

    while (toasts.children.length > MAX_TOASTS) toasts.firstElementChild.remove();

    // Retrait par minuteur plutot que sur animationend, qui ne se declenche
    // pas tant que l'onglet est en arriere-plan.
    setTimeout(() => {
      element.classList.add("is-leaving");
      setTimeout(() => element.remove(), TOAST_EXIT_MS);
    }, TOAST_DURATION_MS);
  }

  function replayAnimation(element, className) {
    element.classList.remove(className);
    void element.offsetWidth;
    element.classList.add(className);
    element.addEventListener("animationend", () => element.classList.remove(className), { once: true });
  }

  // --- Rendu -----------------------------------------------------------------

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
    meta.hidden = !available;
    resultButtons.forEach((button) => {
      button.disabled = !available;
    });
    updateMobileBar();
  }

  function showEmpty(message) {
    placeholderText.textContent = message;
    setResultAvailable(false);
    setStatus("");
  }

  function updateMeta(moduleCount) {
    const version = (moduleCount - 17) / 4;
    let level = "low";
    let label = "Lecture facile";
    if (version > 25) {
      level = "high";
      label = "QR code très dense";
    } else if (version > 10) {
      level = "medium";
      label = "Densité moyenne";
    }
    density.dataset.level = level;
    density.textContent = label;
    metaText.textContent = "Version " + version + " · " + moduleCount + " × " + moduleCount + " modules";
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
        "Testez le scan avant d'imprimer.",
    };
  }

  function render() {
    const name = fields.name.value.trim();
    if (!name) {
      showEmpty("Saisissez votre nom pour faire apparaître votre carte.");
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

    let result;
    try {
      result = QRContact.renderCard(canvas, {
        vcard: vcard,
        title: fields.title.value.trim() || DEFAULT_TITLE,
        description: fields.description.value.trim() || DEFAULT_DESCRIPTION,
        color: state.color,
        photo: state.photo,
        scale: EXPORT_SCALE,
      });
    } catch (err) {
      showEmpty("Trop de données pour un seul QR code. Désactivez l'intégration de la photo ou raccourcissez certains champs.");
      return;
    }

    const firstAppearance = !state.hasResult;
    canvas.setAttribute("aria-label", "QR code de contact pour " + name);
    setResultAvailable(true);
    if (firstAppearance) replayAnimation(canvas, "is-new");
    updateMeta(result.moduleCount);

    const info = photoStatus();
    setStatus(info ? info.message : "", info ? info.tone : "");
  }

  // --- Photo de profil -------------------------------------------------------

  function updatePhotoUi() {
    const hasPhoto = Boolean(state.photo);
    dropzone.classList.toggle("has-photo", hasPhoto);
    photoThumb.hidden = !hasPhoto;
    photoIcon.toggleAttribute("hidden", hasPhoto);
    photoClear.hidden = !hasPhoto;
    includePhoto.disabled = !hasPhoto;
    if (!hasPhoto) includePhoto.checked = false;

    if (hasPhoto) {
      photoThumb.src = state.photo.src;
      photoTitle.textContent = state.photoName;
      photoSubtitle.textContent = "Cliquez ou glissez une autre image pour la remplacer";
    } else {
      photoThumb.removeAttribute("src");
      photoTitle.textContent = "Glissez une photo ici";
      photoSubtitle.textContent = "ou cliquez pour parcourir · PNG, JPEG, WebP";
    }
  }

  function rejectPhoto() {
    photoInput.value = "";
    toast("Impossible de lire cette image", "error");
  }

  // Lecture en data: URL plutot qu'en blob: pour que le canvas reste
  // exportable meme quand la page est ouverte directement depuis le disque.
  function loadPhoto(file) {
    if (file.type && !file.type.startsWith("image/")) {
      rejectPhoto();
      return;
    }
    const reader = new FileReader();
    reader.onerror = rejectPhoto;
    reader.onload = () => {
      const image = new Image();
      image.onload = () => {
        state.photo = image;
        state.photoName = file.name;
        state.vcardPhoto = QRContact.encodeVCardPhoto(image);
        updatePhotoUi();
        scheduleRender();
      };
      image.onerror = rejectPhoto;
      image.src = reader.result;
    };
    reader.readAsDataURL(file);
  }

  photoInput.addEventListener("change", () => {
    const file = photoInput.files && photoInput.files[0];
    if (file) loadPhoto(file);
  });

  photoClear.addEventListener("click", () => {
    state.photo = null;
    state.photoName = "";
    state.vcardPhoto = null;
    photoInput.value = "";
    updatePhotoUi();
    photoInput.focus();
    scheduleRender();
  });

  // Une image peut etre deposee n'importe ou sur la page.
  let dragDepth = 0;
  const isFileDrag = (event) => Boolean(event.dataTransfer) && Array.from(event.dataTransfer.types).includes("Files");

  window.addEventListener("dragenter", (event) => {
    if (!isFileDrag(event)) return;
    dragDepth += 1;
    dropzone.classList.add("is-dragging");
  });

  window.addEventListener("dragleave", (event) => {
    if (!isFileDrag(event)) return;
    dragDepth = Math.max(0, dragDepth - 1);
    if (dragDepth === 0) dropzone.classList.remove("is-dragging");
  });

  window.addEventListener("dragover", (event) => {
    if (isFileDrag(event)) event.preventDefault();
  });

  window.addEventListener("drop", (event) => {
    if (!isFileDrag(event)) return;
    event.preventDefault();
    dragDepth = 0;
    dropzone.classList.remove("is-dragging");
    const file = Array.from(event.dataTransfer.files).find((item) => item.type.startsWith("image/"));
    if (file) loadPhoto(file);
    else toast("Déposez un fichier image (PNG, JPEG, WebP…)", "error");
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

  function setColor(hex, fromHexInput) {
    state.color = hex;

    let isPreset = false;
    presetInputs.forEach((input) => {
      input.checked = input.value === hex;
      isPreset = isPreset || input.checked;
    });
    customSwatch.classList.toggle("is-active", !isPreset);
    customSwatch.style.setProperty("--swatch", hex);
    colorPicker.value = hex;
    if (!fromHexInput) {
      colorHex.value = hex.slice(1);
      colorHex.removeAttribute("aria-invalid");
    }

    colorWarning.hidden = contrastWithWhite(hex) >= MIN_CONTRAST;
    scheduleRender();
  }

  presetInputs.forEach((input) => {
    input.addEventListener("change", () => {
      if (input.checked) setColor(input.value);
    });
  });

  colorPicker.addEventListener("input", () => setColor(colorPicker.value));

  colorHex.addEventListener("input", () => {
    const hex = normalizeHex(colorHex.value);
    if (hex) {
      colorHex.removeAttribute("aria-invalid");
      setColor(hex, true);
    } else {
      colorHex.setAttribute("aria-invalid", "true");
    }
  });

  colorHex.addEventListener("blur", () => {
    colorHex.value = state.color.slice(1);
    colorHex.removeAttribute("aria-invalid");
  });

  // --- Formulaire ------------------------------------------------------------

  const colorControls = new Set([colorHex, colorPicker].concat(presetInputs));

  form.addEventListener("input", (event) => {
    if (colorControls.has(event.target)) return;
    scheduleRender();
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    clearTimeout(renderTimer);
    render();
  });

  // --- Export : telechargement, copie, partage --------------------------------

  function fileBaseName() {
    const slug = fields.name.value
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 40);
    return slug ? "qr-" + slug : OUTPUT_FILENAME;
  }

  function canvasBlob(type) {
    return new Promise((resolve, reject) => {
      canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error("Export impossible"))), type, 0.95);
    });
  }

  // Version synchrone : le partage doit partir directement du clic.
  function canvasFile(type, extension) {
    const binary = atob(canvas.toDataURL(type, 0.95).split(",")[1]);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
    return new File([bytes], fileBaseName() + "." + extension, { type: type });
  }

  async function download(type, extension) {
    if (!state.hasResult) return;
    try {
      const blob = await canvasBlob(type);
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = fileBaseName() + "." + extension;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(link.href), 1000);
      toast("Image " + (type === "image/png" ? "PNG" : "JPEG") + " téléchargée");
    } catch (err) {
      toast("Le téléchargement a échoué", "error");
    }
  }

  async function copyImage() {
    if (!state.hasResult) return;
    try {
      await navigator.clipboard.write([new ClipboardItem({ "image/png": canvasBlob("image/png") })]);
      toast("Image copiée dans le presse-papiers");
    } catch (err) {
      toast("Impossible de copier l'image", "error");
    }
  }

  async function shareImage() {
    if (!state.hasResult) return;
    try {
      await navigator.share({ files: [canvasFile("image/png", "png")], title: "Ma carte de contact" });
    } catch (err) {
      if (err && err.name !== "AbortError") toast("Partage impossible", "error");
    }
  }

  const canCopy = Boolean(navigator.clipboard && navigator.clipboard.write && window.ClipboardItem);
  const canShareFiles = (() => {
    try {
      return Boolean(navigator.canShare && navigator.canShare({ files: [new File([""], "test.png", { type: "image/png" })] }));
    } catch (err) {
      return false;
    }
  })();
  copyButton.hidden = !canCopy;
  shareButton.hidden = !canShareFiles;

  // Masque "Copier" si le navigateur refuse explicitement l'acces au presse-papiers.
  if (canCopy && navigator.permissions) {
    navigator.permissions
      .query({ name: "clipboard-write" })
      .then((permission) => {
        if (permission.state === "denied") copyButton.hidden = true;
      })
      .catch(() => {
        // Permission inconnue de ce navigateur (Firefox, Safari) : on garde le bouton.
      });
  }

  downloadPng.addEventListener("click", () => download("image/png", "png"));
  downloadJpg.addEventListener("click", () => download("image/jpeg", "jpg"));
  copyButton.addEventListener("click", copyImage);
  shareButton.addEventListener("click", shareImage);

  // --- Inclinaison 3D de l'apercu --------------------------------------------

  const canTilt =
    window.matchMedia("(hover: hover) and (pointer: fine)").matches &&
    !window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (canTilt) {
    stage.addEventListener("pointermove", (event) => {
      if (!state.hasResult) return;
      const rect = stage.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width - 0.5;
      const y = (event.clientY - rect.top) / rect.height - 0.5;
      tilt.classList.add("is-tilting");
      tilt.style.setProperty("--rx", (-y * MAX_TILT_DEG).toFixed(2) + "deg");
      tilt.style.setProperty("--ry", (x * MAX_TILT_DEG).toFixed(2) + "deg");
    });

    stage.addEventListener("pointerleave", () => {
      tilt.classList.remove("is-tilting");
      tilt.style.setProperty("--rx", "0deg");
      tilt.style.setProperty("--ry", "0deg");
    });
  }

  // --- Barre d'actions mobile -------------------------------------------------

  function updateMobileBar() {
    mobileBar.hidden = !(state.hasResult && !state.previewVisible);
  }

  if ("IntersectionObserver" in window) {
    new IntersectionObserver(
      (entries) => {
        state.previewVisible = entries[0].isIntersecting;
        updateMobileBar();
      },
      { threshold: 0.2 }
    ).observe(previewColumn);
  }

  mobilePreview.addEventListener("click", () => previewColumn.scrollIntoView({ block: "start" }));
  mobileDownload.addEventListener("click", () => download("image/png", "png"));

  // --- Theme clair / sombre ---------------------------------------------------

  const darkQuery = window.matchMedia("(prefers-color-scheme: dark)");

  function effectiveTheme() {
    return document.documentElement.dataset.theme || (darkQuery.matches ? "dark" : "light");
  }

  function updateThemeButton() {
    themeToggle.setAttribute(
      "aria-label",
      effectiveTheme() === "dark" ? "Activer le thème clair" : "Activer le thème sombre"
    );
  }

  themeToggle.addEventListener("click", () => {
    const next = effectiveTheme() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("theme", next);
    } catch (err) {
      // Stockage indisponible (navigation privee) : le choix vaut pour la session.
    }
    updateThemeButton();
  });

  darkQuery.addEventListener("change", updateThemeButton);

  // --- Initialisation ---------------------------------------------------------

  // Le navigateur peut restaurer les champs (retour arriere, rechargement).
  setColor(normalizeHex(colorHex.value) || DEFAULT_COLOR);
  updatePhotoUi();
  updateThemeButton();
})();
