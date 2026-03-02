# HIS Registries Integration — Buildout Plan for Claude Code

> **How to run** — Use the orchestrator script. It launches one Claude Code agent per phase, checks for clean git state between phases, logs everything, and stops on failure.
>
> ```bash
> # Run all phases (1-5 headless, 6 interactive)
> ./scripts/run-his-buildout.sh
>
> # Resume from a specific phase (e.g., after fixing a failure)
> ./scripts/run-his-buildout.sh --from 3
>
> # Run a single phase
> ./scripts/run-his-buildout.sh --only 2
>
> # Preview what would run
> ./scripts/run-his-buildout.sh --dry-run
> ```
>
> **Why one agent per phase**: Each phase gets a fresh Claude Code session with full context window. A single session running all 6 phases would lose early context by Phase 4. The orchestrator handles sequencing, validation checking, and failure recovery.
>
> **Phase 6** (live deployment) runs interactively — no `--dangerouslySkipPermissions` — because it needs live credentials and hits production GraphDB.
>
> <details><summary>Manual execution (without orchestrator)</summary>
>
> ```bash
> claude -p "Read his-registry-buildout.md. Execute Phase 1 only. Run ALL Phase 1 validations and fix any failures. Only commit once every validation passes." --yes --dangerouslySkipPermissions
> claude -p "Read his-registry-buildout.md. Execute Phase 2 only. Run ALL Phase 2 validations and fix any failures. Only commit once every validation passes." --yes --dangerouslySkipPermissions
> claude -p "Read his-registry-buildout.md. Execute Phase 3 only. Run ALL Phase 3 validations and fix any failures. Only commit once every validation passes." --yes --dangerouslySkipPermissions
> claude -p "Read his-registry-buildout.md. Execute Phase 4 only. Run ALL Phase 4 validations and fix any failures. Only commit once every validation passes." --yes --dangerouslySkipPermissions
> claude -p "Read his-registry-buildout.md. Execute Phase 5 only. Run ALL Phase 5 validations and fix any failures. Only commit once every validation passes." --yes --dangerouslySkipPermissions
> # Phase 6 — interactive (requires live credentials):
> claude -p "Read his-registry-buildout.md. Execute Phase 6 only. Run ALL Phase 6 validations and fix any failures. Only commit once every validation passes."
> ```
>
> </details>

## Background & Motivation

The GC-Core ontology references HIS Registry codes (ROP3, ROG3, ROL3) throughout — on people groups in seed data, in the Joshua Project bridge, and in SPARQL queries. But these codes exist only as **flat literal values** stamped on entities. There is no ROP entity to navigate to, no hierarchy to traverse, and no way to query "all people groups in the Bantu People Cluster" or "all groups whose language belongs to the Niger-Congo family" without hitting an external API.

This buildout imports the HIS Registry of Peoples (ROP) into GraphDB as a SKOS-based classification graph, renames the HIS namespace from GC-owned URIs to a proper `data.global.church/his/` entity space, adds a linking property (`gc:hasPeopleClassification`) to connect people groups to the hierarchy, and provides SPARQL queries to exploit the new structure.

### Why ROP Is the Hub (Not Just Another Data Source)

HIS ROP is the **correlation layer** for the global missions data ecosystem. It's the Rosetta Stone that maps between identifier systems:

- **Joshua Project** PeopleID3 = ROP3 code
- **IMB** PGID references ROP3
- **peoplegroups.org** references ROP3
- **Wycliffe / SIL** references ROP3 via ROL (languages) cross-references
- **CPPI** (Church Planting Progress Indicators) references ROP3

Every future data bridge — IMB, Wycliffe, peoplegroups.org — will link through ROP3 as the common key. By importing ROP as a SKOS concept scheme now, we're building the **hub node** that all bridges connect to. When we later add IMB data, their people group entities get `gc:hasPeopleClassification` pointing to the same `<https://data.global.church/his/rop3/{code}>` entity that JP already links to. That single link makes IMB and JP data joinable without any direct IMB↔JP mapping.

```
                    ┌─── JP People Group (PGIC)
                    │      gc:hasPeopleClassification
                    │
HIS ROP3 Concept ◄──┼─── IMB People Group (future)
  (SKOS hub)        │      gc:hasPeopleClassification
                    │
                    └─── Org X Engagement Data (future)
                           gc:hasPeopleClassification
```

### Ontology Layering: Who Owns What

GC-Core does NOT define what a people group IS — HIS ROP owns that (identity/classification). GC-Core defines what missions organizations DO WITH people groups (engagement tracking). The layers:

1. **Identity/Classification** (HIS ROP) — "Somali" is code 109392, part of the Horn of Africa People Cluster, Somali Affinity Bloc. This is the SKOS concept scheme.
2. **Demographics/Status** (Joshua Project, IMB, etc.) — "Somali in USA" has population 150K, 0.5% evangelical, least-reached. These are PGIC-level entities from data authorities.
3. **Engagement/Coordination** (GC-Core) — Phase 2, strength Growing, two orgs committed, three active workers. This is what `gc:PeopleGroup` actually models.

`gc:PeopleGroup` is a PGIC-level engagement profile — not a redefinition of the people group concept. It links TO the HIS classification via `gc:hasPeopleClassification` and carries the engagement semantics that HIS/JP/IMB don't model.

### Design Decisions

1. **Namespace change**: The current `rop:`, `rog:`, `rol:` prefixes point to `https://ontology.global.church/his/{registry}#` — these were placeholders. Since HIS doesn't publish their own linked data URIs, we mint entity URIs under `https://data.global.church/his/` (data, not ontology) and keep property predicates in the `gc:` namespace. This follows the DBpedia pattern: we host linked data for an authority that doesn't publish it themselves.

2. **SKOS Concept Scheme**: ROP's 4-level hierarchy (ROP1 Affinity Bloc → ROP2 People Cluster → ROP2.5 Kinship Group → ROP3 People) maps naturally to `skos:ConceptScheme` with `skos:broader`/`skos:narrower` relationships.

3. **Named graph**: All HIS registry data lives in `<https://data.global.church/his-registries/>`, separate from org data and JP data.

4. **No flat code properties on people groups**: `gc:rop3Code`, `gc:rop25Code`, etc. are removed from the ontology. HIS owns these identifiers — they don't belong in the `gc:` namespace. The sole connection from a `gc:PeopleGroup` to HIS is `gc:hasPeopleClassification`, which links to a SKOS concept that carries `skos:notation` for the raw code. Queries that need the code add one triple pattern: `?rop3 skos:notation ?code`. The SKOS concepts themselves don't carry `gc:ropXCode` properties either — `skos:notation` is the standard way to attach codes to concepts.

5. **ROP first, ROG/ROL later**: ROG is essentially country codes (lightweight, can stay as literals). ROL delegates to ISO 639-3 (same). ROP has the hierarchical structure that unlocks the most value. ROG and ROL can be added as concept schemes in a follow-up.

### Architecture

```
IMB ArcGIS Open Data                    GraphDB (Railway)
─────────────────────                   ──────────────────
tblROP1 (Affinity Blocs)    ──┐
tblROP2 (People Clusters)   ──┤        <https://data.global.church/his-registries/>
tblROP2.5 (Kinship Groups)  ──┼──►  gc-his-bridge  ──►   SKOS hierarchy
tblROP3 (Peoples)            ──┤        (TypeScript)       + gc:hasPeopleClassification
pROP3GeoIndex (People×Country)┘                            links on JP entities
```

### New URI Patterns

| Entity Type | URI Pattern | Example |
|---|---|---|
| ROP Concept Scheme | `<https://data.global.church/his/rop>` | (singleton) |
| ROP1 Affinity Bloc | `<https://data.global.church/his/rop1/{code}>` | `.../his/rop1/10` |
| ROP2 People Cluster | `<https://data.global.church/his/rop2/{code}>` | `.../his/rop2/307` |
| ROP2.5 Kinship Group | `<https://data.global.church/his/rop25/{code}>` | `.../his/rop25/304200` |
| ROP3 People | `<https://data.global.church/his/rop3/{code}>` | `.../his/rop3/109392` |

### New Ontology Properties

