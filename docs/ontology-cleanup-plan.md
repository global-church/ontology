# GC-Core Ontology Cleanup Plan

**Date:** 2026-03-03
**Status:** Approved with modifications — ready for execution
**Goal:** Remove unused concepts from core.ttl and seed data to reduce complexity

---

## Methodology

Every class, property, SKOS scheme, and individual in core.ttl was cross-referenced against all production code outside `ontology/` — bridges (`gc-org-bridge`, `gc-engagement-bridge`), 55+ SPARQL queries, Supabase Edge Functions, app code (`engage`, `platform`, `admin`), the KNIME pipeline, and the API gateway. A concept is "unused" if it appears **only** in core.ttl, SHACL shapes, seed data (`denver-churches.ttl`), documentation, or agent context strings — never in a bridge that materializes triples, a SPARQL query called by an app, or application logic.

---

## Tier 1: Remove — Zero Production Use

These concepts have no bridge materializing data, no SPARQL query consuming them, and no app referencing them.

### 1.1 Worker Deployment Model (entire subsystem)

**What:** `gc:Person` and all related properties/roles — the field worker tracking model.

| Concept | Type | Why unused |
|---|---|---|
| `gc:Person` | Class | No bridge creates Person triples. User identity is in Supabase, not GraphDB. |
| `gc:MinistryRole` | Class | Role instances below are never referenced outside seed data. |
| `gc:FieldWorkerRole` | Individual | Only in denver-churches.ttl |
| `gc:LeaderRole` | Individual | Only in denver-churches.ttl |
| `gc:TrainerRole` | Individual | Only in denver-churches.ttl |
| `gc:RecorderRole` | Individual | Only in denver-churches.ttl |
| `gc:ChurchPlanterRole` | Individual | Only in denver-churches.ttl |
| `gc:TranslatorRole` | Individual | Only in denver-churches.ttl |
| `gc:StrategyCoordinatorRole` | Individual | Only in denver-churches.ttl |
| `gc:MinistryParticipation` | Class | Never instantiated outside seed data |
| `gc:participationRole` | Property | Never used outside seed data |
| `gc:userId` | Property | Identity lives in Supabase `user_profiles` |
| `gc:groupId` | Property | Never used |
| `gc:personName` | Property | Never used outside seed data |
| `gc:personEmail` | Property | Never used outside seed data |
| `gc:personPhone` | Property | Never used outside seed data |
| `gc:memberOf` | Property | Never used outside seed data |
| `gc:sendingOrganization` | Property | Never used outside seed data |
| `gc:deploymentStatus` | Property | Never used outside seed data |
| `gc:isCrossCultural` | Property | Never used outside seed data |
| `gc:fieldEntryDate` | Property | Never used outside seed data |
| `gc:Team` | Class | Never instantiated |

**Seed file to remove:** `worker-deployment-vocab-seed.ttl` (DeploymentStatusScheme + MethodologyScheme)

**SPARQL queries to remove:**
- `worker-deployment-summary.rq` — queries gc:Person + gc:deploymentStatus, no data exists
- `reached-vs-unreached-workers.rq` — same, dead query

**SHACL shapes to remove:** PersonShape, MinistryParticipationShape (if they exist in core.shacl.ttl)

**Estimated removal:** ~75 lines from core.ttl, 121 lines from seed file, 2 SPARQL files

### 1.2 Data Recording & Exchange Provenance (entire subsystem)

**What:** The GCData protocol modeling layer — recording activities, engagement records, exchange payloads. This was designed for a federated data exchange system (GCBridge + KeyCloak) that was never built.

| Concept | Type | Why unused |
|---|---|---|
| `gc:DataRecordingActivity` | Class | Never instantiated |
| `gc:recordDateTime` | Property | Never used |
| `gc:recordsActivity` | Property | Never used |
| `gc:EngagementRecord` | Class | Never instantiated |
| `gc:entityType` | Property | Never used |
| `gc:documentsOrganization` | Property | Never used |
| `gc:ExchangePayload` | Class | Never instantiated |
| `gc:EntityExchangePayload` | Class | Never instantiated |
| `gc:ScaleExchangePayload` | Class | Never instantiated |
| `gc:DataExchangeActivity` | Class | Never instantiated |
| `gc:payloadFormat` | Property | Never used |
| `gc:payloadVersion` | Property | Never used |
| `gc:payloadPermissions` | Property | Never used |
| `gc:DataSource` | Class | Never instantiated |
| `gc:GCBridge` | Class | Never instantiated |
| `gc:hasSource` | Property | Never used |

