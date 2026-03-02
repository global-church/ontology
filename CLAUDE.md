# GC-Core Ontology

The shared schema for the Global.Church ecosystem. Defines the vocabulary that GraphDB, bridges, SPARQL queries, SHACL validation, and external consumers all depend on.

## Current Version

**v0.15.1** — See [CHANGELOG.md](CHANGELOG.md) for full history.

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
├── gc-core.ttl                  OWL 2 ontology (classes, properties, individuals)
├── gc-core.shacl.ttl            SHACL constraint shapes
├── diagrams/                    Mermaid class hierarchy and pattern diagrams
├── data/
│   ├── seed/                    Denver churches, HIS registry seeds, vocab seeds
│   └── migrations/              Schema migration docs
├── docs/
│   ├── ontology-design-principles.md   Design rubric (DOLCE, PROV-O, namespace, minimalism)
│   ├── gc-core-reference.html          Auto-generated ontology reference
│   └── gc-core-resources-ontology.html Resource ontology reference
├── his-registry-buildout.md     HIS Registry integration log
├── CHANGELOG.md                 Version history
└── CLAUDE.md                    This file
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
2. Edit `gc-core.ttl` and/or `gc-core.shacl.ttl`
3. Bump the `owl:versionInfo` in `gc-core.ttl`
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

## Publishing (Future)

The ontology will be published at `https://ontology.global.church/` so the namespace URI is dereferenceable. Options: static hosting with content negotiation, GitHub Pages, or W3C-style PURL.

## Owner

Paul Martel (paulmmartel@gmail.com)
