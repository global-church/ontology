# Schema Migration: Global.Church → GC-Core Ontology v0.4.0

## Overview

This document describes the changes needed in the Global.Church schema and GCData OpenAPI spec to align with the GC-Core ontology. It covers changes from v0.1.0 through v0.3.0.

---

## Change 1: Practices — from booleans to structured objects (v0.2.0)

### What changed in the ontology

The 13 boolean practice properties on Church (`practicesBelieversBaptism`, `practicesBelieversBaptismWithin`, `practicesLordsSupper`, etc.) have been replaced by a single `hasPractice` relationship pointing to `Practice` instances. Each Practice has a `practiceType` (from an extensible SKOS vocabulary), plus optional qualifiers like `isPerformedInternally`, `practiceFrequency`, and `practiceDateAdopted`.

### What needs to change in the Global.Church schema

**Before (LinkML / current schema):**
```yaml
Church:
  attributes:
    practicesBelieversBaptism:
      range: boolean
    practicesBelieversBaptismWithin:
      range: boolean
    practicesLordsSupper:
      range: boolean
    # ... 11 more boolean fields
```

**After:**
```yaml
Practice:
  attributes:
    practiceType:
      range: PracticeTypeEnum
      required: true
    isActive:
      range: boolean
    isPerformedInternally:
      range: boolean
    frequency:
      range: string
    dateAdopted:
      range: date

PracticeTypeEnum:
  permissible_values:
    BeliversBaptism:
    LordsSupper:
    Giving:
    TeachingTheWord:
    Serving:
    Accountability:
    Prayer:
    Worship:
    DiscipleMaking:

Church:
  attributes:
    practices:
      range: Practice
      multivalued: true
    # Remove all practicesXxx boolean fields
    # Remove activelyMakingDisciples (now a practice type)
```

### What needs to change in GCData OpenAPI spec

**ChurchEntity schema — replace boolean fields with a practices array:**

```yaml
ChurchEntity:
  allOf:
    - $ref: "#/components/schemas/EntityBase"
    - type: object
      properties:
        # REMOVE these fields:
        # practicesBelieversBaptism, practicesBelieversBaptismWithin,
        # practicesLordsSupper, practicesLordsSupperWithin,
        # practicesGiving, practicesTeachingTheWord,
        # practicesTeachingTheWordWithin, practicesServing,
        # practicesAccountability, practicesPrayer, practicesWorship,
        # activelyMakingDisciples

        # ADD this field:
        practices:
          type: array
          items:
            $ref: "#/components/schemas/ChurchPractice"

ChurchPractice:
  type: object
  required:
    - practiceType
  properties:
    practiceType:
      type: string
      enum:
        - BelieversBaptism
        - LordsSupper
        - Giving
        - TeachingTheWord
        - Serving
        - Accountability
        - Prayer
        - Worship
        - DiscipleMaking
    isActive:
      type: boolean
      default: true
    isPerformedInternally:
      type: boolean
      description: "Replaces the paired 'xxxWithin' booleans. True = performed by a member of the gathering."
    frequency:
      type: string
      description: "e.g., 'weekly', 'monthly', 'as-needed'"
    dateAdopted:
      type: string
      format: date
```

### Data migration

For existing records with boolean practice fields, convert each `true` boolean into a Practice object:

```
practicesBelieversBaptism: true        →  { practiceType: "BelieversBaptism", isActive: true }
practicesBelieversBaptismWithin: true  →  (merge) isPerformedInternally: true on the same object
practicesLordsSupper: true             →  { practiceType: "LordsSupper", isActive: true }
activelyMakingDisciples: true          →  { practiceType: "DiscipleMaking", isActive: true }
```

Fields that are `false` or `null` can either be omitted (absence = not practiced) or included with `isActive: false` depending on whether you need to distinguish "not practiced" from "unknown."

### JSON payload example

**Before:**
```json
{
  "entityType": "Church",
  "practicesBelieversBaptism": true,
  "practicesBelieversBaptismWithin": true,
  "practicesLordsSupper": true,
  "practicesLordsSupperWithin": false,
  "practicesPrayer": true,
  "activelyMakingDisciples": true
}
```

