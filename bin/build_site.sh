#!/usr/bin/env bash
# Regenerate the static .html pages from the .md sources with pandoc.
#
# GitHub Pages here is served with .nojekyll, so we ship real .html files.
# .md sources stay in the repo for reading/diffing on github.com.
# Links between .md files are rewritten to .html by bin/mdlinks.lua.
#
# Usage:  bin/build_site.sh
set -euo pipefail
cd "$(dirname "$0")/.."

# <src.md>  <page title>
PAGES=(
  "index.md|Valley View astronomy"
  "astro-evening-vv.md|Astronomy Evening at Valley View"
  "telescopes.md|Valley View telescopes"
  "vv20260909/highlights.md|Valley View sky highlights — Wed Sept 9, 2026"
  "vv20260909/satellites.md|Satellite passes — Sept 9, 2026"
  "vv20260910/highlights.md|Valley View sky highlights — Thu Sept 10, 2026"
  "vv20260910/satellites.md|Satellite passes — Sept 10, 2026"
)

for entry in "${PAGES[@]}"; do
  src="${entry%%|*}"; title="${entry#*|}"
  out="${src%.md}.html"
  # css path is relative to the page's directory
  depth=$(tr -cd / <<<"$src" | wc -c)
  css=""; for ((i=0; i<depth; i++)); do css+="../"; done; css+="assets/style.css"
  pandoc --standalone --from markdown+pipe_tables --to html5 \
    --metadata pagetitle="$title" \
    --css "$css" \
    --lua-filter "$(dirname "$0")/mdlinks.lua" \
    -o "$out" "$src"
  echo "  $src -> $out"
done
echo "done."