**Estimated removal:** ~70 lines from core.ttl

### 1.3 Agentic Trust Layer Alignment

**What:** Hook classes for interoperability with agent-explorer ontology. No Agentic Trust system exists.

| Concept | Type | Why unused |
|---|---|---|
| `gc:DataExchangeAttestation` | Class | Never instantiated |
| `gc:attestsPayload` | Property | Never used |
| `gc:DataSource rdfs:subClassOf at:Agent` | Axiom | Dead alignment |
| `at:` prefix | Prefix | Only used by above |

**Estimated removal:** ~20 lines from core.ttl + prefix declaration

### 1.4 Data Privacy Subset Annotations

**What:** Annotation property `gc:dataSubset` and 7 named individuals (SubsetPublic, SubsetPrivate, etc.) plus the annotation triples. No code reads these annotations — access control is handled in Supabase RLS and Zuplo API gateway, not via RDF annotations.

| Concept | Type | Why unused |
|---|---|---|
| `gc:dataSubset` | AnnotationProperty | Never queried |
| `gc:SubsetPublic` | Individual | Never queried |
| `gc:SubsetPrivate` | Individual | Never queried |
| `gc:SubsetPII` | Individual | Never queried |
| `gc:SubsetInternal` | Individual | Never queried |
| `gc:SubsetChurchCore` | Individual | Never queried |
| `gc:SubsetUserCore` | Individual | Never queried |
| `gc:SubsetEnrichment` | Individual | Never queried |
| 9 annotation triples | Triples | Never queried |

**Estimated removal:** ~35 lines from core.ttl (Section VIII entirely)

### 1.5 PeopleGroupEngagement Reification

**What:** A reified count class for engagement with people groups. No bridge produces these triples — engagement is tracked via `gc:EngagementClaim` instead.

| Concept | Type | Why unused |
|---|---|---|
| `gc:PeopleGroupEngagement` | Class | Never instantiated |
| `gc:engagementPeopleGroup` | Property | Never used |
| `gc:engagementCount` | Property | Never used |
| `gc:hasPeopleGroupEngagement` | Property | Never used |

**Estimated removal:** ~20 lines from core.ttl (Section VI entirely)

### 1.6 DataSet Concepts

**What:** Named data collection with geographic scope. Modeled for GCData SEP protocol. JP bridge does use `jp:stateForDataSet` but no DataSet instances actually exist — the bridge produces Assessment/AssessmentResult triples that don't reference DataSets.

| Concept | Type | Why unused |
|---|---|---|
| `gc:DataSet` | Class | Never instantiated |
| `gc:dataSetId` | Property | Never used |
| `gc:dataSetName` | Property | Never used |
| `gc:dataSetAltName` | Property | Never used |
| `gc:lastUpdatedDate` | Property | Never used |
| `gc:coversArea` | Property | Never used |
| `jp:stateForDataSet` | Property | Defined but no DataSet instances to reference |

**Estimated removal:** ~25 lines from core.ttl

### 1.7 `gc:Church` Deprecated Class

**Status:** Marked `owl:deprecated true` with `owl:equivalentClass gc:Organization`. No production code references `gc:Church` as a class.

**Action:** Remove entirely. The deprecation period has served its purpose. Any old data using `gc:Church` was never loaded at scale. Clean break.

**Estimated removal:** ~10 lines from core.ttl

### 1.8 ChurchWebsiteText

**What:** 1 class + 3 properties. Used only in Denver seed data. The KNIME pipeline scrapes websites but stores results in Supabase — it doesn't create ChurchWebsiteText RDF triples.

| Concept | Type | Why unused |
|---|---|---|
| `gc:ChurchWebsiteText` | Class | Never instantiated outside seed data |
| `gc:websiteUrl` | Property | Never used outside seed data |
| `gc:websiteTextContent` | Property | Never used outside seed data |
| `gc:hasWebsiteText` | Property | Never used outside seed data |

