# GC-Core Ontology Changelog

## v0.11.1 — 2026-02-23

### Changed: Remove prov:Entity from gc:Location

`gc:Location` is geographic reference data — coordinates, country codes, and polygons. It is not a provenance-tracked artifact. No Location instances used any PROV-O properties (`prov:wasGeneratedBy`, `prov:wasAttributedTo`, etc.). Removing the superclass aligns Location with the same treatment applied to Language (ROL, v0.5.0) and Religion (ROR, v0.7.0) — reference/classification data without PROV-O parentage.

**Rationale:** The DOLCE categorization test: locations are spatial reference points, not social objects or perdurants that accumulate provenance chains. If location provenance is ever needed (who created/updated a location record), it can be modeled with an explicit `prov:Activity` rather than forcing all locations to carry unused `prov:Entity` inference.

**Impact:**
- `gc:Location` no longer has `rdfs:subClassOf prov:Entity`
- Location instances no longer infer as `prov:Entity` (0 instances affected in practice — none used PROV-O properties)
- No SPARQL queries, SHACL shapes, or dashboard code affected
- LocationShape unchanged (only validates `gc:countryCode`, `gc:latitude`, `gc:longitude`)
- Mermaid class hierarchy diagram updated

**Completes PROV-O alignment Phase C.** All three items resolved:
1. Language → ROL SKOS migration (v0.5.0)
2. Religion → ROR SKOS migration (v0.7.0)
3. Location → removed `prov:Entity` (v0.11.1)

**GraphDB:** 913,882 triples.

**Files changed:**
| File | Change |
|---|---|
| `ontology/gc-core.ttl` | Removed `rdfs:subClassOf prov:Entity` from `gc:Location`, version bump to 0.11.1 |
| `ontology/diagrams/01-class-hierarchy.mermaid` | Location no longer inherits from `prov:Entity` |

## v0.11.0 — 2026-02-23

### Added: Worker Deployment Intelligence (Phase 11)

Extends the worker model with deployment tracking and ministry methodology classification. Enables computing "what percentage of workers serve among unreached groups" and methodology-per-group analysis.

**New MinistryRole instances:**
- `gc:ChurchPlanterRole` — Church Planter
- `gc:TranslatorRole` — Translator
- `gc:StrategyCoordinatorRole` — Strategy Coordinator

**New properties on gc:Person:**
| Property | Type | Range | Description |
|---|---|---|---|
| `gc:sendingOrganization` | ObjectProperty | `gc:Organization` | Organization that deployed/sent this worker (distinct from `gc:memberOf`) |
| `gc:deploymentStatus` | ObjectProperty | `skos:Concept` | Deployment status from `gc:DeploymentStatusScheme` |
| `gc:isCrossCultural` | DatatypeProperty | `xsd:boolean` | Whether the worker is cross-cultural to their field |
| `gc:fieldEntryDate` | DatatypeProperty | `xsd:date` | Date of field entry |

**New property on gc:MinistryActivity:**
| Property | Type | Range | Description |
|---|---|---|---|
| `gc:usesMethodology` | ObjectProperty | `skos:Concept` | Strategic methodology from `gc:MethodologyScheme` |

**New SKOS ConceptSchemes** (`data/seed/worker-deployment-vocab-seed.ttl`):
- `gc:DeploymentStatusScheme` — Active, On Furlough, In Training, Retired
- `gc:MethodologyScheme` — CPM, DMM, Four Fields, T4T, Traditional Church Planting

**SHACL shapes:**
- `PersonShape` extended with 4 optional deployment constraints (all `sh:Info` severity)
- New `MinistryActivityMethodologyShape` validates `gc:usesMethodology` (`sh:Info` severity)

**Seed data:** Denver workers annotated with deployment status, cross-cultural flags, field entry dates, and sending organizations. Ministry activities annotated with methodologies (Four Fields, DMM, T4T).

**SPARQL queries** (3 new `.rq` files):
- `worker-deployment-summary.rq` — Workers with deployment details and engaged groups
- `methodology-by-group.rq` — Methodologies used per people group with activity counts
- `reached-vs-unreached-workers.rq` — Active cross-cultural workers among reached vs unreached groups

**Design decisions:**
- Methodology modeled as SKOS ConceptScheme (not owl:Class), following the HIS registries and IMB vocab pattern
- `gc:usesMethodology` on MinistryActivity only (not Person) — methodology qualifies the activity (DOLCE perdurant), not the person
- `gc:sendingOrganization` kept distinct from `gc:memberOf` — a worker can be a member of Org A but sent by Org B

**GraphDB:** 913,890 triples (default graph), 1,021 triples (denver graph).

**Files changed:**
| File | Change |
|---|---|
| `ontology/gc-core.ttl` | 3 new roles, 5 new properties, version bump to 0.11.0 |
| `ontology/gc-core.shacl.ttl` | PersonShape extended, new MinistryActivityMethodologyShape |
| `data/seed/worker-deployment-vocab-seed.ttl` | **New** — DeploymentStatus + Methodology SKOS schemes |
| `data/seed/denver-churches.ttl` | Workers + activities annotated with deployment/methodology data |
| `test/denver-churches.ttl` | Synced from seed |
| `packages/gc-sparql/src/queries/worker-deployment-summary.rq` | **New** |
| `packages/gc-sparql/src/queries/methodology-by-group.rq` | **New** |
| `packages/gc-sparql/src/queries/reached-vs-unreached-workers.rq` | **New** |
| `apps/dashboard/scripts/generate-agent-context.mjs` | 3 new queries in CURATED_QUERIES |
| `apps/dashboard/api/_generated-context.js` | Regenerated |

## v0.10.0 — 2026-02-23

### Changed: gc:Church is now a subclass of gc:Organization

