# My Collection

Public, generated reading copies used by local automation. The
`facebook-instapaper/` tree contains self-contained Facebook post articles and
the collector's deduplication state.

Content is deployed to GitHub Pages after each push to `main`.

## Publication filtering

The Pages workflow stages a separate public artifact. The Facebook profile in
`UNPUBLISHED_FACEBOOK_PROFILE` is omitted from that artifact, and its exact
profile and post records are removed from the deployed copy of
`facebook-instapaper/state.json`. The repository source tree and canonical
state remain unchanged, so removing the workflow filter republishes them.