**Action:** Remove. If KNIME ever needs to write website text to GraphDB, the model can be re-added.

**Estimated removal:** ~20 lines from core.ttl

### 1.9 Denver Seed Data

**What:** `denver-churches.ttl` — the original test data file exercising early ontology classes. Most of the concepts it instantiates (Person, Worker, Activity, Practice) are being removed or have no production equivalent. It also exercises concepts that remain (Organization, Location, Endorsement) but with fake data that adds noise to GraphDB.

**Action:** Delete `denver-churches.ttl` entirely. Remove all references to it across the project and subprojects.

**Known references (26 files):**

| File | Reference type |
|---|---|
| `ontology/data/seed/denver-churches.ttl` | The file itself |
| `core/graphdb/init/load-seed-data.sh` | Loads it into GraphDB |
| `core/docs/gc-core-graphdb-buildout.md` | Documentation |
| `core/docs/overnight-backlog-2026-02-21.md` | Documentation |
| `core/docs/hex-viewport-fix-prompt.md` | Documentation |
| `core/packages/gc-sparql/src/queries/endorsing-bodies-for-church.rq` | May reference Denver entities |
| `core/packages/gc-sparql/src/queries/verify-church-subclass.rq` | May reference Denver entities |
| `core/packages/gc-jp-bridge/src/linker.ts` | May reference Denver named graph |
| `core/supabase/migrations/20260221300000_hex_summary_performance.sql` | Documentation reference |
| `ontology/CHANGELOG.md` | Historical references (keep) |
| `ontology/CLAUDE.md` | References seed data |
| `ontology/docs/ontology-design-principles.md` | Documentation |
| `ontology/data/migrations/SCHEMA-MIGRATION.md` | Documentation |
| `.claude/skills/gc-skos-scheme/SKILL.md` | References Denver pattern |
| `.claude/skills/gc-graphdb/SKILL.md` | References Denver graph |
| `.claude/skills/gc-shacl/SKILL.md` | References Denver data |
| `.claude/skills/gc-sparql/SKILL.md` | References Denver data |
| `.claude/skills/gc-turtle-author/SKILL.md` | References Denver pattern |
| `docs/prompts/plan-core-extraction.md` | Documentation |
| `CLAUDE.md` | Ecosystem overview |
| `core/reference/data/peoplegroups.org/*` | CSV data (may contain "Denver" in data rows — verify) |

**Approach:** Remove the file, then search-and-update references. CHANGELOG.md entries are historical and should be left as-is. Skills, CLAUDE.md files, and documentation need active cleanup. `load-seed-data.sh` needs the Denver load line removed. SPARQL queries referencing Denver-specific URIs (`:loc-denver`, `:calvary-chapel`, etc.) need review.

---

## Tier 2: Simplify — Partial Use, Trim Edges

### 2.1 Overture Class

**Status:** The Overture class and its properties are partially used — the Org Bridge writes `gc:overtureId`, `gc:overtureCategory`, and `gc:matchedOrganization` on Overture blank nodes. However, `gc:overtureConfidence`, `gc:overtureSourceDataset`, and `gc:overtureLocation` are not populated by the bridge.

**Action:** Keep `gc:Overture`, `gc:overtureId`, `gc:overtureCategory`, `gc:matchedOrganization`. Remove `gc:overtureConfidence`, `gc:overtureSourceDataset`, `gc:overtureLocation` (can re-add when KNIME provides this data).

**Estimated removal:** ~15 lines from core.ttl

---

## Tier 3: Keep — Actively Used or Planned

These are confirmed in use by bridges, SPARQL queries, or apps, or are being intentionally kept for near-term use:

