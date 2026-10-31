const install = document.querySelector("#install");
const installExtension = document.querySelector("#install-extension");
const extensionStatus = document.querySelector("#extension-status");
const copy = document.querySelector("#copy");
const code = document.querySelector("#code");
const status = document.querySelector("#status");

async function loadPermanentExtension() {
  const response = await fetch("release.json", {cache: "no-store"});
  if (!response.ok) {
    throw new Error("The permanent Firefox package is not published yet.");
  }
  const release = await response.json();
  if (
    release.file !== "neo-picker-firefox.xpi"
    || typeof release.version !== "string"
    || !release.version
  ) {
    throw new Error("The permanent Firefox release metadata is invalid.");
  }
  installExtension.href = release.file;
  installExtension.removeAttribute("aria-disabled");
  extensionStatus.textContent = `Mozilla-signed release ${release.version}`;
}

async function loadBookmarklet() {
  const response = await fetch("bookmarklet.js", {cache: "no-store"});
  if (!response.ok) {
    throw new Error(`Could not load the bookmark code: HTTP ${response.status}`);
  }
  const value = (await response.text()).trim();
  if (!value.startsWith("javascript:")) {
    throw new Error("The published bookmark code is invalid.");
  }
  install.href = value;
  code.value = value;
  install.removeAttribute("aria-disabled");
  copy.disabled = false;
}

async function copyBookmarklet() {
  try {
    await navigator.clipboard.writeText(code.value);
  } catch {
    code.hidden = false;
    code.select();
    if (!document.execCommand("copy")) {
      throw new Error("Copy the selected bookmark code manually.");
    }
  }
  status.textContent = "Bookmark code copied.";
}

copy.addEventListener("click", () => {
  copyBookmarklet().catch((error) => {
    status.textContent = error.message;
  });
});

loadBookmarklet().catch((error) => {
  status.textContent = error.message;
});

loadPermanentExtension().catch((error) => {
  extensionStatus.textContent = error.message;
});