Reclassified `gc:Church` from `rdfs:subClassOf prov:Entity` to `rdfs:subClassOf gc:Organization`. This moves Church from the Entity tier into the Agent tier of the PROV-O type hierarchy.

**Inference chain (OWL-Horst):**
```
gc:Church → gc:Organization → prov:Organization → prov:Agent
```

All Church instances are now inferred as Organizations and (via `prov:Organization`) as Agents.

**Rationale:** Churches are agentive social objects with collective intentionality — they commit to serving people groups, plant other churches, endorse peers, and bear responsibility for ministry activities. The previous `prov:Entity` parentage contradicted the design principles (DOLCE ASO classification) and prevented modeling Phase 4-7 transitions where a church acts as a sending organization. See `docs/ontology-design-principles.md` section 2a.

**SHACL compatibility:** No shape changes needed. `OrganizationShape` requires only `rdfs:label` (minCount 1) — all existing Church instances already have labels. `ChurchShape` constraints are additive and don't conflict with `OrganizationShape`.

**Impact:**
- `?x a gc:Organization` queries now return churches alongside traditional organizations (28 results: 6 churches + 22 organizations)
- `gc:memberOf` range (`gc:Organization`) now validly includes churches — a person can be a member of a church
- Existing `?x a gc:Church` queries return identical results (no breakage)
- Endorsement queries (`gc:endorsingOrganization` / `gc:endorsedChurch`) unchanged
- GraphDB: 913,751 → 913,763 triples (+12 from assertion + inferred types)

**Verification:** 7 SPARQL queries in `packages/gc-sparql/src/queries/verify-church-subclass.rq` confirm subclass assertion, Organization inference, existing query stability, and endorsement query integrity.

**Files changed:**
| File | Change |
|---|---|
| `ontology/gc-core.ttl` | `gc:Church rdfs:subClassOf prov:Entity` → `gc:Church rdfs:subClassOf gc:Organization`, updated comment |
| `packages/gc-sparql/src/queries/verify-church-subclass.rq` | New — 7 verification queries |

## v0.4.2 — 2026-02-17

### Added: Church → People Group demographic relationship

New property `gc:servesPeopleGroup` links churches to the people groups they primarily serve or minister to.

| Item | Detail |
|---|---|
| Property | `gc:servesPeopleGroup` (`owl:ObjectProperty`) |
| Domain | `gc:Church` |
| Range | `gc:PeopleGroup` |
| Cardinality | 0..* (multi-valued) |

**Distinct from `gc:targetsPeopleGroup`**: The existing `gc:targetsPeopleGroup` on `gc:Overture` represents automated geographic association (which people groups are in this area). The new `gc:servesPeopleGroup` represents intentional ministry focus declared by the church itself.

**Seed data**: All 6 Denver churches now have `gc:servesPeopleGroup` triples:
- Calvary Church → Anglo-American, Hispanic American
- Arise Church → Anglo-American
- First Baptist → Anglo-American
- Red Rocks Church → Anglo-American
- Colorado Community Church → Anglo-American
- Aurora Burmese Fellowship → Burmese

**SHACL**: `ChurchShape` updated with `sh:Info` severity constraint — churches SHOULD declare at least one served people group.

**SPARQL queries** (2 new `.rq` files in gc-sparql):
- `churches-by-people-group.rq` — "Which churches serve [people group]?" (parameterized by name)
- `people-groups-with-churches-no-engagement.rq` — "Which people groups have churches but no active organizational engagement commitment?"

**Design rationale**: Property (not class) — the relationship doesn't accumulate its own properties. `gc:` namespace — GC-Core coordination concept. Passes minimalism test: real queries need it, real data populates it, directly serves the coordination use case (connection recommendations).

## v0.4.1 — 2026-02-17

### Removed: Flat external identifier properties

Removed five redundant `owl:DatatypeProperty` definitions from `gc:PeopleGroup` that duplicated what is now resolved through the linked data path (`gc:hasPeopleClassification` → HIS ROP3 SKOS concept):

| Property | Reason |
|---|---|
| `gc:rop3byCountryCode` | Composite key (ROP3+ROG3); derivable from the SKOS hierarchy + location |
| `gc:jpPeopleId` | JP people groups already linked via `gc:hasPeopleClassification` → HIS ROP3 SKOS concept + `owl:sameAs` |
| `gc:imbPeopleId` | IMB's identifier; belongs in a future IMB bridge, not gc-core |
| `gc:people3Id` | External ID; bridge concern, not gc-core |
| `gc:peopleGroupClassificationSystem` | Replaced by typed SKOS concepts via `gc:hasPeopleClassification` |

**Impact:**
- Zero live triples existed for any of these properties in GraphDB (confirmed via SPARQL COUNT)
- No SPARQL queries, dashboard code, or bridge code referenced them
- SHACL `PeopleGroupShape` updated: `sh:or` constraint now requires `gc:rop3Code`, `gc:rop25Code`, or `gc:hasPeopleClassification` (removed references to the 5 deleted properties)
- Test seed data (`test/denver-churches.ttl`) cleaned of all flat ID property usage
- `gc:PeopleGroup` class comment updated to reference linked data pattern
- Agent ontology context regenerated

**Design principle:** Minimalism — these properties didn't earn their place once `gc:hasPeopleClassification` provided the linked data resolution path to HIS ROP3 SKOS concepts.

## v0.4.0 — 2026-02-17

JP namespace migration: 3D Insight concepts moved from `gc:` → `jp:` namespace.

## v0.3.0

Engagement commitments, PROV-O patterns, Denver seed data expansion.

## v0.2.0

Joshua Project data bridge, HIS Registry of Peoples SKOS scheme.

## v0.1.0

Initial ontology: PROV-O grounded classes, GraphDB setup, engagement model.
