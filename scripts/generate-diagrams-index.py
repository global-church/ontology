#!/usr/bin/env python3
"""Generate an HTML gallery page for ontology architecture diagrams.

Scans for SVG files in the diagrams output directory and produces a clean
browsable HTML page displaying each diagram with its title.

Usage:
    python3 scripts/generate-diagrams-index.py [--output docs/site/diagrams/index.html]
"""

import argparse
import re
import sys
from pathlib import Path


def title_from_filename(filename: str) -> str:
    """Derive a human-readable title from an SVG filename.

    Examples:
        00-overview.svg         -> Overview
        01-class-hierarchy.svg  -> Class Hierarchy
        06-peoplegroup-engagement.svg -> Peoplegroup Engagement
    """
    stem = Path(filename).stem
    # Strip leading number prefix like "00-", "01-"
    stem = re.sub(r"^\d+-", "", stem)
    # Replace hyphens with spaces and title-case
    return stem.replace("-", " ").title()


def generate_html(diagrams: list[dict]) -> str:
    """Generate the HTML gallery page."""

    diagram_sections = []
    for d in diagrams:
        diagram_sections.append(f"""    <section class="diagram">
      <h2>{d["title"]}</h2>
      <div class="diagram-container">
        <img src="{d["filename"]}" alt="{d["title"]}" />
      </div>
      <p class="view-link"><a href="{d["filename"]}">View full SVG &rarr;</a></p>
    </section>""")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Architecture Diagrams - Global.Church Core Ontology</title>
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
    .diagram {{
      margin-bottom: 2.5rem;
      background: #fff;
      border-radius: 4px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      overflow: hidden;
    }}
    .diagram h2 {{
      font-size: 1.2rem;
      color: #1a1a2e;
      padding: 0.8rem 1rem;
      background: #f5f5f5;
      border-bottom: 1px solid #eee;
    }}
    .diagram-container {{
      padding: 1rem;
      text-align: center;
    }}
    .diagram-container img {{
      max-width: 100%;
      height: auto;
    }}
    .view-link {{
      padding: 0.5rem 1rem 0.8rem;
      font-size: 0.85rem;
    }}
    .view-link a {{
      color: #4a6fa5;
      text-decoration: none;
    }}
    .view-link a:hover {{
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
    <h1>Architecture Diagrams</h1>
    <p>Global.Church Core Ontology</p>
  </header>

{chr(10).join(diagram_sections)}

  <footer>
    Generated from Mermaid source files in <code>diagrams/</code>.
  </footer>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Generate diagram gallery HTML page")
    parser.add_argument("--output", default="docs/site/diagrams/index.html",
                        help="Output HTML file path")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    diagrams_dir = repo_root / "docs" / "site" / "diagrams"
    output_path = repo_root / args.output

    if not diagrams_dir.exists():
        print(f"Warning: diagrams directory not found at {diagrams_dir}, creating it", file=sys.stderr)
        diagrams_dir.mkdir(parents=True, exist_ok=True)

    # Find SVG files, sorted by name (preserves numeric ordering)
    svg_files = sorted(diagrams_dir.glob("*.svg"))

    if not svg_files:
        print("Warning: no SVG files found, generating empty gallery", file=sys.stderr)

    diagrams = []
    for svg in svg_files:
        title = title_from_filename(svg.name)
        diagrams.append({
            "filename": svg.name,
            "title": title,
        })
        print(f"  Found: {svg.name} -> {title}")

    # Generate HTML
    html = generate_html(diagrams)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"\nGenerated {output_path} ({len(html)} bytes)")
    print(f"  {len(diagrams)} diagram(s) included")


if __name__ == "__main__":
    main()
