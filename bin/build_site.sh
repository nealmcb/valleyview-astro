#!/usr/bin/env bash
# Regenerate the static .html pages from the .md sources with pandoc.
#
# GitHub Pages here is served with .nojekyll, so we ship real .html files.
# .md sources stay in the repo for reading/diffing on github.com.
#
# Usage:  bin/build_site.sh
set -euo pipefail
cd "$(dirname "$0")/.."

CSS=assets/style.css

render() {  # <src.md> <out.html> <title> <path-to-css>
    pandoc --standalone --from markdown+pipe_tables --to html5 \
        --metadata title="$3" \
        --css "$4" \
        --lua-filter "$(dirname "$0")/mdlinks.lua" \
        -o "$2" "$1"
    echo "  $1 -> $2"
}

mkdir -p assets
render index.md                     index.html                     "Valley View astronomy"            "$CSS"
render astro-evening-vv.md          astro-evening-vv.html          "Astronomy Evening at Valley View" "$CSS"
render vv20260909/highlights.md     vv20260909/highlights.html     "Valley View sky highlights — Sept 9–10, 2026" "../$CSS"

echo "done."