**After:**
```json
{
  "entityType": "Church",
  "practices": [
    { "practiceType": "BelieversBaptism", "isActive": true, "isPerformedInternally": true },
    { "practiceType": "LordsSupper", "isActive": true, "isPerformedInternally": false },
    { "practiceType": "Prayer", "isActive": true },
    { "practiceType": "DiscipleMaking", "isActive": true }
  ]
}
```

---

## Change 2: Person roles — from subclasses to contextual roles (v0.2.0)

### What changed in the ontology

`FieldWorker` and `Leader` are no longer subclasses of `Person`. Instead, they are instances of `MinistryRole`, and a person's role in any given activity is expressed through `MinistryParticipation` (a PROV-O qualified association).

### What needs to change in the schema

This change is primarily ontological and doesn't necessarily require immediate schema changes if your systems don't currently store a `userType` or `personType` field. The key architectural implication is:

- **Don't add `role` as a fixed property of User/Person.** Instead, role is a property of the relationship between a person and an activity.
- If you need to capture "this user is typically a field worker," treat it as a default role preference on the user profile, not as a type classification.

### What needs to change in GCData OpenAPI spec

The current `userId` field in `EntityEPBase` is sufficient — it identifies who recorded the data. If you want to also capture the role the person played in the activity (not just who recorded it), add an optional `participants` array:

```yaml
EntityEPBase:
  properties:
    # Existing fields remain unchanged
    participants:
      type: array
      description: "Optional. People who participated in this activity and their roles."
      items:
        type: object
        required:
          - userId
          - role
        properties:
          userId:
            type: string
          role:
            type: string
            enum:
              - FieldWorker
              - Leader
              - Trainer
              - Recorder
```

This is an additive, non-breaking change.

---

## Change 3: Overture — corrected to Overture Maps geospatial model (v0.3.0)

### What changed in the ontology

`Overture` was previously modeled as a generic "outreach initiative." It has been corrected to represent geospatial place records from the **Overture Maps Foundation** (overturemaps.org). The class now models church/place-of-worship locations sourced from the Overture Maps "places" theme.

### New properties

| Property | Type | Description |
|----------|------|-------------|
| `overtureId` | string | Unique ID from Overture Maps dataset |
| `overtureCategory` | string | Place category (e.g., 'place_of_worship') |
| `overtureConfidence` | double | Confidence score (0.0-1.0) |
| `overtureSourceDataset` | string | Source dataset ('meta', 'msft', 'osm') |
| `matchedChurch` | → Church | Link to matched Church entity |
| `overtureLocation` | → Location | Geographic location |

### Removed properties

- `overtureStatus` — was modeling initiative status, not applicable
- `overtureDescription` — was modeling initiative narrative, not applicable
- `targetsLocation` — replaced by `overtureLocation`

### OpenAPI schema addition

```yaml
OverturePlace:
  type: object
  required:
    - overtureId
  properties:
    overtureId:
      type: string
      description: "Overture Maps place record ID"
    category:
      type: string
      description: "Overture Maps place category"
    confidence:
      type: number
      format: double
      minimum: 0.0
      maximum: 1.0
    sourceDataset:
      type: string
      enum: [meta, msft, osm]
    matchedChurchId:
      type: string
      description: "ID of matched Church entity, if resolved"
    location:
      $ref: "#/components/schemas/LocationOfActivity"
```

---

## Change 4: 3D Insight Engagement Model (v0.3.0)

### What changed in the ontology

The flat `EngagementPhase` entity has been replaced by a composite model implementing the Joshua Project **3D Insight** framework:

- **`EngagementAssessment`** (prov:Activity) — the act of evaluating a people group's engagement state
- **`EngagementState`** (prov:Entity) — the resulting composite snapshot, with three dimensions:
  - D1: `phaseValue` (integer 0-7)
  - D2: `engagementStrength` (→ EngagementStrengthLevel: Unknown, Initial, Growing, Active, Flourishing)
  - D3: `evangelicalPercentage` (on PeopleGroup: double 0.0-100.0)
