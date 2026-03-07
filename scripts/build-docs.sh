#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────
# build-docs.sh — Generate ontology documentation site
#
# Orchestrates:
#   1. Widoco (Docker) or pyLODE fallback for core.ttl
#   2. pyLODE for each SKOS vocabulary seed file
#   3. Mermaid diagrams → SVG
#   4. JSON-LD export of core.ttl
#   5. Copy core.ttl for content negotiation
#   6. Vocab index page
#   7. Diagram index page
#   8. Summary
# ──────────────────────────────────────────────────────────────

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# ── Flags ────────────────────────────────────────────────────
SKIP_WIDOCO=false
VERSION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-widoco) SKIP_WIDOCO=true; shift ;;
    --version)     VERSION="$2"; shift 2 ;;
    --version=*)   VERSION="${1#*=}"; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ── Resolve version from core.ttl if not provided ───────────
if [[ -z "$VERSION" ]]; then
  VERSION=$(python3 -c "
from rdflib import Graph, Namespace
g = Graph()
g.parse('core.ttl', format='turtle')
OWL = Namespace('http://www.w3.org/2002/07/owl#')
for s, p, o in g.triples((None, OWL.versionInfo, None)):
    print(str(o))
    break
" 2>/dev/null || echo "unknown")
  echo "Detected ontology version: $VERSION"
fi

OUT="docs/site"

# ── Step 0: Clean output directory ──────────────────────────
echo "==> Cleaning $OUT/"
rm -rf "$OUT"
mkdir -p "$OUT"

# ── Step 1: Widoco or pyLODE for core ontology ──────────────
if [[ "$SKIP_WIDOCO" == "true" ]]; then
  echo "==> Skipping Widoco (--skip-widoco), using pyLODE for core ontology"
  pylode core.ttl -o "$OUT/index.html"
else
  echo "==> Running Widoco via Docker"

  # Detect architecture for Docker platform flag
  ARCH=$(uname -m)
  PLATFORM_FLAG=""
  if [[ "$ARCH" == "arm64" || "$ARCH" == "aarch64" ]]; then
    PLATFORM_FLAG="--platform linux/amd64"
    echo "   ARM64 detected, using --platform linux/amd64"
  fi

  WIDOCO_OK=false
  if command -v docker &>/dev/null; then
    # Pull image (with platform flag if needed)
    if docker pull $PLATFORM_FLAG ghcr.io/dgarijo/widoco:latest 2>/dev/null; then
      # Run Widoco
      if docker run --rm $PLATFORM_FLAG \
        -v "$REPO_ROOT:/ontology" \
        ghcr.io/dgarijo/widoco:latest \
        -ontFile /ontology/core.ttl \
        -outFolder /ontology/docs/site \
        -confFile /ontology/scripts/widoco-config.properties \
        -webVowl -rewriteAll -lang en -noPlaceHolderText 2>&1; then
        WIDOCO_OK=true
        echo "   Widoco completed successfully"
      fi
    fi
  fi

  if [[ "$WIDOCO_OK" == "false" ]]; then
    echo "WARNING: Widoco unavailable, using pyLODE fallback (no WebVOWL)"
    pylode core.ttl -o "$OUT/index.html"
  fi
fi

# ── Step 2: pyLODE for SKOS vocabularies ────────────────────
echo "==> Generating vocabulary docs with pyLODE"

VOCAB_ENTRIES=(
  "data/seed/organization-type-vocab-seed.ttl|vocabs/org-type"
  "data/seed/belief-type-vocab-seed.ttl|vocabs/belief-type"
  "data/seed/denomination-vocab-seed.ttl|vocabs/denomination"
  "data/seed/engagement-type-vocab-seed.ttl|vocabs/engagement-type"
  "data/seed/claim-status-vocab-seed.ttl|vocabs/claim-status"
  "data/seed/imb-vocab-seed.ttl|vocabs/imb"
  "data/seed/his-rog.ttl|vocabs/his-rog"
  "data/seed/his-ror.ttl|vocabs/his-ror"
)

for entry in "${VOCAB_ENTRIES[@]}"; do
  src="${entry%%|*}"
  slug="${entry##*|}"
  outdir="$OUT/$slug"
  mkdir -p "$outdir"
  echo "   $src -> $slug/"
  pylode "$src" -o "$outdir/index.html" -p vocpub || \
    echo "   WARNING: pyLODE failed for $src"
done

# ── Step 3: Mermaid diagrams → SVG ──────────────────────────
echo "==> Rendering Mermaid diagrams to SVG"
mkdir -p "$OUT/diagrams"

for mermaid_file in diagrams/*.mermaid; do
  [[ -f "$mermaid_file" ]] || continue
  basename=$(basename "$mermaid_file" .mermaid)
  echo "   $mermaid_file -> diagrams/$basename.svg"
  npx -y @mermaid-js/mermaid-cli \
    -i "$mermaid_file" \
    -o "$OUT/diagrams/$basename.svg" \
    -t neutral 2>&1 || \
    echo "   WARNING: Mermaid render failed for $mermaid_file"
done

# ── Step 4: Generate core.jsonld ────────────────────────────
echo "==> Generating core.jsonld"
python3 -c "
from rdflib import Graph
g = Graph()
g.parse('core.ttl', format='turtle')
g.serialize('$OUT/core.jsonld', format='json-ld')
"

# ── Step 5: Copy core.ttl for content negotiation ───────────
echo "==> Copying core.ttl to $OUT/"
cp core.ttl "$OUT/core.ttl"

# ── Step 6: Generate vocabs/index.html ──────────────────────
echo "==> Generating vocabs/index.html"
mkdir -p "$OUT/vocabs"
cat > "$OUT/vocabs/index.html" <<'VOCHTML'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>GC Ontology — Vocabulary Index</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; color: #333; }
    h1 { border-bottom: 2px solid #2563eb; padding-bottom: 0.5rem; }
    ul { list-style: none; padding: 0; }
    li { margin: 0.5rem 0; }
    a { color: #2563eb; text-decoration: none; font-size: 1.1rem; }
    a:hover { text-decoration: underline; }
    .back { margin-top: 2rem; font-size: 0.9rem; }
  </style>
</head>
<body>
  <h1>Vocabulary Index</h1>
  <p>SKOS vocabulary schemes used by the Global.Church Core Ontology.</p>
  <ul>
    <li><a href="org-type/">Organization Type</a></li>
    <li><a href="belief-type/">Belief Type</a></li>
    <li><a href="denomination/">Denomination</a></li>
    <li><a href="engagement-type/">Engagement Type</a></li>
    <li><a href="claim-status/">Claim Status</a></li>
    <li><a href="imb/">IMB Vocabularies</a></li>
    <li><a href="his-rog/">HIS Registry of Geography (ROG)</a></li>
    <li><a href="his-ror/">HIS Registry of Religions (ROR)</a></li>
  </ul>
  <p class="back"><a href="../">&larr; Back to ontology</a></p>
</body>
</html>
VOCHTML

# ── Step 7: Generate diagrams/index.html ────────────────────
echo "==> Generating diagrams/index.html"

# Build the SVG list dynamically
SVG_LIST=""
for svg in "$OUT"/diagrams/*.svg; do
  [[ -f "$svg" ]] || continue
  name=$(basename "$svg" .svg)
  # Convert filename to title (replace hyphens, drop leading number)
  title=$(echo "$name" | sed 's/^[0-9]*-//; s/-/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)}1')
  SVG_LIST+="    <div class=\"diagram\"><h2>${title}</h2><img src=\"${name}.svg\" alt=\"${title}\"></div>
"
done

cat > "$OUT/diagrams/index.html" <<DIAGHTML
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>GC Ontology — Diagrams</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 1000px; margin: 2rem auto; padding: 0 1rem; color: #333; }
    h1 { border-bottom: 2px solid #2563eb; padding-bottom: 0.5rem; }
    .diagram { margin: 2rem 0; }
    .diagram h2 { font-size: 1.2rem; color: #1e40af; }
    .diagram img { max-width: 100%; border: 1px solid #e5e7eb; border-radius: 8px; }
    .back { margin-top: 2rem; font-size: 0.9rem; }
  </style>
</head>
<body>
  <h1>Ontology Diagrams</h1>
  <p>Architecture and class hierarchy diagrams for the Global.Church Core Ontology.</p>
${SVG_LIST}
  <p class="back"><a href="../">&larr; Back to ontology</a></p>
</body>
</html>
DIAGHTML

# ── Step 8: Summary ─────────────────────────────────────────
echo ""
echo "=== Build complete ==="
FILE_COUNT=$(find "$OUT" -type f | wc -l | tr -d ' ')
echo "Generated $FILE_COUNT files in $OUT/"
echo ""
echo "Contents:"
find "$OUT" -type f | sort | sed "s|^$OUT/|  |"
