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