### Actively used in production
- **gc:Organization** + all org properties (Org Bridge writes 37K+ orgs)
- **gc:PeopleGroup** + peopleGroupName, hasPeopleClassification, populationInCountry (JP Bridge)
- **gc:Location** + countryCode, latitude, longitude, address, locality, region, postalCode (Org Bridge)
- **gc:Assessment / gc:AssessmentResult** + all JP and IMB properties (JP Bridge, IMB Bridge)
- **gc:AssessmentMethodologyScheme** + MethodologyJPProgressScale, MethodologyIMBAssessment (bridges)
- **gc:EngagementClaim** + all claim properties (Engagement Bridge, live in production)
- **gc:EngagementTypeScheme** + all 9 engagement types (Engagement Bridge)
- **gc:ClaimStatusScheme** + all 4 statuses (Engagement Bridge)
- **gc:Endorsement** + all endorsement properties (SPARQL queries, seed data, BGEA import planned)
- **gc:EndorsementStatusScheme** + **EndorsementTypeScheme** (queries, seed data)
- **gc:MissionResource** + all resource properties (IMB resource bridge, 8+ SPARQL queries)
- **gc:ResourceCollection** + collectionName, partOfCollection (IMB resources)
- **ResourceDomainScheme**, **ResourceFormatScheme**, **ResourceFunctionScheme**, **ResourceStatusScheme** (all used)
- **gc:OrganizationTypeScheme** (Org Bridge)
- **gc:hasBeliefClassification** + **BeliefTypeScheme** (Org Bridge)
- **gc:hasDenominationClassification** + **DenominationScheme** (Org Bridge)
- **gc:hasLanguageClassification**, **gc:hasReligionClassification**, **gc:hasGeographyClassification** (bridges)
- **jp:evangelicalPercentage** + all jp: properties on PeopleGroup and AssessmentResult (JP Bridge)
- **imb:** namespace properties (IMB Bridge)
- **gc:MethodologyNPL7Phases** (keep — assessment methodology concept, even if no NPL data yet)

### Kept for near-term tracking app prototype
- **gc:MinistryActivity** (abstract base) + all 8 concrete activity types (ChurchFormation, GospelConversation, PrayerWalk, DiscipleshipActivity, BaptismActivity, LeadershipDevelopment, MediaDistribution, TrainingActivity)
- **Activity properties:** gc:dateTimeOfActivity, gc:atLocation, gc:engagesPeopleGroup, gc:inLanguage, gc:concernsReligion, gc:usesMethodology
- **Gospel Conversation outcomes:** gc:totalHeard, gc:positiveResponse, gc:interestedResponse, gc:negativeResponse, gc:unknownResponse, gc:alreadyFollowingResponse, gc:languageOfConversation
- **gc:Practice** + PracticeTypeScheme + all 9 practice type instances + practice properties

### Kept for future org data enrichment
- **Church-specific properties:** gc:isActive, gc:dateStarted, gc:dateEnded, gc:identifiesAsChurch, gc:hasAppointedLeaders, gc:numberOfPeopleAttending, gc:numberOfBelievers, gc:numberOfBaptizedBelievers, gc:languageUsedWhenGathering, gc:isMultiCampus, gc:campusName, gc:overarchingName, gc:servicesInfo, gc:givingUrl, gc:socialMediaUrl, gc:bannerUrl, gc:logoUrl

---

## Summary

| Tier | Items | Estimated lines removed from core.ttl |
|---|---|---|
| Tier 1: Remove | 9 items, ~55 concepts | ~275 lines |
| Tier 2: Simplify | 1 item, ~3 concepts | ~15 lines |
| **Total** | **~58 concepts** | **~290 lines (~12.5% of core.ttl)** |

core.ttl is currently ~2320 lines. After cleanup: ~2030 lines.

Major items kept vs original plan: Ministry Activity types (+60 lines), Gospel Conversation outcomes (+40 lines), Church-specific properties (+30 lines). Net reduction is smaller but the remaining ontology is tighter — everything left either has production data or a concrete near-term plan.

---

## Seed Data Changes

| File | Action |
|---|---|
| `worker-deployment-vocab-seed.ttl` | Delete entirely |
| `denver-churches.ttl` | Delete entirely + remove all references across project |

## SPARQL Query Changes

| File | Action |
|---|---|
| `worker-deployment-summary.rq` | Delete |
| `reached-vs-unreached-workers.rq` | Delete |
| `churches-by-people-group.rq` | Keep |

## SHACL Shape Changes

