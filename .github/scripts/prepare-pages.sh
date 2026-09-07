#!/usr/bin/env bash
set -euo pipefail

repo=${1:-.}
site=${2:-_site}
state="$repo/facebook-instapaper/state.json"
legacy_profile=${LEGACY_UNPUBLISHED_FACEBOOK_PROFILE:-}
legacy_profile_url=
rsync_args=(
  -a
  --exclude '.git/'
  --exclude '.github/'
  --exclude '.jj/'
  --exclude '_site/'
)

if [[ -n "$legacy_profile" ]]; then
  legacy_profile_url="https://www.facebook.com/$legacy_profile"
  rsync_args+=(--exclude "facebook-instapaper/$legacy_profile/")
fi

mkdir -p "$site"
rsync "${rsync_args[@]}" "$repo/" "$site/"

while IFS= read -r article_path; do
  [[ -z "$article_path" ]] && continue
  case "$article_path" in
    facebook-instapaper/*/*.html)
      rm -f "$site/$article_path"
      rm -rf "${site:?}/${article_path%.html}"
      ;;
    *)
      echo "Invalid private Facebook article path: $article_path" >&2
      exit 1
      ;;
  esac
done < <(
  jq -r --arg legacy_profile_url "$legacy_profile_url" '
    .posts[]
    | select(
        .delivery_mode == "instapaper-private"
        or (
          $legacy_profile_url != ""
          and .profile_url == $legacy_profile_url
        )
      )
    | .article_path // empty
  ' "$state"
)

jq --arg legacy_profile_url "$legacy_profile_url" '
  def private_record:
    .delivery_mode == "instapaper-private"
    or (
      $legacy_profile_url != ""
      and .profile_url == $legacy_profile_url
    );
  (
    [
      .posts[]
      | select(private_record)
      | .profile_url
      | select(. != null)
    ]
    | unique
  ) as $private_profiles
  | .posts |= with_entries(select((.value | private_record) | not))
  | .profiles |= with_entries(
      .key as $profile_url
      | select(($private_profiles | index($profile_url)) == null)
    )
' "$state" > "$site/facebook-instapaper/state.json.tmp"
mv \
  "$site/facebook-instapaper/state.json.tmp" \
  "$site/facebook-instapaper/state.json"
