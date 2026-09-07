# My Collection

Generated reading copies used by local automation. The
`facebook-instapaper/` tree contains Facebook post articles, copied media, and
the collector's deduplication and delivery state.

A filtered public artifact is deployed to GitHub Pages after each push to
`main` when Pages is available for the repository. The source checkout can also
retain articles intended only for Instapaper private-content delivery. GitHub
Free automatically unpublishes Pages when a personal repository becomes
private, so a private source repository may require a separate public
deployment repository.

## Publication Filtering

The Pages workflow stages a separate artifact with
`.github/scripts/prepare-pages.sh`. For every Facebook state record whose
`delivery_mode` is `instapaper-private`, the script removes the exact generated
HTML path and sibling media directory. It also removes private post records and
the affected profile metadata from the deployed copy of
`facebook-instapaper/state.json`.

The repository source tree and canonical state remain unchanged. A temporary
`LEGACY_UNPUBLISHED_FACEBOOK_PROFILE` workflow setting continues to exclude
Se-Jeoung Kim records created before delivery modes were stored; it can be
removed after those records are explicitly migrated.