Review `gc-core.shacl.ttl` (rename to `core.shacl.ttl` as part of this cleanup) and make these changes:

**Shapes to delete entirely (confirmed present):**
- `:PersonShape` (lines 371–411) — targets gc:Person
- `:MinistryParticipationShape` (lines 418–437) — targets gc:MinistryParticipation
- `:DataRecordingActivityShape` (lines 739–763) — targets gc:DataRecordingActivity
- `:ExchangePayloadShape` (lines 706–732) — targets gc:ExchangePayload
- `:PeopleGroupEngagementShape` (lines 770–787) — targets gc:PeopleGroupEngagement
- `:DataSetShape` (lines 794+) — targets gc:DataSet

**Cross-references to remove from kept shapes:**
- `:OrganizationShape` line ~290: remove `sh:property [ sh:path gc:hasWebsiteText ; sh:class gc:ChurchWebsiteText ... ]` — ChurchWebsiteText is being deleted

---

## Section Restructuring

After removal, core.ttl sections would be:

| # | Section | Content |
|---|---|---|
| I | Agents | gc:Organization (+ Team kept as subclass), gc:hasOrganizationType, org properties |
| II | Entities | PeopleGroup, Location, Overture, ChurchWebsiteText removed, MissionResource, ResourceCollection |
| III | Activities | gc:MinistryActivity + all 8 concrete types, activity properties, Gospel Conversation outcomes |
| IV | Practice | gc:Practice, PracticeTypeScheme |
| V | Assessment | Assessment, AssessmentResult, methodology scheme, JP/IMB properties |
| VI | Endorsements | Endorsement model |
| VII | Engagement Claims | EngagementClaim model |
| VIII | Resource Vocabularies | Domain, Format, Function, Status schemes |

Removed sections: Data Recording & Exchange (IV old), PeopleGroupEngagement (VI old), Provenance Patterns (VII old — trim to only document patterns that exist), Data Privacy Subsets (VIII old), Agentic Trust (IX old).

---

## Execution Order

### Phase A: Archive + file cleanup (ontology repo)

1. **Archive first** — copy current core.ttl, gc-core.shacl.ttl, and all seed files to `ontology/archive/v0.15.1/` before any changes
2. **Delete `denver-churches.ttl`** from `ontology/data/seed/`
3. **Delete `worker-deployment-vocab-seed.ttl`** from `ontology/data/seed/`
4. **Remove Tier 1 concepts** from core.ttl (Worker/Person model, Data Recording/Exchange, Agentic Trust alignment, Data Privacy Subsets, PeopleGroupEngagement, DataSet, deprecated gc:Church, ChurchWebsiteText)
5. **Simplify Tier 2** — remove unused Overture properties (gc:overtureConfidence, gc:overtureSourceDataset, gc:overtureLocation)
6. **Rename SHACL file** `gc-core.shacl.ttl` → `core.shacl.ttl`
7. **Update SHACL** — delete 6 shapes (PersonShape, MinistryParticipationShape, DataRecordingActivityShape, ExchangePayloadShape, PeopleGroupEngagementShape, DataSetShape) + remove gc:hasWebsiteText property from OrganizationShape
8. **Renumber/restructure sections** in core.ttl
9. **Bump version** to v0.16.0 in `owl:versionInfo` (core.ttl already says "0.16.0" — confirm)

### Phase B: GraphDB + load script cleanup (core repo)

> **CRITICAL: Vocab migration required.** The `load-seed-data.sh` script currently loads 3 production SKOS vocabularies (organization-type, belief-type, denomination) into the Denver named graph `<https://data.global.church/denver/>`. These vocabs are actively used by the Org Bridge and must NOT be lost when Denver is cleared. They need to be migrated to a proper named graph.

10. **Update `load-seed-data.sh`** — major rewrite:
    - Remove Denver seed data load (lines 33–40)
    - Remove worker deployment vocab load (lines 83–94)
    - Move org-type, belief-type, and denomination vocab loads from Denver graph to a new vocab graph (e.g., `<https://data.global.church/vocabs/>` or the default graph)
    - Keep HIS ROG and ROR loads as-is