| Property | Domain | Range | Purpose |
|---|---|---|---|
| `gc:hasPeopleClassification` | `gc:PeopleGroup` | `skos:Concept` | Links a people group to its ROP3 concept entity |

### Removed Ontology Properties

These are removed from `gc-core.ttl` because HIS owns the identifier concepts — they don't belong in the `gc:` namespace. The raw codes are accessible via `skos:notation` on the linked SKOS concept.

| Removed Property | Replacement |
|---|---|
| `gc:rop3Code` | `gc:hasPeopleClassification` → `skos:notation` |
| `gc:rop25Code` | `gc:hasPeopleClassification` → `skos:broader` → `skos:notation` |

---

## Phase 1: Ontology Updates — New Properties + Namespace Migration Plan

### Why

Before touching any bridge code, the ontology needs the `gc:hasPeopleClassification` property defined, and the SHACL shapes need to account for the new linking pattern. We also document the namespace migration plan for the `rop:`/`rog:`/`rol:` prefixes.

### Steps

1. **Add `gc:hasPeopleClassification` to `ontology/gc-core.ttl`**:

   Add this property definition in the people group section of the ontology (replacing the existing `gc:rop3Code` and `gc:rop25Code` property definitions):

   ```turtle
   gc:hasPeopleClassification a owl:ObjectProperty ;
     rdfs:label "has people classification"@en ;
     rdfs:comment "Links a PeopleGroup to its classification in the HIS Registry of Peoples (ROP) SKOS concept scheme. The linked SKOS concept carries the raw code via skos:notation and the hierarchy via skos:broader."@en ;
     rdfs:domain gc:PeopleGroup ;
     rdfs:range skos:Concept .
   ```

   **Remove** the existing `gc:rop3Code` and `gc:rop25Code` property definitions from the ontology. These are HIS identifiers and don't belong in the `gc:` namespace. The raw codes are accessible via `skos:notation` on the linked SKOS concepts.

2. **Add SKOS import to ontology prefixes** in `gc-core.ttl` (if not already present):

   Ensure these prefixes exist at the top of the file:
   ```turtle
   @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
   ```

   And add SKOS to the ontology imports if there's an `owl:imports` block.

3. **Update SHACL shapes in `ontology/gc-core.shacl.ttl`**:

   Add a property constraint to `PeopleGroupShape` for the new link (optional but typed):

   ```turtle
   sh:property [
     sh:path gc:hasPeopleClassification ;
     sh:class skos:Concept ;
     sh:maxCount 1 ;
     sh:name "people classification" ;
     sh:message "hasPeopleClassification must link to a skos:Concept." ;
   ] ;
   ```

   Also add a new shape for validating HIS ROP Concepts that will be loaded later:

   ```turtle
   :HISConceptShape a sh:NodeShape ;
     sh:targetClass skos:Concept ;
     rdfs:label "HIS Registry Concept Shape"@en ;
     sh:property [
       sh:path skos:prefLabel ;
       sh:minCount 1 ;
       sh:datatype xsd:string ;
       sh:name "preferred label" ;
       sh:message "Every HIS concept must have at least one skos:prefLabel." ;
     ] ;
     sh:property [
       sh:path skos:inScheme ;
       sh:minCount 1 ;
       sh:name "in scheme" ;
       sh:message "Every HIS concept must belong to a skos:ConceptScheme." ;
     ] .
   ```

4. **Create `docs/his-namespace-migration.md`** documenting the namespace change:

   ```markdown
   # HIS Namespace Migration

   ## Previous (Placeholder)
   - `rop:` → `<https://ontology.global.church/his/rop#>` (used as property prefix)
   - `rog:` → `<https://ontology.global.church/his/rog#>` (used as property prefix)
   - `rol:` → `<https://ontology.global.church/his/rol#>` (used as property prefix)
   - Flat code properties: `gc:rop3Code`, `gc:rop25Code` on PeopleGroup entities

   ## New (Entity URIs + SKOS)
   - HIS entities live under `<https://data.global.church/his/>` (data namespace)
   - ROP hierarchy: `<https://data.global.church/his/rop3/{code}>`, etc.
   - SKOS concepts carry codes via `skos:notation` (standard vocabulary)
   - No flat code properties in gc: namespace — HIS owns these identifiers

   ## Migration Path
   The JP bridge (gc-jp-bridge) will be updated in Phase 3 to:
   1. Drop `rop:`, `rog:`, `rol:` as property prefixes entirely
   2. Drop all flat code properties (`rop:rop3Code`, `gc:rop3Code`, etc.)
   3. Add `gc:hasPeopleClassification` as the sole link to HIS entities

   The ontology (gc-core.ttl) will:
   1. Remove `gc:rop3Code` and `gc:rop25Code` property definitions
   2. Add `gc:hasPeopleClassification` (ObjectProperty → skos:Concept)

   ## Query Pattern
   To get a raw ROP3 code from a people group:
   ```sparql
   ?pg gc:hasPeopleClassification ?rop3 .
   ?rop3 skos:notation ?code .
   ```
   ```

### Phase 1 Validation Gate

**CRITICAL: Run ALL of these validations. Fix any failures. Do NOT commit until every check passes.**

```bash
# V1.1 — New property exists in ontology
echo "=== V1.1: gc:hasPeopleClassification defined ==="
grep -c "gc:hasPeopleClassification" ontology/gc-core.ttl | xargs -I{} test {} -ge 1 && echo "✅ Property defined" || echo "❌ Property not found in gc-core.ttl"

# V1.2 — SKOS prefix exists in ontology
echo "=== V1.2: SKOS prefix in ontology ==="
grep -q "skos:" ontology/gc-core.ttl && echo "✅ SKOS prefix present" || echo "❌ SKOS prefix missing"

# V1.3 — SHACL has hasPeopleClassification constraint
echo "=== V1.3: SHACL shape for hasPeopleClassification ==="
grep -q "gc:hasPeopleClassification" ontology/gc-core.shacl.ttl && echo "✅ SHACL constraint present" || echo "❌ SHACL constraint missing"

# V1.4 — HISConceptShape exists in SHACL
echo "=== V1.4: HISConceptShape in SHACL ==="
grep -q "HISConceptShape" ontology/gc-core.shacl.ttl && echo "✅ HISConceptShape present" || echo "❌ HISConceptShape missing"

# V1.5 — Migration doc exists
echo "=== V1.5: Namespace migration doc ==="
test -f docs/his-namespace-migration.md && echo "✅ Migration doc exists" || echo "❌ Migration doc missing"

# V1.6 — Ontology is valid Turtle (parse check)
echo "=== V1.6: Turtle parse check ==="
npx @frogcat/ttl2jsonld ontology/gc-core.ttl > /dev/null 2>&1 && echo "✅ gc-core.ttl parses" || {
  # Fallback: use rapper if available, or basic syntax check
  python3 -c "
import re, sys
with open('ontology/gc-core.ttl') as f:
    content = f.read()
# Check balanced brackets and semicolons
opens = content.count('{') + content.count('[')
closes = content.count('}') + content.count(']')
if abs(opens - closes) > 2:
    print('❌ Possible bracket mismatch')
    sys.exit(1)
print('✅ Basic syntax check passed (install a Turtle parser for full validation)')
"
}