- **Phase sub-indicator** (`phaseSubIndicator`: 0-9 for years of data staleness, or "R" for reported cessation)
- **`EngagementAccelerator`** SKOS concept scheme (12 strategic domains)
- **`AcceleratorScore`** — reified link between EngagementState and EngagementAccelerator with qualitative level
- Multi-source provenance: `assessmentUsedDataSet`, `assessmentUsedPayload`, `assessmentUsedRecord`

### Removed classes

- `EngagementPhase` — replaced by `EngagementState`

### New classes

| Class | Superclass | Description |
|-------|------------|-------------|
| `EngagementAssessment` | prov:Activity | Assessment activity producing an EngagementState |
| `EngagementState` | prov:Entity | Composite 3D engagement snapshot |
| `EngagementStrengthLevel` | skos:Concept | D2 vocabulary: U, I, G, A, F |
| `EngagementAccelerator` | skos:Concept | 12 strategic domain concepts |
| `AcceleratorScore` | prov:Entity | Reified accelerator evaluation |

### New properties on PeopleGroup

| Property | Type | Description |
|----------|------|-------------|
| `evangelicalPercentage` | double (0.0-100.0) | D3: % evangelical Christian |
| `populationInCountry` | nonNegativeInteger | Population within the country |

### OpenAPI schema additions

```yaml
EngagementAssessment:
  type: object
  required:
    - assessmentDate
    - peopleGroupId
  properties:
    assessmentDate:
      type: string
      format: date-time
    methodology:
      type: string
      description: "e.g., 'Joshua Project 3D Insight', 'field survey'"
    peopleGroupId:
      type: string
      description: "ROP3byCountry or other PG identifier"
    usedDataSets:
      type: array
      items:
        type: string
        description: "DataSet IDs consumed"
    usedPayloads:
      type: array
      items:
        type: string
        description: "ExchangePayload IDs consumed"

EngagementState:
  type: object
  required:
    - phaseValue
    - engagementStrength
    - peopleGroupId
  properties:
    phaseValue:
      type: integer
      minimum: 0
      maximum: 7
    phaseSubIndicator:
      type: string
      pattern: "^([0-9]|R)$"
      description: "0=current, 1-9=years stale, R=reported cessation"
    engagementStrength:
      type: string
      enum: [Unknown, Initial, Growing, Active, Flourishing]
    peopleGroupId:
      type: string
    acceleratorScores:
      type: array
      items:
        $ref: "#/components/schemas/AcceleratorScore"
    stscAssessment:
      $ref: "#/components/schemas/STSCAssessment"

AcceleratorScore:
  type: object
  required:
    - domain
    - level
  properties:
    domain:
      type: string
      enum:
        - Prayer
        - Scripture
        - Film
        - AudioResources
        - GospelPresentation
        - Workers
        - ChurchPlanting
        - LeaderDevelopment
        - TransformationalDevelopment
        - Broadcasting
        - StrategicIntercessors
        - MovementStrategy
    level:
      type: string
      enum: [none, partial, significant, full]
```

### Data migration

For existing `EngagementPhase` records, convert to `EngagementState`:

```
EngagementPhase { phaseValue: 3 }
→
EngagementState {
  phaseValue: 3,
  phaseSubIndicator: "0",
  engagementStrength: "Unknown"  // default when no D2 data exists
}
```

Existing `phaseForDataSet` and `phaseForPeopleGroup` links become `stateForDataSet` and `stateForPeopleGroup`.

---

## Summary of all breaking vs non-breaking changes

