javascript:(()=>{
const NeoPickerCore = (() => {
  function selectItem(items, currentId, initial, randomValue) {
    if (!Array.isArray(items) || items.length === 0) {
      throw new Error("The Neo feed is empty.");
    }
    if (initial || items.length === 1) {
      return items[0];
    }
    const alternatives = items.filter((item) => String(item.id) !== String(currentId));
    const candidates = alternatives.length ? alternatives : items;
    const index = Math.min(
      candidates.length - 1,
      Math.floor(randomValue * candidates.length),
    );
    return candidates[index];
  }

  function rssPath(user, folderId) {
    if (!user?.id || !user?.rss_key) {
      throw new Error("Sign in to Instapaper before opening Neo Picker.");
    }
    return [
      "",
      "rss",
      "folder",
      encodeURIComponent(folderId),
      encodeURIComponent(user.id),
      encodeURIComponent(user.rss_key),
    ].join("/");
  }

  function normalizedUrl(value) {
    const url = new URL(value);
    url.hash = "";
    url.hostname = url.hostname.toLowerCase().replace(/^www\./, "");
    if (url.pathname.length > 1) {
      url.pathname = url.pathname.replace(/\/+$/, "");
    }
    return url.href;
  }

  function matchItems(rssItems, profileItems) {
    const profiles = new Map();
    for (const item of profileItems) {
      const key = normalizedUrl(item.url);
      profiles.set(key, [...(profiles.get(key) || []), item]);
    }
    return rssItems.map((item) => {
      const matches = profiles.get(normalizedUrl(item.url)) || [];
      if (matches.length !== 1) {
        throw new Error(
          matches.length
            ? `Neo RSS item has multiple profile matches: ${item.title}`
            : `Neo RSS item has no profile match: ${item.title}`,
        );
      }
      return {
        ...matches[0],
        title: item.title || matches[0].title,
        description: item.description || matches[0].description || "",
        published: item.published || "",
      };
    });
  }

  function youtubeSource(value) {
    const url = new URL(value);
    const host = url.hostname.toLowerCase().replace(/^www\./, "");
    if (host === "youtu.be") {
      return "oembed";
    }
    if (host !== "youtube.com") {
      return null;
    }
    const parts = url.pathname.split("/").filter(Boolean);
    if (
      (parts.length === 1 && parts[0].startsWith("@"))
      || (parts.length === 2 && ["channel", "c", "user"].includes(parts[0]))
    ) {
      return "channel";
    }
    if (
      url.pathname === "/watch"
      || url.pathname === "/playlist"
      || ["embed", "live", "shorts", "v"].includes(parts[0])
    ) {
      return "oembed";
    }
    return null;
  }

  function canonicalChannelUrl(value) {
    const url = new URL(value, "https://youtube.com");
    if (youtubeSource(url.href) !== "channel") {
      return null;
    }
    return `https://youtube.com${url.pathname.replace(/\/+$/, "")}`;
  }

  function channelFromOembed(metadata) {
    const url = canonicalChannelUrl(metadata?.author_url || "");
    if (!url) {
      throw new Error("YouTube did not return a channel URL.");
    }
    return {
      url,
      title: metadata.author_name || "",
      thumbnail: metadata.thumbnail_url || "",
    };
  }

  function createBookmarkBody(url) {
    return {url};
  }

  function bookmarkAction(bookmarkId, action, folderId) {
    const value = {bookmark_id: bookmarkId, action};
    if (folderId !== undefined) {
      value.folder_id = folderId;
    }
    return value;
  }

  return {
    bookmarkAction,
    canonicalChannelUrl,
    channelFromOembed,
    createBookmarkBody,
    matchItems,
    normalizedUrl,
    rssPath,
    selectItem,
    youtubeSource,
  };
})();

if (typeof module !== "undefined") {
  module.exports = NeoPickerCore;
}

const existingNeoPicker = document.querySelector("#neo-picker-bookmarklet");
if (existingNeoPicker) {
  existingNeoPicker.remove();
  return;
}
if (location.hostname !== "www.instapaper.com") {
  alert("Open www.instapaper.com before running Neo Picker.");
  return;
}

const host = document.createElement("div");
host.id = "neo-picker-bookmarklet";
host.style.cssText = "position:fixed;inset:0;z-index:2147483647;";
document.documentElement.append(host);
const shadow = host.attachShadow({mode: "open"});
shadow.innerHTML = `
  <style>
    :host{all:initial;color-scheme:dark}
    *{box-sizing:border-box}
    .shell{position:fixed;inset:0;display:grid;grid-template-rows:auto minmax(0,1fr) auto;
      gap:clamp(.65rem,2vw,1.3rem);padding:clamp(.7rem,2.5vw,1.8rem);
      overflow:hidden;background:radial-gradient(circle at 85% 15%,#76411d 0,transparent 32%),
      radial-gradient(circle at 10% 90%,#263b37 0,transparent 38%),#171612;color:#f8f3e8;
      font-family:Inter,ui-sans-serif,system-ui,sans-serif}
    header{display:flex;align-items:center;justify-content:space-between;gap:.8rem}
    .brand{min-width:0}.eyebrow,.published{margin:0 0 .35rem;color:#d9b98c;font-size:.72rem;
      font-weight:700;letter-spacing:.1em;text-transform:uppercase}
    h1,h2,p{margin:0}h1{font:500 clamp(1.45rem,4vw,3rem)/.98 Georgia,serif}
    .top-actions{display:flex;gap:.5rem}
    button,a{min-height:2.7rem;border:1px solid #ffffff2b;border-radius:999px;padding:.65rem .95rem;
      background:#ffffff0d;color:inherit;font:inherit;text-align:center;text-decoration:none;cursor:pointer}
    button:disabled{cursor:wait;opacity:.55}
    button:focus-visible,a:focus-visible{border-color:#edc38b;outline:none}
    .close{width:2.7rem;padding:0;font-size:1.25rem}
    .card{display:grid;grid-template-columns:minmax(14rem,1.1fr) minmax(18rem,1fr);min-height:0;
      overflow:hidden;border:1px solid #ffffff1f;border-radius:clamp(1rem,2vw,2rem);
      background:#0d0d0be8;box-shadow:0 1.5rem 4rem #0007}
    .visual{position:relative;min-height:0;overflow:hidden;background:linear-gradient(145deg,#693d23,#1e3431)}
    .visual img{width:100%;height:100%;object-fit:cover}
    .fallback{position:absolute;right:.08em;bottom:-.22em;color:#ffffff18;
      font:400 min(44vh,40vw)/1 Georgia,serif}
    .copy{display:flex;min-height:0;flex-direction:column;justify-content:center;
      padding:clamp(1rem,4vw,3.5rem)}
    h2{display:-webkit-box;overflow:hidden;font:500 clamp(1.5rem,3.5vw,3.5rem)/1.04 Georgia,serif;
      -webkit-box-orient:vertical;-webkit-line-clamp:4}
    .description{display:-webkit-box;overflow:hidden;margin-top:clamp(.7rem,2vh,1.3rem);color:#d5d0c5;
      font-size:clamp(.88rem,1.5vw,1.1rem);line-height:1.5;-webkit-box-orient:vertical;-webkit-line-clamp:6}
    .status{min-height:1.3em;margin-top:.65rem;color:#d9b98c;font-size:.78rem}
    nav{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.55rem}
    nav .primary{border-color:#edc38b;background:#edc38b;color:#21170f;font-weight:800}
    [hidden]{display:none!important}
    @media(max-width:760px){
      .shell{gap:.6rem;padding:.65rem}h1{font-size:clamp(1.3rem,6vw,2rem)}
      .card{grid-template-columns:1fr;grid-template-rows:minmax(7rem,42%) minmax(0,1fr)}
      .copy{padding:.9rem}h2{font-size:clamp(1.3rem,6vw,2.2rem);-webkit-line-clamp:3}
      .description{font-size:.86rem;-webkit-line-clamp:4}
      nav{grid-template-columns:repeat(2,minmax(0,1fr))}
      nav a,nav button,header button{min-height:2.45rem;padding:.5rem .65rem;font-size:.8rem}
    }
    @media(max-height:560px){
      .eyebrow,.description{display:none}.shell{padding:.5rem}
      .card{grid-template-columns:minmax(12rem,.8fr) 1fr;grid-template-rows:1fr}.copy{padding:.75rem}
    }
  </style>
  <main class="shell">
    <header>
      <div class="brand"><p class="eyebrow">Instapaper · Neo</p><h1>Pick one worth your attention.</h1></div>
      <div class="top-actions">
        <button id="choose" type="button">Choose another</button>
        <button id="close" class="close" type="button" aria-label="Close">×</button>
      </div>
    </header>
    <article class="card" aria-live="polite">
      <div class="visual">
        <img id="image" alt="" hidden>
        <div id="fallback" class="fallback" aria-hidden="true">N</div>
      </div>
      <section class="copy">
        <p id="published" class="published"></p>
        <h2 id="title">Loading Neo…</h2>
        <p id="description" class="description"></p>
        <p id="status" class="status"></p>
      </section>
    </article>
    <nav aria-label="Bookmark actions">
      <a id="original" class="primary" href="#">Open original</a>
      <a id="reader" href="#">Open in Instapaper</a>
      <button id="archive" type="button">Archive</button>
      <button id="neo" type="button" hidden>Add channel to Neo</button>
      <button id="brown" type="button" hidden>Add channel to Brown</button>
    </nav>
  </main>`;

const element = Object.fromEntries(
  [
    "choose",
    "close",
    "image",
    "fallback",
    "published",
    "title",
    "description",
    "status",
    "original",
    "reader",
    "archive",
    "neo",
    "brown",
  ].map((id) => [id, shadow.querySelector(`#${id}`)]),
);
let selected = null;
let currentUser = null;
let folders = null;
let channel = null;
let renderToken = 0;

function closePicker() {
  document.removeEventListener("keydown", onKeydown);
  host.remove();
}

function onKeydown(event) {
  if (event.key === "Escape") {
    closePicker();
  }
}

async function responseJson(path, options = {}) {
  const response = await fetch(path, {
    cache: "no-store",
    credentials: "same-origin",
    ...options,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(
      body.error || body.message || `Instapaper returned HTTP ${response.status}.`,
    );
  }
  return body;
}

async function responseText(path) {
  const separator = path.includes("?") ? "&" : "?";
  const response = await fetch(`${path}${separator}_=${Date.now()}`, {
    cache: "no-store",
    credentials: "same-origin",
  });
  if (!response.ok) {
    throw new Error(`Neo RSS returned HTTP ${response.status}.`);
  }
  return response.text();
}

function itemText(item, name) {
  const child = item.querySelector(name);
  return child ? child.textContent.trim() : "";
}

function plainText(value) {
  const documentValue = new DOMParser().parseFromString(value, "text/html");
  return documentValue.body.textContent.replace(/\s+/g, " ").trim();
}

function parseRss(value) {
  const documentValue = new DOMParser().parseFromString(value, "application/xml");
  if (documentValue.querySelector("parsererror")) {
    throw new Error("Neo RSS is not valid XML.");
  }
  const title = itemText(documentValue, "channel > title");
  if (title !== "Instapaper: neo") {
    throw new Error("The RSS response is not the Neo folder.");
  }
  return [...documentValue.querySelectorAll("channel > item")].map((item) => ({
    url: itemText(item, "link"),
    title: itemText(item, "title"),
    description: plainText(itemText(item, "description")),
    published: itemText(item, "pubDate"),
  }));
}

async function profileBookmarks(username, folderId) {
  const bookmarks = [];
  for (let page = 1; page <= 20; page += 1) {
    const data = await responseJson(
      `/data/profile/${encodeURIComponent(username)}?page=${page}`
      + `&folder_id=${encodeURIComponent(folderId)}&_=${Date.now()}`,
    );
    bookmarks.push(...(Array.isArray(data.bookmarks) ? data.bookmarks : []));
    if (!data.has_next) {
      return bookmarks;
    }
  }
  throw new Error("The Neo profile has too many pages.");
}

async function liveItems() {
  const session = await responseJson(`/data/user_session?_=${Date.now()}`);
  currentUser = session.user;
  if (!currentUser?.form_key) {
    throw new Error("Sign in to Instapaper before opening Neo Picker.");
  }
  folders = Object.fromEntries(
    (currentUser.folders || []).map((folder) => [
      folder.title.toLowerCase(),
      folder,
    ]),
  );
  if (!folders.neo || !folders.brown) {
    throw new Error("Neo or Brown does not exist in this Instapaper account.");
  }
  const [rss, profile] = await Promise.all([
    responseText(NeoPickerCore.rssPath(currentUser, folders.neo.id)),
    profileBookmarks(currentUser.username, folders.neo.id),
  ]);
  return NeoPickerCore.matchItems(parseRss(rss), profile);
}

function randomValue() {
  const value = new Uint32Array(1);
  crypto.getRandomValues(value);
  return value[0] / 4294967296;
}

function setBusy(busy) {
  for (const control of [
    element.choose,
    element.archive,
    element.neo,
    element.brown,
  ]) {
    control.disabled = busy;
  }
}

function setImage(value) {
  if (value) {
    element.image.src = value;
    element.image.hidden = false;
    element.fallback.hidden = true;
  } else {
    element.image.hidden = true;
    element.image.removeAttribute("src");
    element.fallback.hidden = false;
  }
}

function showChannelActions(value) {
  channel = value;
  element.neo.hidden = !value;
  element.brown.hidden = !value;
}

async function enrichYouTube(item, token) {
  const source = NeoPickerCore.youtubeSource(item.url);
  if (!source) {
    return;
  }
  if (source === "channel") {
    showChannelActions({
      url: NeoPickerCore.canonicalChannelUrl(item.url),
      title: "",
      thumbnail: item.og_image || "",
    });
    return;
  }
  const endpoint = new URL("https://www.youtube.com/oembed");
  endpoint.searchParams.set("url", item.url);
  endpoint.searchParams.set("format", "json");
  try {
    const response = await fetch(endpoint);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const value = NeoPickerCore.channelFromOembed(await response.json());
    if (token === renderToken) {
      showChannelActions(value);
      setImage(value.thumbnail || item.og_image || "");
    }
  } catch {
    if (token === renderToken) {
      element.status.textContent = "The YouTube channel could not be resolved.";
    }
  }
}

function render(item) {
  selected = item;
  renderToken += 1;
  const token = renderToken;
  showChannelActions(null);
  element.title.textContent = item.title;
  element.description.textContent =
    item.description || "No preview text is available.";
  element.published.textContent = item.published || item.site_name || "";
  element.status.textContent = "";
  element.original.href = item.url;
  element.reader.href = `/read/${encodeURIComponent(item.id)}`;
  setImage(item.og_image || "");
  enrichYouTube(item, token);
}

async function choose(initial) {
  setBusy(true);
  element.status.textContent = "Refreshing Neo…";
  try {
    const items = await liveItems();
    render(
      NeoPickerCore.selectItem(items, selected?.id, initial, randomValue()),
    );
  } catch (error) {
    element.status.textContent = error.message;
    if (!selected) {
      element.title.textContent = "Neo is unavailable.";
      element.description.textContent =
        "Open Instapaper while signed in, then run Neo Picker again.";
    }
  } finally {
    setBusy(false);
  }
}

async function mutate(path, body) {
  return responseJson(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Form-Key": currentUser.form_key,
      "X-Requested-With": "XMLHttpRequest",
    },
    body: JSON.stringify(body),
  });
}

async function archiveSelected() {
  if (!selected) {
    return;
  }
  setBusy(true);
  try {
    await mutate("/data/bookmarks/actions", {
      actions: [NeoPickerCore.bookmarkAction(selected.id, "archive")],
    });
    selected = null;
    await choose(true);
  } catch (error) {
    element.status.textContent = error.message;
  } finally {
    setBusy(false);
  }
}

async function saveChannel(folderName) {
  if (!channel || !folders?.[folderName]) {
    return;
  }
  setBusy(true);
  try {
    const created = await mutate(
      "/data/bookmarks/create",
      NeoPickerCore.createBookmarkBody(channel.url),
    );
    const bookmarkId = created.bookmark?.id || created.bookmark?.bookmark_id;
    if (!created.success || !bookmarkId) {
      throw new Error("Instapaper did not return the saved channel.");
    }
    await mutate("/data/bookmarks/actions", {
      actions: [
        NeoPickerCore.bookmarkAction(
          bookmarkId,
          "move",
          folders[folderName].id,
        ),
      ],
    });
    const name = channel.title || "YouTube channel";
    element.status.textContent =
      `${name} was added to ${folders[folderName].title}.`;
  } catch (error) {
    element.status.textContent = error.message;
  } finally {
    setBusy(false);
  }
}

element.choose.addEventListener("click", () => choose(false));
element.close.addEventListener("click", closePicker);
element.archive.addEventListener("click", archiveSelected);
element.neo.addEventListener("click", () => saveChannel("neo"));
element.brown.addEventListener("click", () => saveChannel("brown"));
document.addEventListener("keydown", onKeydown);
choose(true);

})();