# V1.7 — SHACL is valid Turtle
echo "=== V1.7: SHACL parse check ==="
npx @frogcat/ttl2jsonld ontology/gc-core.shacl.ttl > /dev/null 2>&1 && echo "✅ gc-core.shacl.ttl parses" || {
  python3 -c "
with open('ontology/gc-core.shacl.ttl') as f:
    content = f.read()
opens = content.count('{') + content.count('[')
closes = content.count('}') + content.count(']')
if abs(opens - closes) > 2:
    print('❌ Possible bracket mismatch'); exit(1)
print('✅ Basic syntax check passed')
"
}
```

**Expected result: ALL checks show ✅. Zero ❌. Then commit:**
```bash
git add -A && git commit -m "Phase 1: add gc:hasPeopleClassification property, HISConceptShape, namespace migration plan"
```

---

## Phase 2: HIS Bridge Package — Fetch + Convert ROP to RDF

### Why

This is the core data pipeline: fetch ROP code tables from IMB's ArcGIS Open Data portal and convert them to SKOS-structured RDF Turtle. Modeled after the existing `gc-jp-bridge` package.

### Steps

1. **Create `packages/gc-his-bridge/`** as a new pnpm workspace package:

   ```
   packages/gc-his-bridge/
   ├── package.json
   ├── tsconfig.json
   └── src/
       ├── his-client.ts     # ArcGIS API client
       ├── rop-to-rdf.ts     # ROP → Turtle converter
       ├── sync.ts           # Orchestrator (fetch → convert → load)
       └── types.ts          # TypeScript interfaces
   ```

   `package.json`:
   ```json
   {
     "name": "@gc-core/his-bridge",
     "version": "0.1.0",
     "type": "module",
     "scripts": {
       "build": "tsc",
       "typecheck": "tsc --noEmit",
       "sync": "node dist/sync.js"
     },
     "bin": {
       "gc-his-sync": "./dist/sync.js"
     },
     "dependencies": {
       "@gc-core/sparql": "workspace:*"
     },
     "devDependencies": {
       "typescript": "^5.4.0",
       "@types/node": "^20.0.0"
     }
   }
   ```

2. **Add to `pnpm-workspace.yaml`** — Ensure `packages/gc-his-bridge` is included.

3. **Implement `src/types.ts`** — Define TypeScript interfaces for each ROP table:

   ```typescript
   /** ArcGIS Feature response wrapper */
   export interface ArcGISFeatureResponse<T> {
     features: Array<{ attributes: T }>;
     exceededTransferLimit?: boolean;
   }

   /** tblROP1 — Affinity Blocs */
   export interface ROP1AffinityBloc {
     ROP1: number;           // e.g., 10
     AffinityBloc: string;   // e.g., "Arab World"
   }

   /** tblROP2 — People Clusters */
   export interface ROP2PeopleCluster {
     ROP2: number;           // e.g., 307
     PeopleCluster: string;  // e.g., "Somali"
     ROP1: number;           // parent Affinity Bloc code
   }

   /** tblROP2.5 — Kinship Groups */
   export interface ROP25KinshipGroup {
     ROP25: string;          // e.g., "304200"
     KinshipGroup: string;   // e.g., "Bedouin, Arabian"
     ROP2: number;           // parent People Cluster code
   }

   /** tblROP3 — Peoples */
   export interface ROP3People {
     ROP3: number;            // e.g., 109392
     PeopleName: string;      // recommended reference name
     ROP25: string;           // parent Kinship Group code
     ROP2: number;            // parent People Cluster code (legacy/convenience)
     ROP1: number;            // parent Affinity Bloc code (legacy/convenience)
   }

   /** pROP3GeoIndex — People × Country linking table */
   export interface ROP3GeoIndex {
     ROP3: number;
     ROG3: string;            // country code
     PeopleName?: string;     // name in that country context
   }
   ```

   **IMPORTANT**: The exact field names in the ArcGIS API may differ slightly from the above (e.g., `Rop3` vs `ROP3`, `Affinity_Bloc` vs `AffinityBloc`). The `his-client.ts` must query the service metadata first to discover actual field names. See step 4.

4. **Implement `src/his-client.ts`** — ArcGIS REST API client:

   The ROP data is hosted on IMB's ArcGIS Open Data portal. The FeatureServer URL base is:
   ```
   https://services1.arcgis.com/p9DmFAkiMCFmaJ1S/ArcGIS/rest/services/ROP_Registry_of_Peoples/FeatureServer
   ```

   **CRITICAL — discover the service first**: Before fetching data, hit the FeatureServer root URL with `?f=json` to discover:
   - The layer/table indices (which number = which table)
   - The exact field names per layer

   ```
   GET {featureServerUrl}?f=json
   → lists layers[] and tables[] with id + name
   GET {featureServerUrl}/{layerId}?f=json
   → lists fields[] with name, alias, type
   ```

   Then query each table:
   ```
   GET {featureServerUrl}/{layerId}/query?where=1=1&outFields=*&f=json&resultRecordCount=2000&resultOffset=0
   ```

   **Pagination**: ArcGIS limits to ~2000 records per request. Use `resultOffset` to paginate. The response includes `exceededTransferLimit: true` if more records exist.

   **Rate limiting**: Add a 300ms delay between requests.

   **Caching**: Cache raw JSON responses per table to `data/cache/his/` (same pattern as JP bridge). File names: `rop1.json`, `rop2.json`, `rop25.json`, `rop3.json`, `rop3-geoindex.json`.

   **Fallback**: If the FeatureServer URL doesn't work (the exact service name may vary), try the ArcGIS Hub download API:
   ```
   https://hub.arcgis.com/api/v3/datasets/{datasetId}/downloads/data?format=geojson&spatialRefId=4326&where=1=1
   ```
   Dataset IDs for ROP tables can be discovered from `https://go-imb.opendata.arcgis.com/` search results.

   **If discovery shows different field names than the types.ts interfaces, update types.ts to match.** The interfaces are educated guesses — the ArcGIS schema is the source of truth.

5. **Implement `src/rop-to-rdf.ts`** — Convert cached JSON to SKOS Turtle:

   Prefixes:
   ```turtle
   @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
   @prefix gc:   <https://ontology.global.church/core#> .
   @prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
   @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
   @prefix dcterms: <http://purl.org/dc/terms/> .
   ```

   **Concept Scheme** (top-level container):
   ```turtle
   <https://data.global.church/his/rop> a skos:ConceptScheme ;
     skos:prefLabel "HIS Registry of Peoples"@en ;
     dcterms:publisher "HIS Registries (hisregistries.org)" ;
     dcterms:description "Four-level classification of the world's peoples: Affinity Bloc → People Cluster → Kinship Group → People."@en .
   ```

   **ROP1 Affinity Bloc** (e.g., code 10):
   ```turtle
   <https://data.global.church/his/rop1/10> a skos:Concept ;
     skos:inScheme <https://data.global.church/his/rop> ;
     skos:prefLabel "Arab World"@en ;
     skos:topConceptOf <https://data.global.church/his/rop> ;
     skos:notation "10" .
   ```

   **ROP2 People Cluster** (e.g., code 307):
   ```turtle
   <https://data.global.church/his/rop2/307> a skos:Concept ;
     skos:inScheme <https://data.global.church/his/rop> ;
     skos:prefLabel "Somali"@en ;
     skos:broader <https://data.global.church/his/rop1/10> ;
     skos:notation "307" .
   ```

   **ROP2.5 Kinship Group** (e.g., code 304200):
   ```turtle
   <https://data.global.church/his/rop25/304200> a skos:Concept ;
     skos:inScheme <https://data.global.church/his/rop> ;
     skos:prefLabel "Bedouin, Arabian"@en ;
     skos:broader <https://data.global.church/his/rop2/304> ;
     skos:notation "304200" .
   ```

   **ROP3 People** (e.g., code 109392):
   ```turtle
   <https://data.global.church/his/rop3/109392> a skos:Concept ;
     skos:inScheme <https://data.global.church/his/rop> ;
     skos:prefLabel "Somali"@en ;
     skos:broader <https://data.global.church/his/rop25/304200> ;
     skos:notation "109392" .
   ```

   Also generate `skos:narrower` inverse links for each `skos:broader`.

   The ROP3 GeoIndex table is NOT converted to RDF in this phase — it's used in Phase 3 to generate `gc:hasPeopleClassification` links from JP people groups.

   Output file: `data/cache/his/his-rop.ttl`

6. **Implement `src/sync.ts`** — Orchestrator:

   Follow the same 4-step pattern as the JP bridge sync (`packages/gc-jp-bridge/src/sync.ts`):

   - Step 1: Discover service metadata (field names, layer indices)
   - Step 2: Fetch all ROP tables (with caching + pagination)
   - Step 3: Convert to RDF Turtle
   - Step 4: Load into GraphDB (named graph `<https://data.global.church/his-registries/>`)

   For Step 4, use the same GraphDB HTTP loading approach as the JP bridge — POST Turtle to the statements endpoint with the `context` parameter set to the named graph URI. Batch into chunks if the file is large.

   Environment variables:
   ```bash
   GRAPHDB_URL        # Optional: GraphDB base URL
   GRAPHDB_REPO       # Optional: Repository name (default: gc-core)
   GC_API_KEY         # Optional: API key for authenticated GraphDB requests
   HIS_CACHE_DIR      # Optional: Cache directory (default: data/cache/his/)
   ```

