# Ontology Design Principles for GC-Core

> A practical decision framework for the Global.Church ontology — grounded in DOLCE, PROV-O, and ontology engineering best practices. Written for the strategy coordinator role: not academic completeness, but working fluency for making and defending design calls.
>
> **DOLCE reference:** Borgo, S., Ferrario, R., Gangemi, A., Guarino, N., Masolo, C., Porello, D., Sanfilippo, E.M., & Vieu, L. (2022). *DOLCE: A descriptive ontology for linguistic and cognitive engineering.* Applied Ontology, 17(1), 45–69. Local copy: `gc-core/reference/standards/DOLCE-2308.01597v1.pdf`

---

## 0. How GC-Core Uses DOLCE

Before the design principles themselves, it's worth being explicit about the *role* DOLCE plays in this project. The DOLCE paper identifies four ways an upper ontology can be used:

1. **As an upper ontology** — your domain classes formally subclass DOLCE categories.
2. **As an expressive axiomatic theory** — you import DOLCE's full axiomatization and lean on a reasoner.
3. **As a coherence stabilizer** — you use DOLCE's distinctions to pressure-test your modeling decisions, without importing it.
4. **As a source of ontology design patterns** — you lift reusable structural patterns (participation, quality-of-a-thing, etc.) and apply them locally.

**GC-Core uses approaches 3 and 4.** We don't import DOLCE directly or subclass its categories in Turtle. Instead, we use DOLCE's category system as a *litmus test* — "does this concept fit cleanly into one DOLCE bucket?" — and we adopt its structural patterns (qualities inhering in endurants, participation linking agents to activities) as recurring shapes in our domain model. PROV-O remains the formal type system; DOLCE is the design conscience.

This means every principle below that references DOLCE is a *design heuristic*, not a formal constraint. If a GC-Core concept doesn't fit neatly into one DOLCE category, that's a signal to re-examine the modeling decision — not an error to paper over.

---

## 1. The Identity Test — "Is this a thing, or a fact about a thing?"

This is the single most common design question, and DOLCE gives you a clean way to answer it.

**Make it a class** if it has identity independent of anything else. Can you point to it? Does it persist over time? Could two people disagree about its properties while agreeing it exists?

**Make it a property** if it only makes sense *in relation to* something else. It describes, measures, or classifies — it doesn't stand on its own.

DOLCE formalizes this distinction through **dependence**: a quality (like a color, a weight, or an engagement score) is *specifically dependent* on its host — it can't exist without the thing it inheres in. An endurant (like a church or an organization) is *independent* — it carries its own identity criteria. If the thing you're modeling couldn't exist without some other specific thing, it's a quality or a role, not an independent entity.

GC-Core examples:

- `gc:Church` — clearly a class. A church has identity, persists over time, and has properties that change (pastor, location, membership count).
- `gc:churchName` — clearly a property. A name doesn't exist independently of the church it names.
- `gc:Endorsement` — this is the interesting case. You *could* model "BGEA endorses First Baptist" as a simple boolean property on Church. But an endorsement has its own attributes (date granted, expiration, type, the endorsing body). Once a "fact about a thing" starts accumulating its own facts, promote it to a class. This is called **reification** — turning a relationship into a first-class entity.

**The rule of thumb:** If you need more than one property to describe the relationship between two things, reify it into a class.

---

## 2. The DOLCE Category System

DOLCE's top-level taxonomy gives you four buckets. Every concept in GC-Core should fit cleanly into one:

| DOLCE Category | What it is | GC-Core examples |
|---|---|---|
| **Endurant** | Things that persist through time — you can observe the whole thing at any instant | Church, Organization, Person, PeopleGroup |
| **Perdurant** | Things that unfold over time — you can only observe a temporal part at any instant | MinistryActivity, DataRecording, ExchangePayload transfer |
| **Quality** | Properties that inhere in something — they depend on a host entity for existence | engagementStrength, evangelicalPercentage, population |
| **Abstract** | Things outside of space and time — classification systems, sets, regions | Language codes (ROL), Religion codes, ROP3 concepts, SKOS schemes |

**Why this matters for GC-Core:** Your current task list includes several decisions this resolves directly:

- **Language, Religion → Abstract.** They're classification reference data, not things with provenance histories. This is why removing `prov:Entity` from them is correct — DOLCE would never put a classification code in the same bucket as a church or a ministry activity.
- **EngagementState → Quality.** An engagement state is a measurement that inheres in a people group at a point in time. It doesn't float around independently. DOLCE would model it as a quality, which aligns with your current pattern of reifying it as a class (because it has multiple dimensions — phase, strength, evangelical %) while keeping it attached to a people group via `gc:hasEngagementState`.
- **EngagementAssessment → Perdurant.** The *act* of assessing engagement is an event that happens at a time, carried out by an agent. Distinct from the state it measures.

**When you're stuck**, ask: "If I froze time right now, could I observe this thing in its entirety (endurant), only a slice of it (perdurant), or does it not exist in time at all (abstract)?"

### 2a. Endurant Subcategories — Social Objects and Agents

DOLCE doesn't treat all endurants alike. The subcategory hierarchy matters for GC-Core because most of our domain lives in one specific branch: **social objects**.

```
Endurant
├── Physical Endurant (PED)
│   ├── Agentive Physical Object (APO) — things with intentionality: a person
│   └── Non-Agentive Physical Object (NAPO) — things without: a building, a book
├── Non-Physical Endurant (NPED)
│   ├── Social Object (SOB) — constituted by social agreement/convention
│   │   ├── Agentive Social Object (ASO) — orgs, institutions with collective intentionality
│   │   └── Non-Agentive Social Object (NASO) — laws, norms, plans, datasets
│   └── Mental Object (MOB) — beliefs, intentions (individual cognition)
└── Arbitrary Sum (AS) — collections with no unified identity
```

**GC-Core mapping:**

- `gc:Church`, `gc:Organization` → **Agentive Social Object (ASO)**. A church is not a physical building — it's a socially constituted entity that can act, decide, and bear responsibility. It's "agentive" because it has collective intentionality (it can commit to serving a people group, endorse another church, make strategic decisions). This aligns with our PROV-O mapping to `prov:Agent`.
- `gc:Person` → **Agentive Physical Object (APO)**. A person is a physical being with individual intentionality.
- `gc:PeopleGroup` → **Social Object (SOB)**, arguably non-agentive. A people group is a socially recognized grouping — it doesn't have collective intentionality the way an organization does. It can't "decide" anything. It's constituted by shared ethnolinguistic and cultural characteristics, which are themselves social constructs. This is why people groups sit in the reference/classification tier more naturally than in the agentive tier, even though GC-Core currently maps them to `prov:Agent` — a known tension worth revisiting.
- `gc:DataSet`, `gc:ExchangePayload` → **Non-Agentive Social Object (NASO)**. These are information artifacts — constituted by social agreement about what their symbols mean, but not capable of agency.
- `gc:Location` → **Physical Endurant (PED)**, or arguably a GeoSPARQL `geo:Feature`. A geographic location is a physical region, not a social construct. This is another reason PROV-O parentage feels forced for Location — a mountain or set of coordinates doesn't have a provenance story in the same way a church record does.

**Why this matters:** The agentive vs. non-agentive distinction directly tells you which things can meaningfully be `prov:Agent`. If something can't intentionally act, it shouldn't be an agent. This is a useful cross-check when deciding PROV-O parentage.

### 2b. Perdurant Subcategories — Events, States, and Processes

DOLCE distinguishes perdurants by whether they're *stative* (homeomeric — every temporal part is the same kind of thing) or *eventive* (non-homeomeric — they have distinct phases):

```
Perdurant
├── Stative
│   ├── State (STV) — a situation that holds: "this people group is unengaged"
│   └── Process (PRO) — an ongoing activity with no inherent endpoint: "discipleship"
└── Eventive
    ├── Achievement (ACH) — instantaneous transitions: "church was planted"
    └── Accomplishment (ACC) — activities with a definite endpoint: "Bible translation completed"
```

**GC-Core mapping:**