| Change | Version | Breaking? | Scope |
|--------|---------|-----------|-------|
| Remove 13 boolean practice fields | v0.2.0 | **Yes** | GCData OpenAPI, Global.Church schema |
| Add `practices` array to ChurchEntity | v0.2.0 | No | GCData OpenAPI |
| Add `participants` array to EntityEPBase | v0.2.0 | No | GCData OpenAPI |
| Remove `overtureStatus`/`overtureDescription` | v0.3.0 | **Yes** | Global.Church schema |
| Add Overture Maps properties | v0.3.0 | No | Global.Church schema |
| Remove `EngagementPhase` class | v0.3.0 | **Yes** | GCData OpenAPI, consuming systems |
| Add `EngagementAssessment` + `EngagementState` | v0.3.0 | No | GCData OpenAPI |
| Add `EngagementStrengthLevel` vocabulary | v0.3.0 | No | GCData OpenAPI |
| Add `EngagementAccelerator` + `AcceleratorScore` | v0.3.0 | No | GCData OpenAPI |
| Add `evangelicalPercentage` to PeopleGroup | v0.3.0 | No | Global.Church schema |

### Recommended rollout

1. **Phase 1** — Add all new schemas as optional alongside existing structures. Producing systems begin populating both old and new. Non-breaking.
2. **Phase 2** — Consuming systems migrate to read from new structures (`practices`, `EngagementState`, Overture Maps fields). Validate both paths.
3. **Phase 3** — Deprecate and remove old structures (boolean practices, `EngagementPhase`, old Overture fields). Bump GCData version to 2.0.

---

## Change 5: JP 3D Insight Namespace Migration (v0.4.0)

### What changed in the ontology

Joshua Project's 3D Insight engagement model was originally minted under the `gc:` namespace. Since JP is the authority and designer of this framework, these concepts have been moved to the `jp:` namespace (`https://ontology.global.church/joshuaproject#`) to properly credit JP as the vocabulary owner. GC-Core still *uses* these concepts but no longer *owns* them.

**Namespace**: `jp: <https://ontology.global.church/joshuaproject#>` (pre-existing, already used for JP metadata properties like `jp:population`, `jp:jpScale`, etc.)

### Classes moved from gc: → jp:

| Old URI | New URI | Type |
|---------|---------|------|
| `gc:EngagementAssessment` | `gc:Assessment` | Class (prov:Activity) |
| `gc:EngagementState` | `gc:AssessmentResult` | Class (prov:Entity) |
| `gc:EngagementStrengthLevel` | `jp:EngagementStrengthLevel` | Class (skos:Concept) |
| `gc:STSCAssessment` | `(removed in v0.13.0)` | Class (prov:Entity) |
| `gc:EngagementAccelerator` | `jp:EngagementAccelerator` | Class (skos:Concept) |
| `gc:AcceleratorScore` | `(removed in v0.13.0)` | Class (prov:Entity) |

### SKOS concept schemes moved

| Old URI | New URI |
|---------|---------|
| `gc:EngagementStrengthScheme` | `jp:EngagementStrengthScheme` |
| `gc:EngagementAcceleratorScheme` | `jp:EngagementAcceleratorScheme` |

### Individuals moved (5 strength levels + 12 accelerators)

- `gc:StrengthUnknown` → `jp:StrengthUnknown` (and Initial, Growing, Active, Flourishing)
- `gc:AccPrayer` → `jp:AccPrayer` (and all 11 other accelerator domains)

### Properties moved