### Phase 2 Validation Gate

**CRITICAL: Run ALL of these validations. Fix any failures. Do NOT commit until every check passes.**

```bash
# V2.1 — Package structure exists
echo "=== V2.1: Package structure ==="
for f in packages/gc-his-bridge/package.json packages/gc-his-bridge/tsconfig.json packages/gc-his-bridge/src/his-client.ts packages/gc-his-bridge/src/rop-to-rdf.ts packages/gc-his-bridge/src/sync.ts packages/gc-his-bridge/src/types.ts; do
  test -f "$f" && echo "✅ $f" || echo "❌ MISSING: $f"
done

# V2.2 — Package is in pnpm workspace
echo "=== V2.2: pnpm workspace includes his-bridge ==="
grep -q "gc-his-bridge" pnpm-workspace.yaml && echo "✅ In workspace" || echo "❌ Not in workspace"

# V2.3 — TypeScript compiles
echo "=== V2.3: TypeScript compilation ==="
cd packages/gc-his-bridge && pnpm install && pnpm exec tsc --noEmit && echo "✅ TypeScript compiles" || echo "❌ TypeScript errors"
cd ../..

# V2.4 — Types file defines all 5 interfaces
echo "=== V2.4: Type interfaces ==="
for iface in ROP1AffinityBloc ROP2PeopleCluster ROP25KinshipGroup ROP3People ROP3GeoIndex; do
  grep -q "interface $iface" packages/gc-his-bridge/src/types.ts && echo "✅ $iface" || echo "❌ MISSING: $iface"
done

# V2.5 — RDF converter generates SKOS structure (with skos:notation, NOT gc:ropXCode)
echo "=== V2.5: SKOS patterns in rop-to-rdf.ts ==="
for pattern in "skos:ConceptScheme" "skos:Concept" "skos:broader" "skos:prefLabel" "skos:inScheme" "skos:notation"; do
  grep -q "$pattern" packages/gc-his-bridge/src/rop-to-rdf.ts && echo "✅ $pattern" || echo "❌ MISSING: $pattern"
done

# V2.5b — No gc:ropXCode properties in converter output
echo "=== V2.5b: No gc:ropXCode in converter ==="
grep -rn "gc:rop[0-9]" packages/gc-his-bridge/src/rop-to-rdf.ts && echo "❌ Found gc:ropXCode properties — use skos:notation instead" || echo "✅ No gc:ropXCode properties"

# V2.6 — Sync orchestrator has all 4 steps
echo "=== V2.6: Sync steps ==="
grep -q "data.global.church/his" packages/gc-his-bridge/src/sync.ts && echo "✅ Named graph URI" || echo "❌ Named graph URI missing"
grep -q "his-registries" packages/gc-his-bridge/src/sync.ts && echo "✅ his-registries graph" || echo "❌ his-registries graph missing"

# V2.7 — No references to old ontology.global.church/his/ namespace as entity URIs
echo "=== V2.7: No old namespace in new code ==="
grep -r "ontology.global.church/his/" packages/gc-his-bridge/src/ && echo "❌ Found old namespace references" || echo "✅ No old namespace references"

# V2.8 — Uses data.global.church/his/ for entity URIs
echo "=== V2.8: Correct entity namespace ==="
grep -q "data.global.church/his/" packages/gc-his-bridge/src/rop-to-rdf.ts && echo "✅ Correct entity namespace" || echo "❌ Wrong entity namespace"
```

**Expected result: ALL checks show ✅. Zero ❌. Then commit:**
```bash
git add -A && git commit -m "Phase 2: add gc-his-bridge package — ArcGIS client, ROP-to-SKOS converter, sync orchestrator"
```

---

## Phase 3: JP Bridge Migration — Namespace Cleanup + Classification Links

### Why

The JP bridge currently writes `rop:rop3Code`, `rog:rog3Code`, `rol:rol3Code` using the old placeholder namespaces. These need to migrate to `gc:` namespace properties, and the bridge needs to generate `gc:hasPeopleClassification` links pointing to the HIS ROP3 entities created in Phase 2.

### Steps

1. **Update `packages/gc-jp-bridge/src/jp-to-rdf.ts`**:

   **Remove** the old HIS namespace prefixes:
   ```typescript
   // REMOVE these lines:
   // @prefix rop:  <https://ontology.global.church/his/rop#> .
   // @prefix rog:  <https://ontology.global.church/his/rog#> .
   // @prefix rol:  <https://ontology.global.church/his/rol#> .
   ```

   **Remove** all `rop:rop3Code`, `rop:rop1Code`, `rop:rop2Code`, `rog:rog3Code`, `rol:rol3Code` field mappings entirely. These flat code properties are being eliminated — HIS owns these identifiers.

   **Replace** with a single `gc:hasPeopleClassification` link on every JP people group that has a ROP3 code:
   ```typescript
   // BEFORE:
   // triples.push(`  ; rop:rop3Code ${pg.ROP3}`);
   // triples.push(`  ; rop:rop1Code ${pg.PeopleID1}`);
   // triples.push(`  ; rop:rop2Code ${pg.PeopleID2}`);
   // triples.push(`  ; rog:rog3Code "${escapeTurtle(pg.ROG3)}"`);
   // triples.push(`  ; rol:rol3Code "${escapeTurtle(pg.ROL3)}"`);

   // AFTER — single link replaces all flat codes:
   if (pg.ROP3) {
     triples.push(`  ; gc:hasPeopleClassification <https://data.global.church/his/rop3/${pg.ROP3}>`);
   }
   ```

   **Note**: ROG3 (country) and ROL3 (language) codes are not modeled as properties on PeopleGroup at all. Country context is already captured in the JP entity URI (`/jp/pg/{ROP3}-{ROG3}`), and language data can be added later when ROL becomes its own SKOS concept scheme. For now, queries that need country context can parse it from the URI or use JP-specific properties.

2. **Remove stale HIS code properties from `ontology/gc-core.ttl`**:

   Delete the existing `gc:rop3Code` and `gc:rop25Code` property definitions from the ontology. Do NOT add `gc:rop1Code`, `gc:rop2Code`, `gc:rog3Code`, or `gc:rol3Code` — none of these belong in the `gc:` namespace. The sole connection from PeopleGroup to HIS is `gc:hasPeopleClassification` (added in Phase 1).

3. **Update all SPARQL queries** in `packages/gc-sparql/src/queries/` that reference old prefixes:

   Search all `.rq` files for `rop:`, `rog:`, `rol:` prefix usage and **remove** them entirely. Also remove any `gc:rop3Code`, `gc:rop25Code` references. Replace with `gc:hasPeopleClassification` + `skos:notation` pattern where needed:

   ```sparql
   # REMOVE these prefixes:
   # PREFIX rop: <https://ontology.global.church/his/rop#>
   # PREFIX rog: <https://ontology.global.church/his/rog#>
   # PREFIX rol: <https://ontology.global.church/his/rol#>

   # REPLACE patterns like:
   #   ?pg gc:rop3Code ?code .
   # WITH:
   #   ?pg gc:hasPeopleClassification ?rop3concept .
   #   ?rop3concept skos:notation ?code .
   ```

4. **Update the linker** (`packages/gc-jp-bridge/src/linker.ts`) — The linker currently matches seed data to JP entities using `gc:rop3Code`. Since that property is being removed, the linker needs to match via `gc:hasPeopleClassification` links instead — both the JP entity and the seed entity will point to the same `<https://data.global.church/his/rop3/{code}>` SKOS concept, which serves as the join key. Also verify no references to the old `rop:` namespace remain.

### Phase 3 Validation Gate

**CRITICAL: Run ALL of these validations. Fix any failures. Do NOT commit until every check passes.**

