const install = document.querySelector("#install");
const copy = document.querySelector("#copy");
const code = document.querySelector("#code");
const status = document.querySelector("#status");

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
