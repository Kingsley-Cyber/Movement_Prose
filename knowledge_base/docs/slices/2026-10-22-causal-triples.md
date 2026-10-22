# Causal triples: closed predicates, seed, closure and isomorphism queries (2026-10-22)

Unparked by: the review queue exists. Lexical and catalog-grounded only; no model, no embeddings.

## Predictions (written before code)
1. Memory table `causal_triples` (subject concept, predicate, object concept, evidence, passage, confidence, who, when) with predicates limited to amplifies, dampens, triggers, inhibits, requires, breaks, compensates_for. `causal add` refuses any other predicate and an empty evidence.
2. Seed from two grounded sources: (a) the handbook's lexical requires / depends_on / conflicts_with clauses whose object text names a concept alias and whose source passage carries a concept (10 clauses were found earlier; expect 6–12 triples after both ends resolve), mapped requires→requires, depends_on→requires, conflicts_with→inhibits; (b) the catalog's `requires` satisfiers and `conflicts_with` pairs between directive concepts (17 requires rows, ~20 conflict pairs → 30–40 triples). Total seed 40–55.
3. `causal closure <concept>` walks requires/triggers/amplifies edges with a recursive CTE to depth 3; for `directive:aa_env_yutapon_cubes` it reaches `directive:aa_env_radial_fracture` and nothing beyond (the fracture's own requirement is a declared token, not a concept).
4. `causal isomorph` finds pairs of two-edge chains with the same predicate sequence over different concepts; with only seed triples it returns at least one pair among the directive conflict/requires chains, or an empty list with the right shape.
5. Retrieval is untouched; benchmark unchanged (0.836 / 0.874).

## Measured
1. `causal_triples` with the closed predicate set; `causal add` refuses other predicates and empty evidence (held, tested).
2. Seed: seed:catalog 34, seed:handbook 3 → 37 triples (prediction 2: handbook 6–12, catalog 30–40, total 40–55 → MISSED (37)). Correction made in-step: the first handbook pass chose each clause's subject by raw link weight, so the broad alias "ones" made `on_ones` the subject of three clauses; subject selection now requires a specific alias (the retrieval cap). A second defect surfaced while re-seeding: a read statement left open on the index connection (which has memory attached) held a shared lock, so the writer hit "database is locked"; the seeder now materialises its reads before writing.
3. `closure directive:aa_env_yutapon_cubes` → `directive:aa_env_radial_fracture` at depth 1 and nothing beyond (held).
4. `isomorph` returns 50 two-edge pairs; with seed data they are `inhibits>inhibits` chains among mutually conflicting directives (the right shape, trivial content until authored triples exist).
5. Benchmark unchanged at 0.836 / 0.874 (held).

## Honest reading
Catalog-grounded triples are reliable (mechanical_guidance is explicit). Handbook-seeded ones are lexical guesses with the clause as evidence and confidence 0.5; they are the start of the authored layer, not a result. Transitive closure over "requires" is the only inference running; nothing feeds retrieval until an allocator-style nuance hop reads triples, which is parked with the allocator.