```bash
# V3.1 — No old HIS namespace references in JP bridge
echo "=== V3.1: No old namespace in JP bridge ==="
grep -r "ontology.global.church/his/" packages/gc-jp-bridge/src/ && echo "❌ Found old namespace" || echo "✅ Clean"

# V3.2 — No rop:/rog:/rol: prefix declarations in JP bridge
echo "=== V3.2: No old prefix declarations ==="
grep -rn "@prefix rop:\|@prefix rog:\|@prefix rol:" packages/gc-jp-bridge/src/ && echo "❌ Found old prefixes" || echo "✅ Clean"

# V3.3 — hasPeopleClassification is generated
echo "=== V3.3: hasPeopleClassification in JP RDF output ==="
grep -q "hasPeopleClassification" packages/gc-jp-bridge/src/jp-to-rdf.ts && echo "✅ Link generated" || echo "❌ Link missing"

# V3.4 — data.global.church/his/rop3/ URI pattern used
echo "=== V3.4: Correct HIS entity URI in JP bridge ==="
grep -q "data.global.church/his/rop3/" packages/gc-jp-bridge/src/jp-to-rdf.ts && echo "✅ Correct URI" || echo "❌ Wrong URI"

# V3.5 — JP bridge TypeScript compiles
echo "=== V3.5: JP bridge compilation ==="
cd packages/gc-jp-bridge && pnpm install && pnpm exec tsc --noEmit && echo "✅ Compiles" || echo "❌ Errors"
cd ../..

# V3.6 — No old rop:/rog:/rol: prefixes in SPARQL queries
echo "=== V3.6: No old prefixes in SPARQL queries ==="
grep -rn "PREFIX rop:\|PREFIX rog:\|PREFIX rol:" packages/gc-sparql/src/queries/ && echo "❌ Found old prefixes in queries" || echo "✅ Clean"

# V3.7 — No stale rop:rop3Code usage in SPARQL queries
echo "=== V3.7: No old HIS code properties in queries ==="
grep -rn "rop:rop3Code\|rog:rog3Code\|rol:rol3Code\|gc:rop3Code\|gc:rop1Code\|gc:rop2Code\|gc:rop25Code\|gc:rog3Code\|gc:rol3Code" packages/gc-sparql/src/queries/ && echo "❌ Found stale HIS code property references" || echo "✅ Clean"

# V3.8 — Old gc:rop3Code and gc:rop25Code removed from ontology
echo "=== V3.8: No flat HIS code properties in ontology ==="
grep -n "gc:rop3Code\|gc:rop25Code\|gc:rop1Code\|gc:rop2Code\|gc:rog3Code\|gc:rol3Code" ontology/gc-core.ttl && echo "❌ Found flat HIS code properties — these should be removed" || echo "✅ No flat HIS code properties"

# V3.9 — Ontology still parses
echo "=== V3.9: Ontology parse check ==="
python3 -c "
with open('ontology/gc-core.ttl') as f: content = f.read()
opens = content.count('['); closes = content.count(']')
if abs(opens - closes) > 2: print('❌ Bracket mismatch'); exit(1)
print('✅ Basic parse OK')
"
```

**Expected result: ALL checks show ✅. Zero ❌. Then commit:**
```bash
git add -A && git commit -m "Phase 3: migrate JP bridge from rop:/rog:/rol: to gc: namespace, add hasPeopleClassification links"
```

---

## Phase 4: SPARQL Queries for Hierarchy Traversal

### Why

The whole point of importing ROP as a graph (not flat codes) is enabling hierarchy queries. This phase adds SPARQL queries that exploit the SKOS structure.

### Steps

1. **Create new SPARQL query files** in `packages/gc-sparql/src/queries/`:

   **`his-affinity-bloc-summary.rq`** — People groups per Affinity Bloc with engagement status:
   ```sparql
   PREFIX gc:   <https://ontology.global.church/core#>
   PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

   SELECT ?blocName (COUNT(DISTINCT ?rop3) AS ?totalPeoples) (COUNT(DISTINCT ?engaged) AS ?engagedPeoples)
   WHERE {
     GRAPH <https://data.global.church/his-registries/> {
       ?bloc skos:topConceptOf <https://data.global.church/his/rop> ;
             skos:prefLabel ?blocName .
       ?cluster skos:broader ?bloc .
       ?kinship skos:broader ?cluster .
       ?rop3 skos:broader ?kinship .
     }
     OPTIONAL {
       ?pg gc:hasPeopleClassification ?rop3 .
       ?result gc:resultForPeopleGroup ?pg .
       BIND(?pg AS ?engaged)
     }
   }
   GROUP BY ?blocName
   ORDER BY DESC(?totalPeoples)
   ```

   **`his-people-cluster-drilldown.rq`** — All peoples in a given People Cluster:
   ```sparql
   PREFIX gc:   <https://ontology.global.church/core#>
   PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
   PREFIX jp:   <https://ontology.global.church/joshuaproject#>

   SELECT ?peopleName ?rop3Code ?population ?jpScale ?phaseValue
   WHERE {
     GRAPH <https://data.global.church/his-registries/> {
       ?cluster skos:prefLabel {{clusterName}} .
       ?kinship skos:broader ?cluster .
       ?rop3concept skos:broader ?kinship ;
                    skos:prefLabel ?peopleName ;
                    skos:notation ?rop3Code .
     }
     OPTIONAL {
       ?pg gc:hasPeopleClassification ?rop3concept .
       GRAPH <https://data.global.church/joshua-project/> {
         ?pg jp:population ?population ;
             jp:jpScale ?jpScale .
       }
       OPTIONAL {
         ?result gc:resultForPeopleGroup ?pg ;
                jp:phaseValue ?phaseValue .
       }
     }
   }
   ORDER BY ?peopleName
   ```

   **`his-unengaged-by-bloc.rq`** — Unengaged peoples grouped by Affinity Bloc:
   ```sparql
   PREFIX gc:   <https://ontology.global.church/core#>
   PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
   PREFIX jp:   <https://ontology.global.church/joshuaproject#>

   SELECT ?blocName ?clusterName ?peopleName ?population
   WHERE {
     GRAPH <https://data.global.church/his-registries/> {
       ?bloc skos:topConceptOf <https://data.global.church/his/rop> ;
             skos:prefLabel ?blocName .
       ?cluster skos:broader ?bloc ;
                skos:prefLabel ?clusterName .
       ?kinship skos:broader ?cluster .
       ?rop3concept skos:broader ?kinship ;
                    skos:prefLabel ?peopleName .
     }
     ?pg gc:hasPeopleClassification ?rop3concept .
     GRAPH <https://data.global.church/joshua-project/> {
       ?pg jp:population ?population ;
           jp:leastReached "true"^^xsd:boolean .
     }
     FILTER NOT EXISTS {
       ?result gc:resultForPeopleGroup ?pg .
     }
   }
   ORDER BY ?blocName ?clusterName DESC(?population)
   ```

   **`his-hierarchy-path.rq`** — Given a people group, return its full classification path:
   ```sparql
   PREFIX gc:   <https://ontology.global.church/core#>
   PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

   SELECT ?peopleName ?kinshipName ?clusterName ?blocName
   WHERE {
     GRAPH <https://data.global.church/his-registries/> {
       {{rop3Uri}} skos:prefLabel ?peopleName ;
                   skos:broader ?kinship .
       ?kinship skos:prefLabel ?kinshipName ;
                skos:broader ?cluster .
       ?cluster skos:prefLabel ?clusterName ;
                skos:broader ?bloc .
       ?bloc skos:prefLabel ?blocName ;
             skos:topConceptOf <https://data.global.church/his/rop> .
     }
   }
   ```

2. **Add query loader functions** to `packages/gc-sparql/src/index.ts`:

   Add exports for the new queries: `getAffinityBlocSummary()`, `getPeopleClusterDrilldown(clusterName)`, `getUnengagedByBloc()`, `getHierarchyPath(rop3Uri)`.

3. **Update the AI agent context** in `packages/gc-agent/` — Add few-shot examples so the natural language agent can answer:
   - "How many people groups are in the Arab World affinity bloc?"
   - "Show me all peoples in the Somali cluster"
   - "What's the classification path for the Burmese?"
   - "Which affinity blocs have the most unengaged peoples?"

### Phase 4 Validation Gate

**CRITICAL: Run ALL of these validations. Fix any failures. Do NOT commit until every check passes.**

