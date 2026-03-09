# Ontology modularization TODOs

## Status
- Monolithic ontology has begun splitting into layered modules.
- Legacy compatibility mappings are intentionally deferred (not yet in production).
- Bridge ontologies are deferred until additional domains are introduced.

## Layering decisions (locked)
- One namespace per module (versioned IRIs).
- Strict one-way imports up to `domain-common`.
- Domain-specific cross-domain relationships should use bridge ontologies when needed.
- Full OWL restrictions remain enabled.
- Structural document restrictions belong to drawing-metadata (Option A).

## Future TODO: Legacy compatibility ontology
- Create `aec_legacy_compat_v01.ttl` when production migration starts.
- Re-declare old IRIs and map them to new module IRIs.
- Use `owl:equivalentClass` / `owl:equivalentProperty` for pure renames.
- Use `rdfs:subClassOf` / `rdfs:subPropertyOf` for narrowing changes.
- Mark deprecated legacy terms with `owl:deprecated true`.
- Add migration notes via `rdfs:comment` and `rdfs:seeAlso`.
- Implementation guidance for authoring software lives in:
	- `docs/governance/compatibility-diff-algorithm-spec.md`
	- `docs/governance/compatibility-report.schema.json`

## Future TODO: Bridge ontology governance
- Introduce bridge ontologies per cross-domain dependency (example: facade ↔ structural).
- Keep domain modules decoupled; place inter-domain links in bridge modules.
- Avoid cyclic imports between domain ontologies.
- Version bridges independently from domain modules.

## Future TODO: Migration hardening before production
- Add consistency checks (reasoner pass over composed modules).
- Add CI checks for unresolved references and cycles.
- Add deprecation policy and migration timeline for downstream users.
- Publish a mapping table from monolith terms to module terms.
