#!/usr/bin/env python3
"""Generate an HTML index page for SKOS vocabulary seed files.

Parses each seed Turtle file with rdflib, extracts ConceptScheme metadata
and concept counts, and produces a clean browsable HTML page organised by
namespace group.

Usage:
    python3 scripts/generate-vocabs-index.py [--version 0.16.0] [--output docs/site/vocabs/index.html]
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from rdflib import Graph, Namespace, RDF
except ImportError:
    print("Error: rdflib is required. Install with: pip install rdflib", file=sys.stderr)
    sys.exit(1)

SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
DCTERMS = Namespace("http://purl.org/dc/terms/")

# Seed file → output slug mapping and namespace group assignment
SEED_FILES = [
    # (filename, slug, group)
    ("organization-type-vocab-seed.ttl", "org-type", "gc"),
    ("belief-type-vocab-seed.ttl", "belief-type", "gc"),
    ("denomination-vocab-seed.ttl", "denomination", "gc"),
    ("engagement-type-vocab-seed.ttl", "engagement-type", "gc"),
    ("claim-status-vocab-seed.ttl", "claim-status", "gc"),
    ("imb-vocab-seed.ttl", "imb", "imb"),
    ("his-rog.ttl", "his-rog", "his"),
    ("his-ror.ttl", "his-ror", "his"),
]

# Fallback descriptions if the seed file has no dcterms:description or skos:definition
FALLBACK_DESCRIPTIONS = {
    "Organization Type": "Classification of organizations by type (Church, Mission Agency, Denomination, etc.).",
    "Belief Type": "High-level belief classification for organizations.",
    "Denomination": "Denominational affiliation categories.",
    "Engagement Type": "Types of engagement activities with people groups.",
    "Claim Status": "Status values for engagement claims (Pending, Approved, Rejected, Withdrawn).",
    "Global Status of Evangelical Christianity": "Seven-level scale (0-6) assessing evangelical Christianity status among a people group.",
    "Strategic Priority Index": "Three-category index for IMB strategic priority classification.",
    "Church Planting Status": "Three-level scale for church planting activity status.",
    "Evangelical Level": "Eleven categorical bands of evangelical percentage.",
    "IMB Target Audience Scheme": "IMB target audience classification.",
    "IMB Affinity Region Scheme": "IMB affinity-based region groupings.",
    "HIS Registry of Geography": "Three-level geography hierarchy: Region (5) -> Subregion (22) -> Country (242).",
    "HIS Registry of Religions": "Two-level religion classification: families (10) -> sub-traditions (36).",
}

GROUP_LABELS = {
    "gc": "GC Core Vocabularies",
    "imb": "IMB Vocabularies",
    "his": "HIS Registries",
}

GROUP_ORDER = ["gc", "imb", "his"]


def parse_seed_file(filepath: Path) -> list[dict]:
    """Parse a seed file and return a list of scheme info dicts."""
    g = Graph()
    g.parse(str(filepath), format="turtle")

    schemes = []
    for scheme_uri in g.subjects(RDF.type, SKOS.ConceptScheme):
        label = g.value(scheme_uri, SKOS.prefLabel)
        label_str = str(label) if label else str(scheme_uri).split("#")[-1].split("/")[-1]

        description = g.value(scheme_uri, DCTERMS.description)
        if not description:
            description = g.value(scheme_uri, SKOS.definition)
        desc_str = str(description) if description else FALLBACK_DESCRIPTIONS.get(label_str, "")

        # Count concepts in this scheme
        concept_count = 0
        for concept in g.subjects(SKOS.inScheme, scheme_uri):
            if (concept, RDF.type, SKOS.Concept) in g:
                concept_count += 1

        schemes.append({
            "uri": str(scheme_uri),
            "label": label_str,
            "description": desc_str,
            "concept_count": concept_count,
        })

    return schemes


def generate_html(all_entries: dict[str, list[dict]], version: str) -> str:
    """Generate the HTML page content."""

    group_sections = []
    for group_key in GROUP_ORDER:
        entries = all_entries.get(group_key, [])
        if not entries:
            continue

        rows = []
        for entry in entries:
            note = ""
            if entry["label"] == "Belief Type":
                note = ' <span style="color: #b8860b; font-size: 0.85em;">(may be superseded by HIS ROR)</span>'

            slug = entry.get("slug", "")
            link = f'<a href="{slug}.html">{entry["label"]}</a>' if slug else entry["label"]

            rows.append(f"""        <tr>
          <td>{link}{note}</td>
          <td><code style="font-size: 0.85em; color: #666;">{entry["uri"]}</code></td>
          <td style="text-align: center;">{entry["concept_count"]}</td>
          <td>{entry["description"]}</td>
        </tr>""")

        group_sections.append(f"""    <h2>{GROUP_LABELS[group_key]}</h2>
    <table>
      <thead>
        <tr>
          <th>Scheme</th>
          <th>URI</th>
          <th>Concepts</th>
          <th>Description</th>
        </tr>
      </thead>
      <tbody>
{chr(10).join(rows)}
      </tbody>
    </table>""")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SKOS Vocabulary Browser - Global.Church Core Ontology</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      line-height: 1.6;
      color: #333;
      max-width: 1100px;
      margin: 0 auto;
      padding: 2rem 1.5rem;
      background: #fafafa;
    }}
    header {{
      margin-bottom: 2rem;
      padding-bottom: 1rem;
      border-bottom: 2px solid #e0e0e0;
    }}
    header h1 {{
      font-size: 1.8rem;
      color: #1a1a2e;
      margin-bottom: 0.25rem;
    }}
    header p {{
      color: #666;
      font-size: 0.95rem;
    }}
    nav {{
      margin-bottom: 1.5rem;
    }}
    nav a {{
      color: #4a6fa5;
      text-decoration: none;
      font-size: 0.9rem;
    }}
    nav a:hover {{
      text-decoration: underline;
    }}
    h2 {{
      font-size: 1.3rem;
      color: #1a1a2e;
      margin: 2rem 0 0.75rem;
      padding-bottom: 0.4rem;
      border-bottom: 1px solid #e0e0e0;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 1.5rem;
      background: #fff;
      border-radius: 4px;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }}
    th {{
      background: #f5f5f5;
      text-align: left;
      padding: 0.6rem 0.8rem;
      font-size: 0.85rem;
      color: #555;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}
    td {{
      padding: 0.6rem 0.8rem;
      border-top: 1px solid #eee;
      font-size: 0.9rem;
      vertical-align: top;
    }}
    td a {{
      color: #4a6fa5;
      text-decoration: none;
      font-weight: 500;
    }}
    td a:hover {{
      text-decoration: underline;
    }}
    footer {{
      margin-top: 3rem;
      padding-top: 1rem;
      border-top: 1px solid #e0e0e0;
      color: #999;
      font-size: 0.8rem;
    }}
  </style>
</head>
<body>
  <nav><a href="../">&larr; Back to Ontology</a></nav>
  <header>
    <h1>SKOS Vocabulary Browser</h1>
    <p>Global.Church Core Ontology v{version}</p>
  </header>

{chr(10).join(group_sections)}

  <footer>
    Generated from seed data files. See <code>data/seed/</code> for source Turtle.
  </footer>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Generate SKOS vocabulary index HTML page")
    parser.add_argument("--version", default="0.16.0", help="Ontology version (default: 0.16.0)")
    parser.add_argument("--output", default="docs/site/vocabs/index.html", help="Output HTML file path")
    args = parser.parse_args()

    # Resolve paths relative to repo root (script is in scripts/)
    repo_root = Path(__file__).resolve().parent.parent
    seed_dir = repo_root / "data" / "seed"
    output_path = repo_root / args.output

    if not seed_dir.exists():
        print(f"Error: seed directory not found at {seed_dir}", file=sys.stderr)
        sys.exit(1)

    # Parse all seed files and organise by group
    all_entries: dict[str, list[dict]] = {k: [] for k in GROUP_ORDER}

    for filename, slug, group in SEED_FILES:
        filepath = seed_dir / filename
        if not filepath.exists():
            print(f"Warning: {filepath} not found, skipping", file=sys.stderr)
            continue

        schemes = parse_seed_file(filepath)
        for scheme in schemes:
            scheme["slug"] = slug
            all_entries[group].append(scheme)

        print(f"  Parsed {filename}: {len(schemes)} scheme(s)")

    # Generate HTML
    html = generate_html(all_entries, args.version)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"\nGenerated {output_path} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