```bash
# V4.1 — All new query files exist
echo "=== V4.1: Query files exist ==="
for f in his-affinity-bloc-summary his-people-cluster-drilldown his-unengaged-by-bloc his-hierarchy-path; do
  test -f "packages/gc-sparql/src/queries/$f.rq" && echo "✅ $f.rq" || echo "❌ MISSING: $f.rq"
done

# V4.2 — All new queries are valid SPARQL (have SELECT + PREFIX)
echo "=== V4.2: SPARQL syntax check ==="
for f in packages/gc-sparql/src/queries/his-*.rq; do
  if grep -q "SELECT\|CONSTRUCT\|ASK" "$f" && grep -q "PREFIX" "$f"; then
    echo "✅ $(basename $f) has SELECT + PREFIX"
  else
    echo "❌ $(basename $f) may be malformed"
  fi
done

# V4.3 — Queries reference the HIS named graph
echo "=== V4.3: Named graph references ==="
for f in packages/gc-sparql/src/queries/his-*.rq; do
  grep -q "his-registries" "$f" && echo "✅ $(basename $f) uses his-registries graph" || echo "❌ $(basename $f) missing graph reference"
done

# V4.4 — Queries use SKOS vocabulary
echo "=== V4.4: SKOS usage ==="
for f in packages/gc-sparql/src/queries/his-*.rq; do
  grep -q "skos:" "$f" && echo "✅ $(basename $f) uses SKOS" || echo "❌ $(basename $f) missing SKOS"
done

# V4.5 — Query loader exports new functions
echo "=== V4.5: Query loader exports ==="
for fn in "AffinityBlocSummary\|affinityBlocSummary" "PeopleClusterDrilldown\|peopleClusterDrilldown" "UnengagedByBloc\|unengagedByBloc" "HierarchyPath\|hierarchyPath"; do
  grep -q "$fn" packages/gc-sparql/src/index.ts && echo "✅ $fn exported" || echo "❌ $fn not exported"
done

# V4.6 — No old namespace references in new queries
echo "=== V4.6: No old namespaces ==="
grep -rn "ontology.global.church/his/" packages/gc-sparql/src/queries/his-*.rq && echo "❌ Found old namespace" || echo "✅ Clean"

# V4.7 — gc-sparql TypeScript compiles
echo "=== V4.7: gc-sparql compilation ==="
cd packages/gc-sparql && pnpm exec tsc --noEmit && echo "✅ Compiles" || echo "❌ Errors"
cd ../..
```

**Expected result: ALL checks show ✅. Zero ❌. Then commit:**
```bash
git add -A && git commit -m "Phase 4: add SPARQL queries for ROP hierarchy traversal — bloc summary, cluster drilldown, unengaged analysis"
```

---

## Phase 5: Seed Data + End-to-End Validation

### Why

The previous phases built the infrastructure. This phase proves it works end-to-end with representative data: a small hand-crafted ROP subset in the seed data, `gc:hasPeopleClassification` links on the Denver test people groups, and SPARQL queries that return correct results against a local GraphDB instance.

### Steps

1. **Create `data/seed/his-rop-seed.ttl`** — A small representative slice of the ROP hierarchy:

   Include at least:
   - 2 Affinity Blocs (e.g., "Horn of Africa Peoples", "South Asian Peoples")
   - 3 People Clusters (e.g., "Somali", "Amhara", "Nepali/Pahari")
   - 3 Kinship Groups
   - 6 ROP3 Peoples (matching the Denver seed data people groups: Somali 109392, Amhara 100293, Burmese 107775, Nepali 107204, plus 2 additional to show hierarchy)

   Follow the exact Turtle patterns from Phase 2 (SKOS Concept Scheme + broader/narrower).

   The named graph for this seed data is `<https://data.global.church/his-registries/>`.

2. **Update `data/seed/denver-churches.ttl`** — Replace flat HIS code properties with `gc:hasPeopleClassification` links:

   **Remove** all `gc:rop3Code`, `gc:rop25Code`, `gc:rop3byCountryCode`, `gc:jpPeopleId` flat properties from the Denver people group entities (these are HIS/JP identifiers, not GC-Core properties).

   **Add** `gc:hasPeopleClassification` links:
   ```turtle
   :pg-somali-us gc:hasPeopleClassification <https://data.global.church/his/rop3/109392> .
   :pg-amhara-us gc:hasPeopleClassification <https://data.global.church/his/rop3/100293> .
   :pg-burmese-us gc:hasPeopleClassification <https://data.global.church/his/rop3/107775> .
   :pg-nepali-us gc:hasPeopleClassification <https://data.global.church/his/rop3/107204> .
   ```

   The raw ROP3 code is now accessible by following the link to the SKOS concept and reading `skos:notation`.

3. **Update GraphDB init scripts** — Modify `apps/graphdb/init/load-seed-data.sh` (or equivalent) to also load `his-rop-seed.ttl` into the `his-registries` named graph.

4. **Write an end-to-end validation script** at `scripts/validate-his.sh`:

   This script:
   - Starts GraphDB locally (via docker compose)
   - Waits for it to be ready
   - Loads the ontology, seed data, and HIS seed data
   - Runs each HIS SPARQL query against the local instance
   - Validates that results are non-empty and structurally correct
   - Reports pass/fail

### Phase 5 Validation Gate

**CRITICAL: Run ALL of these validations. Fix any failures. Do NOT commit until every check passes.**

```bash
# V5.1 — HIS seed data file exists
echo "=== V5.1: HIS seed data ==="
test -f data/seed/his-rop-seed.ttl && echo "✅ Seed file exists" || echo "❌ Seed file missing"

# V5.2 — Seed data contains SKOS structure
echo "=== V5.2: SKOS in seed data ==="
for pattern in "skos:ConceptScheme" "skos:Concept" "skos:broader" "skos:prefLabel" "skos:inScheme" "skos:topConceptOf"; do
  grep -q "$pattern" data/seed/his-rop-seed.ttl && echo "✅ $pattern" || echo "❌ MISSING: $pattern"
done

# V5.3 — Seed data has correct named graph URI
echo "=== V5.3: Named graph reference ==="
grep -q "data.global.church/his" data/seed/his-rop-seed.ttl && echo "✅ Correct namespace" || echo "⚠️  Namespace not in file (may be set at load time)"

# V5.4 — All 4 ROP levels present in seed
echo "=== V5.4: All hierarchy levels ==="
grep -q "data.global.church/his/rop1/" data/seed/his-rop-seed.ttl && echo "✅ ROP1 entities" || echo "❌ ROP1 missing"
grep -q "data.global.church/his/rop2/" data/seed/his-rop-seed.ttl && echo "✅ ROP2 entities" || echo "❌ ROP2 missing"
grep -q "data.global.church/his/rop25/" data/seed/his-rop-seed.ttl && echo "✅ ROP2.5 entities" || echo "❌ ROP2.5 missing"
grep -q "data.global.church/his/rop3/" data/seed/his-rop-seed.ttl && echo "✅ ROP3 entities" || echo "❌ ROP3 missing"

# V5.5 — Denver seed data has classification links
echo "=== V5.5: Classification links in Denver data ==="
grep -c "hasPeopleClassification" data/seed/denver-churches.ttl | xargs -I{} test {} -ge 4 && echo "✅ At least 4 classification links" || echo "❌ Missing classification links"

# V5.6 — Seed data parses as valid Turtle
echo "=== V5.6: Turtle parse ==="
python3 -c "
with open('data/seed/his-rop-seed.ttl') as f: content = f.read()
opens = content.count('['); closes = content.count(']')
if abs(opens - closes) > 2: print('❌ Bracket mismatch'); exit(1)
# Check that every URI is closed
import re
unclosed = re.findall(r'<[^>]{200,}', content)
if unclosed: print(f'❌ Possibly unclosed URI: {unclosed[0][:80]}...'); exit(1)
print('✅ Basic parse OK')
"

# V5.7 — Denver seed data still parses
echo "=== V5.7: Denver seed parse ==="
python3 -c "
with open('data/seed/denver-churches.ttl') as f: content = f.read()
opens = content.count('['); closes = content.count(']')
if abs(opens - closes) > 2: print('❌ Bracket mismatch'); exit(1)
print('✅ Basic parse OK')
"

# V5.8 — Validation script exists
echo "=== V5.8: Validation script ==="
test -f scripts/validate-his.sh && echo "✅ Script exists" || echo "❌ Script missing"

# V5.9 — GraphDB init loads HIS seed data
echo "=== V5.9: Init script updated ==="
grep -rq "his-rop-seed" apps/graphdb/init/ && echo "✅ Init loads HIS seed" || echo "❌ Init doesn't load HIS seed"
```

