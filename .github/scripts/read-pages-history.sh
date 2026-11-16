#!/usr/bin/env bash
set -euo pipefail

history_dir=${1:?A history directory is required}
public_history_url=${2:-}
mkdir -p "$history_dir"

gh api --method GET "repos/$GITHUB_REPOSITORY/actions/artifacts" \
  -f name=pages-size-history -f per_page=100 \
  --jq '[.artifacts[] | select(.expired == false)] | sort_by(.id) | reverse' \
  > "$history_dir/artifacts.json"

# A successful build does not prove that Pages deployed its artifact.
while IFS= read -r run_id; do
  conclusion=$(gh api "repos/$GITHUB_REPOSITORY/actions/runs/$run_id" --jq .conclusion)
  if [[ "$conclusion" != success ]]; then
    continue
  fi
  gh run download "$run_id" --repo "$GITHUB_REPOSITORY" \
    --name pages-size-history --dir "$history_dir"
  exit 0
done < <(jq -r '.[].workflow_run.id' "$history_dir/artifacts.json")

if [[ -n "$public_history_url" ]]; then
  curl --fail --silent --show-error --location --retry 3 --max-time 45 \
    "$public_history_url" --output "$history_dir/collection.json"
  exit 0
fi
printf '{"history":[]}\n' > "$history_dir/collection.json"
