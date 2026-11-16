#!/usr/bin/env bash
set -euo pipefail

repo=${1:-.}
checkpoint_dir=${2:?A checkpoint directory is required}
manifest=$(sha256sum "$repo/.github/legacy-image-migration.json" | cut -d ' ' -f 1)
mkdir -p "$checkpoint_dir"

gh api --method GET "repos/$GITHUB_REPOSITORY/actions/artifacts" \
  -f "name=legacy-image-checkpoint-$manifest" -f per_page=100 \
  --jq '[.artifacts[] | select(.expired == false)] | max_by(.id)' \
  > "$checkpoint_dir/artifact.json"
run_id=$(jq -r '.workflow_run.id // empty' "$checkpoint_dir/artifact.json")
if [[ -z "$run_id" ]]; then
  exit 0
fi
gh run download "$run_id" --repo "$GITHUB_REPOSITORY" \
  --name "legacy-image-checkpoint-$manifest" --dir "$checkpoint_dir"
jq '{updated_at, run_id: .workflow_run.id}' "$checkpoint_dir/artifact.json" \
  > "$checkpoint_dir/checkpoint.json"