**Expected result: ALL checks show ✅. Zero ❌. Then commit:**
```bash
git add -A && git commit -m "Phase 5: add HIS ROP seed data, classification links on Denver data, end-to-end validation"
```

---

## Phase 6: Live Deployment — GraphDB + Engage Dashboard

### Why

Phases 1–5 build and validate everything locally. But the live GraphDB at `graphdb.global.church` (Railway) still has the old ontology, old JP data with `rop:` prefixes, and no HIS registry graph. The engage dashboard at `engage.global.church` doesn't know about the new SPARQL queries. This phase migrates the live system.

### Prerequisites

- Phases 1–5 committed and pushed
- Environment variables available: `GRAPHDB_URL`, `GC_API_KEY` (or whatever auth the live GraphDB requires)
- `JP_API_KEY` for re-syncing Joshua Project data

### Steps

1. **Reload the ontology into live GraphDB**:

   The updated `ontology/gc-core.ttl` (with `gc:hasPeopleClassification`, minus the removed `gc:rop3Code`/`gc:rop25Code`) and `ontology/gc-core.shacl.ttl` (with `HISConceptShape`) need to be loaded into the live repository. Use the GraphDB REST API or Workbench UI to replace the ontology:

   ```bash
   # Upload updated ontology to the default graph (or whichever graph holds the ontology)
   curl -X POST "https://graphdb.global.church/repositories/gc-core/statements" \
     -H "Content-Type: text/turtle" \
     -H "Authorization: Bearer ${GC_API_KEY}" \
     --data-binary @ontology/gc-core.ttl

   # Upload updated SHACL shapes
   curl -X POST "https://graphdb.global.church/repositories/gc-core/statements" \
     -H "Content-Type: text/turtle" \
     -H "Authorization: Bearer ${GC_API_KEY}" \
     --data-binary @ontology/gc-core.shacl.ttl
   ```

   **Note**: The exact auth mechanism depends on what's configured for task #1 (GraphDB auth). Adjust headers accordingly. If using GraphDB built-in security, use basic auth instead of bearer token.

2. **Run the HIS bridge sync against live GraphDB**:

   ```bash
   GRAPHDB_URL=https://graphdb.global.church \
   GC_API_KEY=${GC_API_KEY} \
   pnpm --filter @gc-core/his-bridge run sync
   ```

   This fetches all ROP tables from ArcGIS, converts to SKOS Turtle, and loads into the `<https://data.global.church/his-registries/>` named graph on the live instance. Verify the graph exists afterward.

3. **Re-run the JP bridge sync against live GraphDB**:

   The JP data currently in the live GraphDB uses the old `rop:`/`rog:`/`rol:` predicates and has no `gc:hasPeopleClassification` links. The updated JP bridge (Phase 3) needs to re-sync to replace the stale data:

   ```bash
   JP_API_KEY=${JP_API_KEY} \
   GRAPHDB_URL=https://graphdb.global.church \
   GC_API_KEY=${GC_API_KEY} \
   pnpm --filter @gc-core/jp-bridge run sync
   ```

   The JP sync is idempotent — it drops and reloads the `<https://data.global.church/joshua-project/>` named graph. After this, all JP people groups will have `gc:hasPeopleClassification` links pointing to the HIS ROP3 SKOS entities.