| Old URI | New URI | Domain → Range |
|---------|---------|----------------|
| `gc:assessesPeopleGroup` | `gc:assessesPeopleGroup` | gc:Assessment → gc:PeopleGroup |
| `gc:assessmentDate` | `gc:assessmentDate` | gc:Assessment → xsd:date |
| `gc:assessmentMethodology` | `gc:assessmentMethodology` | gc:Assessment → xsd:string |
| `gc:assessmentUsedDataSet` | `jp:assessmentUsedDataSet` | gc:Assessment → gc:DataSet |
| `gc:assessmentUsedPayload` | `jp:assessmentUsedPayload` | gc:Assessment → gc:ExchangePayload |
| `gc:assessmentUsedRecord` | `jp:assessmentUsedRecord` | gc:Assessment → gc:EngagementRecord |
| `gc:stateForPeopleGroup` | `gc:resultForPeopleGroup` | gc:AssessmentResult → gc:PeopleGroup |
| `gc:stateForDataSet` | `jp:stateForDataSet` | gc:AssessmentResult → gc:DataSet |
| `gc:phaseValue` | `jp:phaseValue` | gc:AssessmentResult → xsd:integer |
| `gc:phaseSubIndicator` | `jp:phaseSubIndicator` | gc:AssessmentResult → xsd:string |
| `gc:engagementStrength` | `jp:engagementStrength` | gc:AssessmentResult → jp:EngagementStrengthLevel |
| `gc:hasAcceleratorScore` | `(removed in v0.13.0)` | gc:AssessmentResult → (removed in v0.13.0) |
| `gc:acceleratorDomain` | `(removed in v0.13.0)` | (removed in v0.13.0) → jp:EngagementAccelerator |
| `gc:acceleratorLevel` | `(removed in v0.13.0)` | (removed in v0.13.0) → xsd:string |
| `gc:hasSTSCAssessment` | `(removed in v0.13.0)` | gc:AssessmentResult → (removed in v0.13.0) |
| `gc:statusOfTheTask` | `(removed in v0.13.0)` | (removed in v0.13.0) → xsd:integer |
| `gc:stateOfTheChurch` | `(removed in v0.13.0)` | (removed in v0.13.0) → xsd:integer |
| `gc:evangelicalPercentage` | `jp:evangelicalPercentage` | gc:PeopleGroup → xsd:decimal |

### What did NOT move (stays in gc:)

- `gc:PeopleGroup`, `gc:EngagementCommitment`, `gc:EngagementRecord`, `gc:DataSet` — these are GC-Core concepts, not JP-owned
- All commitment properties (`gc:commitmentOrg`, `gc:commitmentStatus`, etc.)
- `gc:engagesPeopleGroup` — GC-Core activity → people group link
- All church, organization, person, ministry activity classes and properties

### Files updated

| Layer | Files | Changes |
|-------|-------|---------|
| Ontology | `ontology/gc-core.ttl` | Added jp: prefix, moved all 3D Insight definitions to jp: namespace |
| SHACL | `ontology/gc-core.shacl.ttl` | Updated sh:targetClass, sh:path, sh:class for all engagement shapes |
| SPARQL queries (12) | `packages/gc-sparql/src/queries/*.rq` | Added PREFIX jp:, updated all engagement property references |
| Seed data | `data/seed/denver-churches.ttl` | Added jp: prefix, migrated all engagement instances |
| Test data | `test/denver-churches.ttl` | Same as seed data |
| JP bridge | `packages/gc-jp-bridge/src/jp-to-rdf.ts` | `gc:evangelicalPercentage` → `jp:evangelicalPercentage` |
| Dashboard | `apps/dashboard/src/components/SparqlConsole.tsx` | Updated default query |
| Agent (Vercel) | `apps/dashboard/api/ask.ts` | Updated terminology section |
| Agent (package) | `packages/gc-agent/src/agent.ts` | Updated instructions text |
| Agent context | `packages/gc-agent/src/ontology-context.ts` | Updated regex patterns and hardcoded text |
| Build script | `apps/dashboard/scripts/generate-agent-context.mjs` | Updated regex patterns and prefixes |
| Documentation | `README.md`, `gc-core-graphdb-buildout.md`, `his-registry-buildout.md` | Updated all SPARQL examples |
| Test script | `test/query-engagement-status.py` | Updated SPARQL query |
| Skills | `.claude/skills/gc-sparql/`, `gc-shacl/`, `gc-ontology-doc/` | Updated examples |

### Impact on consuming systems

- **SPARQL queries**: All queries referencing engagement classes/properties must add `PREFIX jp:` and use `jp:` for migrated concepts
- **OpenAPI / GCData**: The URI strings in JSON-LD responses change (e.g., `gc:EngagementState` → `gc:AssessmentResult`). Consumers parsing RDF URIs must update.
- **JP bridge**: Already used `jp:` prefix for metadata — `jp:evangelicalPercentage` is now consistent with the rest
- **No backward compatibility layer**: This is a clean break. No `owl:equivalentClass` bridges are maintained.

### Breaking?

**Yes** — all SPARQL queries, RDF consumers, and API clients that reference the old `gc:` URIs for engagement concepts must update to `jp:` URIs.