11. **Migrate vocabs in live GraphDB** — before clearing Denver graph, reload the 3 vocab files into their new named graph (requires GraphDB auth credentials — server now returns 401)
12. **Clear Denver named graph** from live GraphDB — `DELETE` on `<https://data.global.church/denver/>`
13. **Delete SPARQL queries** from core repo: `worker-deployment-summary.rq`, `reached-vs-unreached-workers.rq`
14. **Reload cleaned ontology** into GraphDB default graph

### Phase C: Cross-project reference cleanup

15. **Remove Denver references across the project** (see 1.9 reference list — 26 files)
    - `load-seed-data.sh` (done in Phase B)
    - CLAUDE.md files (root + ontology/)
    - Skills (gc-graphdb, gc-sparql, gc-shacl, gc-turtle-author, gc-skos-scheme)
    - Documentation (buildout docs, prompts, migration docs)
    - `core/packages/gc-sparql/src/index.ts` — remove exports for deleted queries
    - `core/packages/gc-agent/src/ontology-context.ts` — trim to reflect simplified ontology
    - CHANGELOG.md entries — leave as-is (historical)
16. **Update gc-sparql skill** — remove `at:` prefix from standard prefix list, update named graph table (remove Denver)
17. **Update gc-graphdb skill** — remove Denver from known named graphs table, add vocabs graph

### Phase D: Validate

18. **Validate Turtle syntax** — parse cleaned core.ttl and core.shacl.ttl with rdflib
19. **Validate SHACL** — run pyshacl against remaining seed data (engagement-type, claim-status, org-type, belief-type, denomination, imb vocabs)
20. **Smoke test GraphDB** — run key production SPARQL queries (org search, people group lookup, engagement claims, endorsements, resources) and confirm no breakage
21. **Update CLAUDE.md** files — note cleanup in changelogs

### Phase E: Version Tag + Downstream Version Bump

> The ontology version propagates to 3 downstream consumers via git tags. After the cleanup lands, the version must be bumped everywhere.

22. **Git tag in ontology repo** — `cd ontology/ && git tag v0.16.0 && git push origin v0.16.0`
23. **Update `core/graphdb/Dockerfile`** — `ARG ONTOLOGY_VERSION=v0.16.0` (line 3, currently v0.16.0 — confirm matches)
24. **Update `core/docker-compose.yml`** — `ONTOLOGY_VERSION: v0.16.0` (line 7, currently v0.15.1 — **needs update**)
25. **Update `apps/engage/.env.example`** — `ONTOLOGY_VERSION=v0.16.0` (currently v0.15.1 — **needs update**)
26. **Update `apps/engage/scripts/fetch-build-deps.mjs`** — fallback default `const ONTOLOGY_VERSION = process.env.ONTOLOGY_VERSION || "v0.16.0"` (line 27, currently v0.16.0 — confirm)
27. **Update Vercel env var for engage** — set `ONTOLOGY_VERSION=v0.16.0` in Vercel project settings (engage.global.church). This is a manual step in the Vercel dashboard or via `vercel env add`.
28. **Redeploy Railway GraphDB** — Railway rebuild will fetch the new tag and load the cleaned ontology
29. **Redeploy engage on Vercel** — Vercel rebuild will fetch cleaned core.ttl at v0.16.0 tag

**Version reference inventory:**

| File | Variable | Current Value | Needs Update? |
|---|---|---|---|
| `ontology/core.ttl` | `owl:versionInfo` | "0.16.0" | Confirm (already set) |
| `core/graphdb/Dockerfile` | `ARG ONTOLOGY_VERSION` | v0.16.0 | Confirm (already set) |
| `core/docker-compose.yml` | `ONTOLOGY_VERSION` | v0.15.1 | **Yes → v0.16.0** |
| `apps/engage/.env.example` | `ONTOLOGY_VERSION` | v0.15.1 | **Yes → v0.16.0** |
| `apps/engage/scripts/fetch-build-deps.mjs` | fallback default | v0.16.0 | Confirm (already set) |
| Vercel (engage) | `ONTOLOGY_VERSION` env var | v0.15.1 | **Yes → v0.16.0** (manual) |
| Git tag (ontology repo) | — | v0.15.1 (latest) | **Create v0.16.0** |
