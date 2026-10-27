# My Collection

Public generated reading copies used by local automation. The
`facebook-instapaper/` tree contains only publicly accessible Facebook post
articles and copied media.

A GitHub Pages artifact is deployed after each push to `main`.

## Neo Picker

`neo-picker/` is a full-screen static application for choosing one random item
from the current Instapaper Neo RSS window. The maintenance scheduler publishes
its credential-free `bookmarks.json`; the private RSS URL and account key are
never stored in this repository. The published bookmark titles, descriptions,
original URLs, and bookmark IDs are public.

The app opens original and Instapaper URLs in the current tab and restores the
selected preview after browser Back. Its Instapaper control is for manual
archive work and is not labelled as an archive operation. YouTube entries can
open confirmation flows that mark a channel for later routing to Neo or Brown
by the maintenance scheduler.

## Privacy Boundary

Facebook collector state and authenticated-only generated articles are stored
outside this public repository under
`instapaper-picker/private-facebook-content/`. The Pages staging script fails
if a Facebook state file appears here, preventing private collector metadata
from being deployed accidentally.
