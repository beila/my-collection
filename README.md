# My Collection

Public generated reading copies used by local automation. The
`facebook-instapaper/` tree contains only publicly accessible Facebook post
articles and copied media.

A GitHub Pages artifact is deployed after each push to `main`.

## Privacy Boundary

Facebook collector state and authenticated-only generated articles are stored
outside this public repository under
`instapaper-picker/private-facebook-content/`. The Pages staging script fails
if a Facebook state file appears here, preventing private collector metadata
from being deployed accidentally.
