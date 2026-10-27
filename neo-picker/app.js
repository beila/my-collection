const stateKey = "neo-picker:selected-id";
const elements = {
  choose: document.querySelector("#choose"),
  title: document.querySelector("#title"),
  description: document.querySelector("#description"),
  published: document.querySelector("#published"),
  status: document.querySelector("#status"),
  image: document.querySelector("#preview-image"),
  fallback: document.querySelector("#visual-fallback"),
  original: document.querySelector("#open-original"),
  instapaper: document.querySelector("#open-instapaper"),
  neo: document.querySelector("#save-neo"),
  brown: document.querySelector("#save-brown"),
};

let items = [];
let selected = null;

function videoId(url) {
  const parsed = new URL(url);
  if (!/(^|\.)youtu\.be$/.test(parsed.hostname) &&
      !/(^|\.)youtube\.com$/.test(parsed.hostname)) {
    return null;
  }
  if (/(^|\.)youtu\.be$/.test(parsed.hostname)) {
    return parsed.pathname.split("/").filter(Boolean)[0] || null;
  }
  if (parsed.pathname === "/watch") {
    return parsed.searchParams.get("v");
  }
  const parts = parsed.pathname.split("/").filter(Boolean);
  return ["embed", "live", "shorts", "v"].includes(parts[0])
    ? parts[1] || null
    : null;
}

function channelUrl(url) {
  const parsed = new URL(url);
  if (!/(^|\.)youtube\.com$/.test(parsed.hostname)) {
    return null;
  }
  const parts = parsed.pathname.split("/").filter(Boolean);
  if (parts.length === 1 && parts[0].startsWith("@")) {
    return `https://youtube.com/${parts[0]}`;
  }
  if (parts.length === 2 && ["channel", "c", "user"].includes(parts[0])) {
    return `https://youtube.com/${parts.join("/")}`;
  }
  return null;
}

function randomItem() {
  if (items.length === 1) {
    return items[0];
  }
  const alternatives = selected
    ? items.filter((item) => item.id !== selected.id)
    : items;
  const values = new Uint32Array(1);
  crypto.getRandomValues(values);
  return alternatives[values[0] % alternatives.length];
}

function saveUrl(channel, folder) {
  const marked = new URL(channel);
  marked.hash = `instapaper-picker=${folder}`;
  const target = new URL("https://www.instapaper.com/edit");
  target.searchParams.set("url", marked.href);
  target.searchParams.set("title", `YouTube channel for ${folder}`);
  return target.href;
}

function setChannelActions(channel) {
  for (const [folder, link] of [["neo", elements.neo], ["brown", elements.brown]]) {
    link.href = saveUrl(channel, folder);
    link.hidden = false;
  }
}

async function enrichYouTube(item) {
  const directChannel = channelUrl(item.url);
  if (directChannel) {
    setChannelActions(directChannel);
    return;
  }
  const id = videoId(item.url);
  if (!id) {
    return;
  }
  elements.image.src = `https://i.ytimg.com/vi/${encodeURIComponent(id)}/hqdefault.jpg`;
  elements.image.alt = "";
  elements.image.hidden = false;
  elements.fallback.hidden = true;
  const endpoint = new URL("https://www.youtube.com/oembed");
  endpoint.searchParams.set("url", item.url);
  endpoint.searchParams.set("format", "json");
  try {
    const response = await fetch(endpoint);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const metadata = await response.json();
    const resolved = channelUrl(metadata.author_url || "");
    if (resolved && selected?.id === item.id) {
      setChannelActions(resolved);
    }
  } catch {
    elements.status.textContent = "The YouTube channel could not be resolved.";
  }
}

function render(item) {
  selected = item;
  sessionStorage.setItem(stateKey, item.id);
  elements.title.textContent = item.title;
  elements.description.textContent = item.description || "No preview text is available.";
  elements.published.textContent = item.published || "";
  elements.status.textContent = "";
  elements.original.href = item.url;
  elements.instapaper.href = item.instapaperUrl;
  elements.image.hidden = true;
  elements.image.removeAttribute("src");
  elements.fallback.hidden = false;
  elements.neo.hidden = true;
  elements.brown.hidden = true;
  enrichYouTube(item);
}

async function start() {
  try {
    const response = await fetch("bookmarks.json", {cache: "no-store"});
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    items = Array.isArray(data.items) ? data.items : [];
    if (!items.length) {
      throw new Error("The Neo feed is empty.");
    }
    const saved = sessionStorage.getItem(stateKey);
    render(items.find((item) => item.id === saved) || randomItem());
  } catch (error) {
    elements.title.textContent = "Neo is unavailable.";
    elements.description.textContent = error.message;
    elements.choose.disabled = true;
  }
}

elements.choose.addEventListener("click", () => render(randomItem()));
start();
