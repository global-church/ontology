# GC-Core Ontology

The shared schema for the Global.Church ecosystem. Defines the vocabulary that GraphDB, bridges, SPARQL queries, SHACL validation, and external consumers all depend on.

## Current Version

**v0.16.0** — See [CHANGELOG.md](CHANGELOG.md) for full history.

## Namespace

```
https://ontology.global.church/core#  (prefix: gc:)
```

Additional namespaces defined in the ontology:
- `jp:` — `https://ontology.global.church/joshuaproject#` (Joshua Project-owned concepts)
- `imb:` — `https://ontology.global.church/imb#` (IMB-owned concepts)

## File Layout

```
ontology/
├── core.ttl                     OWL 2 ontology (classes, properties, individuals)
├── core.shacl.ttl               SHACL constraint shapes
├── diagrams/                    Mermaid class hierarchy and pattern diagrams
├── data/
│   ├── seed/                    HIS registry seeds, vocab seeds (org-type, belief-type, denomination)
│   └── migrations/              Schema migration docs
├── docs/
│   ├── ontology-design-principles.md   Design rubric (DOLCE, PROV-O, namespace, minimalism)
│   ├── gc-core-reference.html          Auto-generated ontology reference (legacy, replaced by doc site)
│   └── site/                           Generated doc site output (gitignored)
├── scripts/
│   ├── build-docs.sh                   Orchestrates Widoco + pyLODE + Mermaid + JSON-LD
│   ├── widoco-config.properties        Widoco metadata
│   ├── generate-vocabs-index.py        SKOS vocabulary browser index generator
│   └── generate-diagrams-index.py      SVG diagram gallery generator
├── .github/workflows/build-docs.yml    CI: validate + build + deploy on v* tags
├── vercel.json                         Static deploy config for ontology.global.church
├── his-registry-buildout.md            HIS Registry integration log
├── CHANGELOG.md                        Version history
└── CLAUDE.md                           This file
```

## Core Type System

Built on W3C PROV-O:
- **prov:Agent** — Organizations, Teams, People (who acts)
- **prov:Activity** — Ministry activities, Assessments (what happens)
- **prov:Entity** — People Groups, Resources, Engagement Records (what is produced/tracked)

Reference data (Location, SKOS vocabularies) does NOT inherit from PROV-O.

## Versioning

Git tags on this repo serve as ontology releases (e.g., `v0.15.1`). Consumers pin to a specific tag:
- **GraphDB** fetches a tagged release at Docker build time
- **Engage app** fetches tagged TTL at Vercel build time
- **Core packages** reference the ontology by version for validation

## How to Make Changes

1. Read `docs/ontology-design-principles.md` — the design rubric
2. Edit `core.ttl` and/or `core.shacl.ttl`
3. Bump the `owl:versionInfo` in `core.ttl`
4. Update `CHANGELOG.md`
5. Tag the release: `git tag v0.X.Y && git push --tags`

Use the Claude skills for guided workflows:
- `gc-ontology-review` — evaluate changes against design principles
- `gc-turtle-author` — produce valid Turtle
- `gc-shacl` — create/update SHACL shapes
- `gc-ontology-doc` — generate documentation

## Relationship to Other Repos

| Repo | How it uses the ontology |
|---|---|
| `core/` | GraphDB Dockerfile fetches tagged release; bridges validate against it |
| `apps/engage/` | Build scripts fetch TTL to generate AI agent context and UI tooltips |
| `apps/platform/` | Indirect — consumes data shaped by the ontology via API |
| `infra/api-gateway/` | Routes SPARQL queries that reference ontology terms |

## Documentation Site

Published at `https://ontology.global.church/` (password-protected during development).

**Local build:**
```bash
# Full build (requires Docker for Widoco + WebVOWL)
bash scripts/build-docs.sh

# Without Docker (pyLODE fallback, no WebVOWL)
bash scripts/build-docs.sh --skip-widoco
```

**Prerequisites:** Docker (for Widoco), Python 3.11+ with pylode + rdflib, Node.js 20+

**How it deploys:** GitHub Action on tagged release (`v*`) → SHACL validation → build → Vercel static deploy

**URL structure:**
- `/` — OWL class/property tables + WebVOWL interactive graph
- `/vocabs/` — SKOS vocabulary browser (13 schemes)
- `/diagrams/` — Rendered Mermaid architecture diagrams (7 SVGs)
- `/core.ttl` — Raw Turtle (content negotiation)
- `/core.jsonld` — JSON-LD serialization

**Output:** `docs/site/` (gitignored — generated fresh on each tagged release)

## Owner

Paul Martel (paulmmartel@gmail.com)
