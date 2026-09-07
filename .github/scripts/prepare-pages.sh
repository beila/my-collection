#!/usr/bin/env bash
set -euo pipefail

repo=${1:-.}
site=${2:-_site}

if [[ -e "$repo/facebook-instapaper/state.json" ]]; then
  echo "Private Facebook state must not be stored in the public collection" >&2
  exit 1
fi

mkdir -p "$site"
rsync \
  -a \
  --exclude '.git/' \
  --exclude '.github/' \
  --exclude '.jj/' \
  --exclude '_site/' \
  "$repo/" \
  "$site/"
