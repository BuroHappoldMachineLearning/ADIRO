# Compatibility Guard: Diff Algorithm Specification

## Purpose
Define a deterministic algorithm that compares two ontology versions and classifies changes as non-breaking, potentially-breaking, or breaking, then proposes compatibility actions.

## Inputs
- `oldOntologyGraph`: previous release graph (RDF triples)
- `newOntologyGraph`: edited graph (RDF triples)
- `settings`:
  - `mode`: `off | warn | enforce`
  - `productionTarget`: boolean
  - `renameSimilarityThreshold`: float (default `0.85`)

## Outputs
- `compatibilityReport` (JSON object)
- optional generated compatibility graph (`compatGraph`)

## Processing Pipeline
1. Parse and normalize RDF graphs.
2. Build symbol tables (`classes`, `properties`, `individuals`) for old/new.
3. Match equivalent terms and detect renames/moves.
4. Compute structural and axiom deltas.
5. Classify each delta by compatibility severity.
6. Generate suggested compatibility mappings.
7. Produce report and blocking decision.

## Step 1 — Parse and Normalize
Normalization rules:
- Expand prefixes to full IRIs.
- Canonicalize blank-node restrictions where possible.
- Normalize literal datatypes (`xsd:int` vs `xsd:integer` handling strategy must be explicit).
- Treat label/comment-only changes separately from semantic changes.

## Step 2 — Build Symbol Tables
For each graph, build indexed sets:
- `C`: all terms with `rdf:type owl:Class`
- `OP`: all terms with `rdf:type owl:ObjectProperty`
- `DP`: all terms with `rdf:type owl:DatatypeProperty`
- `AP`: all terms with `rdf:type owl:AnnotationProperty`
- `I`: individuals (non-class/property terms used as instances)

Store per-term metadata:
- local name
- namespace
- labels
- direct superclasses / superproperties
- domain/range
- restrictions attached to the term

## Step 3 — Term Matching (Rename/Move Detection)
### 3.1 Exact match
If IRI exists in both versions, map directly.

### 3.2 Candidate renamed/moved match
For each old term missing in new:
- Candidate new terms of same kind (class/property type)
- Similarity score:
  - local-name similarity (Levenshtein/Jaro-Winkler)
  - label similarity
  - neighborhood similarity (superclasses, domain/range, restrictions)

If best score >= threshold and unique -> mark as `rename_or_move_candidate`.

### 3.3 Confirmation rules
Promote candidate to `renamed`/`moved` if:
- type unchanged, and
- at least one structural signature overlap (superclass/domain/range/restriction predicate).

Otherwise classify as `removed + added`.

## Step 4 — Delta Computation
Detect the following delta records:
- `TERM_ADDED`
- `TERM_REMOVED`
- `TERM_RENAMED`
- `NAMESPACE_MOVED`
- `TYPE_CHANGED` (e.g., datatype property -> object property)
- `DOMAIN_CHANGED`
- `RANGE_CHANGED`
- `SUPERCLASS_CHANGED`
- `SUPERPROPERTY_CHANGED`
- `RESTRICTION_ADDED`
- `RESTRICTION_REMOVED`
- `RESTRICTION_TIGHTENED`
- `RESTRICTION_LOOSENED`
- `ANNOTATION_CHANGED`

## Step 5 — Severity Classification
Default mapping:
- Non-breaking:
  - `TERM_ADDED`, `ANNOTATION_CHANGED`, `RESTRICTION_LOOSENED`
- Potentially-breaking:
  - `DOMAIN_CHANGED`, `RANGE_CHANGED`, `SUPERCLASS_CHANGED`, `RESTRICTION_ADDED`, `RESTRICTION_TIGHTENED`
- Breaking:
  - `TERM_REMOVED`, `TERM_RENAMED`, `NAMESPACE_MOVED`, `TYPE_CHANGED`, `SUPERPROPERTY_CHANGED` (if constraints imply old assertions become invalid)

Note: implementers may override with policy rules file.

## Step 6 — Compatibility Action Suggestions
For each breaking/potentially-breaking item, generate `suggestedAction`:

### 6.1 Renamed/moved class
- Add legacy term in compat graph.
- Add `owl:equivalentClass` to new term.
- Add `owl:deprecated true`.

### 6.2 Renamed/moved property
- Add `owl:equivalentProperty`.
- Add `owl:deprecated true`.

### 6.3 Removed with narrower replacement
- Add `rdfs:subClassOf` or `rdfs:subPropertyOf` mapping.
- Mark legacy deprecated.

### 6.4 Type changed property
- No safe automatic equivalence.
- Mark as `manual_intervention_required`.

### 6.5 Tightened restrictions
- Keep warning; optionally add migration hint only.

## Step 7 — Decision Logic
Given maximum severity in report:
- `off`: never block.
- `warn`: show warning panel; allow continue.
- `enforce`: block if breaking exists and compatibility generation not accepted.

Additional CI rule:
- if `productionTarget=true` and breaking deltas exist with no compat output -> fail.

## Pseudocode
```text
function evaluateCompatibility(oldGraph, newGraph, settings):
    old = normalize(oldGraph)
    new = normalize(newGraph)

    oldTable = buildSymbolTable(old)
    newTable = buildSymbolTable(new)

    termMap = exactMatches(oldTable, newTable)
    renameCandidates = detectRenameMoveCandidates(oldTable, newTable, termMap, settings.renameSimilarityThreshold)
    termMap = resolveCandidates(termMap, renameCandidates)

    deltas = computeDeltas(old, new, oldTable, newTable, termMap)

    findings = []
    for delta in deltas:
        severity = classify(delta)
        action = proposeCompatibilityAction(delta)
        findings.append({delta, severity, action})

    maxSeverity = max(findings.severity)
    decision = decide(settings.mode, settings.productionTarget, maxSeverity, findings)

    compatGraph = null
    if decision.generateCompatibility:
        compatGraph = generateCompatOntology(findings)

    return { findings, decision, compatGraph }
```

## Data Structures (recommended)
- `TermDescriptor`
  - `iri`, `kind`, `labels`, `namespace`, `signatures`
- `DeltaRecord`
  - `type`, `oldTerm`, `newTerm`, `details`
- `Finding`
  - `deltaId`, `severity`, `impact`, `suggestedAction`, `autoFixAvailable`

## Edge Cases
- Blank-node heavy ontologies: restriction diffing should compare normalized patterns, not blank-node IDs.
- Multiple equally similar rename candidates: mark ambiguous and require user confirmation.
- Split/merge terms: produce 1:N or N:1 mapping records; avoid automatic `equivalentClass` unless user confirms.
- Imported ontologies: by default diff local ontology namespace only; optional deep mode can include imported changes.

## Performance Notes
- Expected complexity is dominated by rename candidate matching.
- Use indexed lookup by term kind and label tokens.
- For large ontologies, cap candidate set by namespace + token prefilter before expensive similarity scoring.

## Authoring Tool UX Contract
When findings exist:
- show grouped by severity
- each finding exposes:
  - why it is risky
  - whether autofix exists
  - proposed compat triples preview
- user chooses:
  - `Proceed`
  - `Generate compatibility ontology`
  - `Cancel and edit`

## Minimal Test Matrix
- Add-only change -> non-breaking
- Rename class -> breaking + autofix
- Rename property -> breaking + autofix
- Remove property with replacement -> breaking + mapped subProperty action
- Tighten cardinality -> potentially-breaking warning
- Datatype -> object property change -> breaking, manual action required