4. **Reload the Denver seed data** (or skip if prod doesn't use seed data):

   If the live instance includes the Denver seed data for demo purposes, reload it so it has the new `gc:hasPeopleClassification` links:

   ```bash
   curl -X POST "https://graphdb.global.church/repositories/gc-core/statements?context=%3Chttps%3A%2F%2Fdata.global.church%2Fdenver%2F%3E" \
     -H "Content-Type: text/turtle" \
     -H "Authorization: Bearer ${GC_API_KEY}" \
     --data-binary @data/seed/denver-churches.ttl
   ```

5. **Update the engage dashboard** (`apps/dashboard/`):

   - Add the new HIS hierarchy queries to the dashboard's query registry (if it maintains one)
   - If the dashboard has a query selector or navigation, add entries for the Affinity Bloc summary, People Cluster drilldown, etc.
   - Update the AI agent's few-shot examples in `packages/gc-agent/` to include hierarchy questions ("all peoples in the Somali cluster", "classification path for the Burmese", etc.)
   - Deploy the updated dashboard to Vercel:

   ```bash
   cd apps/dashboard && pnpm build
   # Deploy via Vercel CLI or git push (depending on CI setup)
   ```

6. **Create a `scripts/sync-live.sh`** convenience script that runs steps 1–4 in sequence:

   ```bash
   #!/usr/bin/env bash
   set -euo pipefail

   # Usage: GRAPHDB_URL=https://graphdb.global.church GC_API_KEY=xxx JP_API_KEY=xxx ./scripts/sync-live.sh

   : "${GRAPHDB_URL:?GRAPHDB_URL is required}"
   : "${GC_API_KEY:?GC_API_KEY is required}"
   : "${JP_API_KEY:?JP_API_KEY is required}"

   echo "=== Step 1: Upload ontology ==="
   curl -sf -X POST "${GRAPHDB_URL}/repositories/gc-core/statements" \
     -H "Content-Type: text/turtle" \
     -H "Authorization: Bearer ${GC_API_KEY}" \
     --data-binary @ontology/gc-core.ttl
   echo "✅ Ontology uploaded"

   echo "=== Step 2: Upload SHACL shapes ==="
   curl -sf -X POST "${GRAPHDB_URL}/repositories/gc-core/statements" \
     -H "Content-Type: text/turtle" \
     -H "Authorization: Bearer ${GC_API_KEY}" \
     --data-binary @ontology/gc-core.shacl.ttl
   echo "✅ SHACL shapes uploaded"

   echo "=== Step 3: Sync HIS registries ==="
   GRAPHDB_URL=${GRAPHDB_URL} GC_API_KEY=${GC_API_KEY} \
     pnpm --filter @gc-core/his-bridge run sync
   echo "✅ HIS registries synced"

   echo "=== Step 4: Re-sync Joshua Project ==="
   JP_API_KEY=${JP_API_KEY} GRAPHDB_URL=${GRAPHDB_URL} GC_API_KEY=${GC_API_KEY} \
     pnpm --filter @gc-core/jp-bridge run sync
   echo "✅ Joshua Project re-synced"

   echo "=== All live syncs complete ==="
   ```

### Phase 6 Validation Gate

**CRITICAL: Run ALL of these validations against the LIVE GraphDB instance. These confirm the deployment worked end-to-end.**

```bash
GRAPHDB_URL="${GRAPHDB_URL:-https://graphdb.global.church}"
REPO_URL="${GRAPHDB_URL}/repositories/gc-core"
AUTH_HEADER="Authorization: Bearer ${GC_API_KEY}"

# V6.1 — HIS named graph exists and has data
echo "=== V6.1: HIS named graph on live ==="
RESULT=$(curl -sf -X POST "${REPO_URL}" \
  -H "${AUTH_HEADER}" \
  -H "Content-Type: application/sparql-query" \
  -H "Accept: application/sparql-results+json" \
  -d "SELECT (COUNT(*) AS ?c) WHERE { GRAPH <https://data.global.church/his-registries/> { ?s ?p ?o } }")
echo "$RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
count = int(data['results']['bindings'][0]['c']['value'])
if count > 100:
    print(f'✅ HIS graph has {count} triples')
else:
    print(f'❌ HIS graph only has {count} triples (expected thousands)')
    sys.exit(1)
"

# V6.2 — SKOS hierarchy is navigable
echo "=== V6.2: SKOS hierarchy query ==="
RESULT=$(curl -sf -X POST "${REPO_URL}" \
  -H "${AUTH_HEADER}" \
  -H "Content-Type: application/sparql-query" \
  -H "Accept: application/sparql-results+json" \
  -d "PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT (COUNT(DISTINCT ?bloc) AS ?blocs) WHERE {
  GRAPH <https://data.global.church/his-registries/> {
    ?bloc skos:topConceptOf <https://data.global.church/his/rop> .
  }
}")
echo "$RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
count = int(data['results']['bindings'][0]['blocs']['value'])
if count >= 10:
    print(f'✅ Found {count} Affinity Blocs')
else:
    print(f'❌ Only {count} Affinity Blocs (expected ~15+)')
    sys.exit(1)
"

# V6.3 — JP data has hasPeopleClassification links
echo "=== V6.3: JP classification links on live ==="
RESULT=$(curl -sf -X POST "${REPO_URL}" \
  -H "${AUTH_HEADER}" \
  -H "Content-Type: application/sparql-query" \
  -H "Accept: application/sparql-results+json" \
  -d "PREFIX gc: <https://ontology.global.church/core#>
SELECT (COUNT(*) AS ?c) WHERE {
  GRAPH <https://data.global.church/joshua-project/> {
    ?pg gc:hasPeopleClassification ?rop3 .
  }
}")
echo "$RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
count = int(data['results']['bindings'][0]['c']['value'])
if count > 10000:
    print(f'✅ {count} JP people groups have classification links')
else:
    print(f'❌ Only {count} classification links (expected 16K+)')
    sys.exit(1)
"

# V6.4 — No old rop:/rog:/rol: predicates in JP graph
echo "=== V6.4: No stale predicates on live ==="
RESULT=$(curl -sf -X POST "${REPO_URL}" \
  -H "${AUTH_HEADER}" \
  -H "Content-Type: application/sparql-query" \
  -H "Accept: application/sparql-results+json" \
  -d "SELECT (COUNT(*) AS ?c) WHERE {
  GRAPH <https://data.global.church/joshua-project/> {
    ?s ?p ?o .
    FILTER(STRSTARTS(STR(?p), 'https://ontology.global.church/his/'))
  }
}")
echo "$RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
count = int(data['results']['bindings'][0]['c']['value'])
if count == 0:
    print('✅ No stale rop:/rog:/rol: predicates')
else:
    print(f'❌ Found {count} triples with old namespace predicates')
    sys.exit(1)
"

# V6.5 — Cross-graph hierarchy query works end-to-end
echo "=== V6.5: Cross-graph hierarchy query ==="
RESULT=$(curl -sf -X POST "${REPO_URL}" \
  -H "${AUTH_HEADER}" \
  -H "Content-Type: application/sparql-query" \
  -H "Accept: application/sparql-results+json" \
  -d "PREFIX gc: <https://ontology.global.church/core#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX jp: <https://ontology.global.church/joshuaproject#>
SELECT ?blocName (COUNT(DISTINCT ?pg) AS ?peoples) WHERE {
  GRAPH <https://data.global.church/his-registries/> {
    ?bloc skos:topConceptOf <https://data.global.church/his/rop> ;
          skos:prefLabel ?blocName .
    ?cluster skos:broader ?bloc .
    ?kinship skos:broader ?cluster .
    ?rop3 skos:broader ?kinship .
  }
  GRAPH <https://data.global.church/joshua-project/> {
    ?pg gc:hasPeopleClassification ?rop3 .
  }
} GROUP BY ?blocName ORDER BY DESC(?peoples) LIMIT 5")
echo "$RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
bindings = data['results']['bindings']
if len(bindings) >= 3:
    for b in bindings:
        print(f\"  {b['blocName']['value']}: {b['peoples']['value']} peoples\")
    print('✅ Cross-graph hierarchy query works')
else:
    print(f'❌ Only {len(bindings)} results (expected 3+)')
    sys.exit(1)
"

# V6.6 — sync-live.sh script exists
echo "=== V6.6: Sync script ==="
test -f scripts/sync-live.sh && echo "✅ sync-live.sh exists" || echo "❌ sync-live.sh missing"
test -x scripts/sync-live.sh && echo "✅ sync-live.sh is executable" || echo "❌ sync-live.sh not executable"
```

**Expected result: ALL checks show ✅. Zero ❌. Then commit:**
```bash
git add -A && git commit -m "Phase 6: live deployment — ontology reload, HIS sync, JP re-sync, dashboard update, sync-live script"
```

---

## ROL — Registry of Languages (Fully Loaded)

> **Status:** Complete (2026-02-25)
> **Bridge:** `packages/gc-rol-bridge/`
> **Named graph:** `<https://data.global.church/his-registries/>`

### Overview

The ROL bridge fetches the complete ISO 639-3 code set from SIL International and loads it as a flat SKOS ConceptScheme into the HIS registries named graph. This replaced the 6-language seed file (`data/seed/his-rol-seed.ttl`) with 7,083 living languages and macrolanguages.

### Data Source

- **Primary:** SIL ISO 639-3 Code Tables — `https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3.tab`
- **Filter:** scope = Individual (I) or Macrolanguage (M), type = Living (L)
- **Record count:** 7,083 concepts (living + macrolanguages)
- **Unresolved source codes:** 14 (codes referenced by resources but not in the Living/Macrolanguage subset)

### SKOS Structure

- Flat — all concepts are `skos:topConceptOf his:rol` (no hierarchy)
- Each concept: `rdf:type skos:Concept`, `skos:inScheme his:rol`, `skos:prefLabel` (English), `skos:notation` (ISO 639-3 code)
- URI pattern: `<https://data.global.church/his/rol/{iso639-3}>` (e.g., `rol:eng`, `rol:spa`)
- Linked via: `gc:hasLanguageClassification`, `gc:resourceLanguage`, `gc:inLanguage`

### GraphDB Metrics

- ~35K ROL triples in `<https://data.global.church/his-registries/>`
- HIS registries total: ~172,453 triples (ROP + ROL + ROR + ROG)
- 2,619 languages appear in resource facets (with human-readable labels)

### Dashboard Impact

- Resource Explorer language dropdown now shows all ~2,619 language names used by resources
- Text filter input added to the language dropdown when >20 options are present (client-side substring search)
- Language filter supports `?lang=<rolCode>` URL param from Map hex links

### Sync Cadence

Quarterly — aligns with SIL's ISO 639-3 update cycle. The bridge is idempotent: re-running downloads the latest TSV, regenerates Turtle, clears old ROL concepts, and reloads.

### CLI Usage

```bash
cd packages/gc-rol-bridge
npx tsx src/index.ts            # all steps: fetch + convert + load
npx tsx src/index.ts --fetch    # download TSV only
npx tsx src/index.ts --convert  # generate Turtle only
npx tsx src/index.ts --load     # load into GraphDB only
```

---

## Summary

| Phase | What | Key Outputs |
|---|---|---|
| 1 | Ontology updates | `gc:hasPeopleClassification` property, remove `gc:rop3Code`/`gc:rop25Code`, `HISConceptShape`, migration doc |
| 2 | HIS bridge package | `gc-his-bridge/` — ArcGIS client, ROP→SKOS converter (using `skos:notation`), sync orchestrator |
| 3 | JP bridge migration | Remove all flat HIS code properties + old namespaces, add `gc:hasPeopleClassification` links, update queries |
| 4 | SPARQL queries | 4 hierarchy queries — bloc summary, cluster drilldown, unengaged analysis, path |
| 5 | Seed data + local validation | Hand-crafted ROP subset, Denver links, end-to-end test script (localhost) |
| 6 | Live deployment | Ontology reload, HIS sync, JP re-sync, dashboard update, `sync-live.sh` script |

### New Named Graph

```
<https://data.global.church/his-registries/> — SKOS concept scheme with ~17K ROP3 entities
```

### New SPARQL Capabilities After Completion

- "How many people groups are in the Arab World affinity bloc?"
- "Show me all peoples in the Somali cluster with their engagement status"
- "Which affinity blocs have the most unengaged peoples?"
- "What's the full classification path for the Burmese?"
- "All people groups in the Horn of Africa cluster that no organization is engaging"