- `gc:MinistryActivity` → typically an **Accomplishment** (has temporal extent and a completion point) or a **Process** (ongoing, no inherent endpoint). The distinction matters if you ever need to model "is this activity completed or ongoing?" — that's a stative vs. eventive question.
- `gc:DataRecording` → **Achievement or Accomplishment.** The act of recording data is an event with a definite structure (start, capture, end).
- `gc:EngagementAssessment` → **Achievement.** An assessment is a judgment made at a point in time. It produces an `EngagementState` (a quality), but the assessment act itself is an instantaneous-ish event.
- An engagement commitment being fulfilled → **Accomplishment.** It has a beginning, duration, and a definable completion.

**Practical value:** When you find yourself unsure whether to model something as "a thing that happened" (perdurant) vs. "a condition that holds" (quality/state), DOLCE's stative/eventive split helps. If it's stative and depends on a host entity, it's probably a quality. If it has internal temporal structure (phases, participants at different times), it's a perdurant.

### 2c. Qualities and Quality Spaces — Values vs. Measurements

DOLCE draws a critical distinction that GC-Core benefits from: a **quality** is an individual property that inheres in a specific entity (this church's engagement strength), while a **quality space** (or **region**) is the abstract dimension where that quality's value lives (the 1–5 scale itself).

```
Quality (individual)                    Region / Quality Space (abstract)
─────────────────────                   ──────────────────────────────────
"Somali people's engagement             "The 1–5 JP scale" (a value space)
 strength = 2"  (inheres in the          — exists independently of any
 Somali people group)                    particular people group)
```

**GC-Core mapping:**

- The `gc:EngagementState` of a specific people group is a **quality individual** — it depends on that people group for its existence.
- The JP Scale (1–5), the GSEC scale, the SPI scale — these are **quality spaces** (abstract regions). In practice, GC-Core models these as SKOS ConceptSchemes, which is the right RDF pattern for the abstract value-space side of this distinction.
- `gc:evangelicalPercentage` as a property → the property definition describes the quality space (0–100%, decimal); each triple using it instantiates a quality individual.

**The practical upshot:** When you model a measurement, you're always dealing with two things: the individual measurement (quality) and the scale it's measured on (quality space). Keep them separate. The SKOS schemes (engagement phases, GSEC codes) define the scales; the triples on specific people groups instantiate measurements on those scales. Conflating the two — putting scale definitions and instance data in the same modeling pattern — leads to confusion about whether you're defining a vocabulary or recording a fact.

---

### 2d. Participation — How Endurants Relate to Perdurants

DOLCE formalizes the relationship between things-that-persist (endurants) and things-that-happen (perdurants) through **participation**: an endurant *participates in* a perdurant during a time interval. This is not just "X is related to Y" — it's the specific claim that a persistent thing was involved in a time-bounded occurrence.

**GC-Core mapping:**

- An `gc:Organization` (endurant) *participates in* a `gc:MinistryActivity` (perdurant). This is exactly what `gc:MinistryParticipation` models — and the fact that we reified it into a class (rather than a simple property) is justified because participation has its own attributes (role, time period, contribution type).
- A `gc:Person` (endurant) *participates in* a `gc:DataRecording` (perdurant) as the assessor.
- A `gc:Church` (endurant) *participates in* an endorsement relationship — though here the endorsement is modeled as an entity rather than an activity, because the emphasis is on the persistent social agreement rather than the event of endorsing.

**The DOLCE constraint to remember:** Participation is always temporally qualified. An organization participates in an activity *during a time interval*. If you're modeling a relationship between an endurant and a perdurant and you can't meaningfully attach a time interval, reconsider whether it's truly participation — it might be classification, constitution, or some other relation.

### 2e. Constitution — When One Thing Makes Up Another

DOLCE distinguishes **constitution** from identity. A physical church building *constitutes* the church (social object) but is not identical to it — the church could move buildings and remain the same church. Constitution is a non-identity relation between co-located entities at different ontological levels.

**GC-Core relevance:** This matters when modeling the relationship between physical and social aspects of churches. The building at 123 Main St is not the same thing as First Baptist Church — First Baptist is a social object constituted (at a given time) by a particular congregation, meeting in a particular building. If the church splits, relocates, or merges, the social entity's identity story is independent of the physical location's story. This is why `gc:hasLocation` is a relationship to a `gc:Location`, not an inherent property — the location can change while the church's identity persists.

---

## 3. The Provenance Litmus Test — "Does this thing have a story?"

This is GC-Core's defining design principle, inherited from PROV-O as your core type system.

**Give it PROV-O parentage** (Entity, Activity, or Agent) if you need to answer: *Who said this? When? Based on what evidence? How has it changed?*

**Don't give it PROV-O parentage** if it's reference data that just *is* — classification vocabularies, code lists, controlled terms. Nobody "generated" the concept of the Somali language; it's a stable reference point that data links *to*.

This produces a clean two-tier architecture:

```
PROV-O tier (domain data — has provenance)
├── gc:Church          → prov:Agent    — "CIL submitted this record on 2024-03-15"
├── gc:MinistryActivity → prov:Activity — "recorded by Denver org, March 2024"
├── gc:DataRecording   → prov:Activity — "generated this engagement assessment"
└── gc:EngagementAssessment → prov:Entity — "derived from JP data, assessed by agent X"

Reference tier (classification data — no provenance)
├── skos:ConceptScheme (ROP3, ROL, religion codes)
├── skos:Concept instances (individual people codes, language codes)
└── Controlled vocabularies (engagement phases, resource statuses)
```

**The test:** If you can't imagine writing a meaningful `prov:wasGeneratedBy` triple for an instance, it probably doesn't belong in the PROV-O tier.

---

## 4. The Reuse Principle — "Has someone already defined this well?"

Ontology engineering's version of "don't reinvent the wheel." Before minting a new `gc:` term, check whether an established vocabulary already covers it.

**Hierarchy of preference:**

1. **Use the external term directly** if it means exactly what you need. Example: `prov:startedAtTime` instead of `gc:dateTimeOfActivity`.
2. **Subclass or subproperty** if you need domain-specific semantics on top of a general concept. Example: `gc:MinistryActivity rdfs:subClassOf prov:Activity` — preserves interop while adding domain meaning.
3. **Map via `skos:exactMatch` / `owl:sameAs`** if two systems define the same concept independently. Example: linking GC-Core people groups to JP people groups.
4. **Mint a new `gc:` term** only when nothing else fits.

**For GC-Core specifically**, the relevant external vocabularies are:

- **PROV-O** — provenance (your core type system)
- **SKOS** — classification schemes, concept hierarchies (ROP, ROL, religion codes)
- **GeoSPARQL** — locations, spatial relationships (future alignment for `gc:Location`)
- **Dublin Core** — basic metadata (title, description, date, creator)
- **FOAF** — people and organizations (overlaps with PROV-O Agent)

**The payoff:** Every alignment you make is a free interoperability win. If `gc:participationRole rdfs:subPropertyOf prov:hadRole`, then any PROV-O tool on earth can see your role assignments without knowing anything about GC-Core.

---

## 5. The Namespace Ownership Principle — "Who is the authority?"

If a concept was designed and is maintained by an external organization, it should live in their namespace, not yours.

**GC-Core (`gc:`) should own:**
- Domain concepts specific to the Global.Church coordination use case (Church, MinistryParticipation, EngagementClaim, DataSet)
- Relationships that connect external vocabularies in ways unique to your architecture (hasPeopleClassification, servesPeopleGroup)

**External namespaces should own:**
- Concepts they designed, even if you use them heavily. The 3D Insight model belongs to Joshua Project → `jp:`. People codes belong to HIS → modeled as SKOS concepts under `data.global.church/his/rop3/`. Language codes → ROL scheme.

**The test:** If the external org changed their definition tomorrow, would your use of the concept need to change to stay correct? If yes, they own it.

This is exactly why the JP namespace migration is on your task list — GC-Core currently mints `gc:EngagementState` and `gc:EngagementAccelerator` as its own, but JP designed these and is the authority on what the 12 accelerators mean.

---

## 6. The Closed-World vs. Open-World Awareness

This catches people coming from relational databases. In SQL, if a column is empty, the fact is false or unknown. In RDF/OWL, the **open-world assumption** applies: absence of a statement means *we don't know*, not *it's false*.

**Practical implications for GC-Core:**

- **You can't query for "people groups with no engagement."** You can only find people groups where no `gc:hasEngagementState` triple exists — which could mean unengaged *or* unreported. This is why your gap analysis queries need to be framed carefully: "no *known* engagement" rather than "no engagement."
- **Don't model absence as presence.** Avoid patterns like `gc:isEngaged false`. Instead, let the absence of an engagement triple speak for itself, and use SPARQL `FILTER NOT EXISTS` to find gaps.
- **SHACL bridges the gap.** Your SHACL shapes enforce closed-world constraints at *data validation time* (e.g., "every Church MUST have a name"). The ontology stays open-world, but the shapes say "if you're submitting data to us, these fields are required." This two-layer pattern — open ontology, constrained shapes — is exactly right for a multi-org ecosystem.

---

## 7. The Minimalism Principle — "Every triple should earn its place"

From Semantic Arts (the gist methodology): resist the urge to model everything you *could* and only model what you *need to query or reason over*.

**Ask before adding any class or property:**

1. Is there a SPARQL query or inference rule that needs this?
2. Will real data populate this?
3. Does this serve the core coordination use case (finding gaps, connecting organizations, tracking engagement)?

If the answer to all three is no, it goes in the backlog, not the ontology.

**GC-Core example:** The flat external identifier properties (`gc:jpPeopleId`, `gc:imbPeopleId`, `gc:people3Id`) were added early but are now redundant — the same links are resolved through the SKOS concept hierarchy. They don't earn their place anymore, which is why removing them is on the task list.

---

## 8. The Named Graph Boundary — "Whose truth is this?"

Specific to GC-Core's multi-organization architecture. Every assertion lives in a named graph scoped to its source organization.

**Design implications:**

- **The same people group can have different engagement assessments in different graphs.** CIL might say Phase 3, IMB might say Phase 2. Neither is "wrong" — they're different organizational perspectives. The ontology doesn't resolve this; the query layer and UI present both with provenance.
- **Cross-graph statements need explicit justification.** If a triple appears in the default graph (or a `gc:` graph), it implies Global.Church is asserting it as canonical. Reserve this for things like `owl:sameAs` links and SKOS mappings that GC-Core maintains as the integration layer.
- **SHACL shapes validate per-graph.** An organization's data submission is validated against shapes before loading into their named graph. Different orgs could theoretically have different shape requirements (strict vs. lenient), though you're using a single shape set for now.

---

## 9. Concept Evolution — "What happens when meanings shift?"

DOLCE addresses a problem GC-Core will inevitably face: concepts evolve over time. A term like "unreached" means something subtly different to Joshua Project, IMB, and a local denomination — and those meanings shift as methodology improves. DOLCE handles this by treating concepts as having **temporal extent** and **social constitution**: a concept's meaning is constituted by the community that uses it, and that constitution can change.

**Practical implications for GC-Core:**

- **Version your classification schemes.** When JP updates its engagement scale definitions, don't silently overwrite — create a new version of the SKOS ConceptScheme and preserve the old one. Named graphs already give you temporal isolation per data load; extend that thinking to vocabularies.
- **Don't assume stable identity for socially constituted concepts.** "Evangelical" means different things in different contexts. If two organizations define the term differently, model them as different SKOS concepts linked by `skos:relatedMatch` rather than forcing them into one concept with `skos:exactMatch`.
- **Use `skos:changeNote` and `dcterms:modified`** to track when and why a concept's definition changed. This preserves the history of meaning evolution that DOLCE tells us to expect.

**The DOLCE insight:** Social objects (including concepts, classification schemes, and organizational definitions) are constituted by agreement, and agreements change. An ontology for multi-organization coordination must anticipate this by building versioning and provenance into its vocabulary management, not just its data.

---

## 10. The Multiplicative Principle — "Don't confuse categories with instances"

DOLCE warns against what it calls the "multiplicative effect" — the temptation to create a new *class* for every combination of properties, when what you really need is instances classified along independent dimensions.

**The anti-pattern:** Creating classes like `gc:UnreachedPeopleGroupInAfricaWithNoBible`. This multiplies the class hierarchy combinatorially and makes the ontology unmaintainable.

**The DOLCE approach:** Keep orthogonal classification dimensions separate and let SPARQL queries compose them at runtime:

- People groups are classified by engagement phase (SKOS concepts on the JP scale)
- People groups are classified by geography (ROG SKOS concepts)
- People groups are classified by Bible status (a separate property)
- "Unreached groups in Africa with no Bible" is a *query*, not a *class*

**GC-Core already does this well** with its SKOS-based classification scheme approach — engagement, geography, language, religion, and people codes are all independent classification axes. The principle to remember: if you're tempted to create a new class that combines two or more classification dimensions, you almost certainly want a query pattern instead.

---

## 11. The Namespace Incubation Principle — "Prove it in one org's namespace before promoting to core"

When a contributing organization introduces a new vocabulary (SKOS scheme, property, or class) that doesn't yet exist in GC-Core, it should **enter the ontology in that org's namespace** — not in `gc:`.

**The pattern:**

1. **Incubate** — The new concept lives in the org's namespace (e.g., `imb:TargetAudienceScheme`, `jp:EngagementAccelerator`). The org is the authority on what the concept means and what values it contains.
2. **Observe** — As other bridges and data sources are integrated, watch for convergence. Does a second organization need the same classification dimension? Do their values overlap or align?
3. **Promote** — When multi-org consensus emerges (two or more organizations reference compatible concepts), migrate the vocabulary to `gc:` using the namespace migration skill. Add `skos:exactMatch` links back to the org-specific versions for backward compatibility.

**Why this matters:**

- **Avoids premature generalization.** A concept that seems universal when you've only seen one org's data often turns out to be org-specific. IMB's "Affinity Regions" don't map 1:1 to any standard geography; JP's engagement accelerators are JP's intellectual framework. Putting these in `gc:` prematurely implies false consensus.
- **Keeps `gc:` authoritative.** The `gc:` namespace should only contain concepts that Global.Church maintains as the integration authority. If IMB changes their audience categories tomorrow, that's IMB's business — it shouldn't require a `gc:` ontology version bump.
- **Makes promotion a deliberate act.** Moving from `imb:` to `gc:` requires a namespace migration (with the `gc-namespace-migrate` skill), which naturally triggers a design review, SHACL updates, and documentation. This ceremony is appropriate for concepts being elevated to shared infrastructure.

**Examples:**

- `imb:TargetAudienceScheme` (8 concepts: Men, Women, Students, etc.) — stays in `imb:` until a second org needs audience tagging. If JP or Wycliffe later adopt compatible audience concepts, evaluate promotion to `gc:TargetAudienceScheme`.
- `imb:AffinityRegionScheme` (11 IMB affinity regions) — definitively IMB's organizational construct. Unlikely to promote since standard geography (ROG) serves the cross-org case.
- `jp:EngagementAccelerator` — already correctly in `jp:` namespace. Would only promote if multiple orgs adopted the same 12-accelerator framework.

**The test:** "If only one organization uses this concept today, it belongs in their namespace. If you're tempted to put it in `gc:` for convenience, ask: would a *second* org recognize and adopt this exact vocabulary?"

---

## 12. Quick Decision Checklist

When you're staring at a modeling question, run through this:

| Question | If yes → | If no → |
|---|---|---|
| Does it have identity on its own? | Class | Property |
| Does it accumulate its own properties? | Class (reify it) | Property |
| Which DOLCE category? | Assign to endurant / perdurant / quality / abstract | Re-examine — if it doesn't fit one bucket, the concept may be conflating two things |
| If endurant: is it agentive? | Can be `prov:Agent` | Probably `prov:Entity` or reference tier |
| If endurant: is it social or physical? | Social → constituted by agreement, may evolve | Physical → more stable identity criteria |
| If perdurant: stative or eventive? | Stative → quality/state; Eventive → activity/event | |
| If quality: what's the quality space? | Model the scale as SKOS; instances as triples | |
| Does it have a provenance story? | PROV-O tier | Reference tier (SKOS) |
| Did an external org design it? | Their namespace | `gc:` namespace |
| Does an established vocabulary cover it? | Reuse (direct, subclass, or mapping) | Mint new term |
| Does a real query need it? | Add it | Backlog it |
| Could orgs disagree about it? | Named graph isolation | Default graph is fine |
| Are you creating a class for a combination of dimensions? | Stop — use a query pattern instead | Class is probably justified |
