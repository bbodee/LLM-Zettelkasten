# T-09 — SPEC §13 example fixtures + rendering pass

**Size:** S · **Depends on:** T-08 · **Status:** todo
**Binds:** SPEC §13 · D-030, D-040, D-051, D-063, D-068, D-069

Closes the loop on the one document that bans instruction traps and contains four
examples. An example is instruction-shaped, so a stale one is an instruction trap living
inside SPEC.md — this chunk supplies the resident detector.

## Scope

- `tests/fixtures/vaults/examples/` as the source of §13's renderings.
- `tests/test_examples.py` — the conformance test.
- The architecture.md re-read against shipped script behaviour.

## Interface contract

```python
def spec_examples(spec_path: Path) -> dict[PurePosixPath, str]: ...
    # parses §13: each labelled vault-relative path → the ```markdown fence that follows
```

No new script. D-007 fixes the surface at five, and a renderer only tests can invoke is a
test.

## Behaviour that must be exact

- **The fixture is the source; §13 is the rendering** (D-063, D-068). Conflicts between
  an example and a rule resolve **toward the rule**.
- **Two guarantees, answering different questions.** **Lint-clean** (D-063) says the
  examples are valid. **Byte-equal** says SPEC's rendered fences *are* the fixture files,
  so what is shown and what is tested cannot drift. Byte-equality **implements** D-068's
  "structural coupling" — it is the mechanism that clause names, not a deviation from it.
- **This is the second sanctioned byte-level claim in SPEC.md** (D-069, amending D-059's
  sweep). The category, stated so a third needs no entry: **byte claims are legitimate for
  generated or coupled artifacts and never for user testimony.** `index.md` is
  machine-written (D-012); §13's fences are machine-compared against the files they
  render. Any other `byte` occurrence in SPEC.md is still a defect.
- The fixture vault carries a `projects/game-x/project.md` that §13 **does not render**.
  Without it the directory is UNCHARTED and trips ZK024, making "lint-clean forever"
  unsatisfiable. D-063 couples the example to the fixture, never the fixture to the
  example set, and §13's own criterion already explains why a charter earns no
  rendering — a closed section vocabulary is a single-rule shape, and single-rule shapes
  are their own example.
- **Annotations describing the example itself are legal** (self-description);
  **comments explaining a rule are banned** — that is restatement, and every rule has one
  normative home (D-030).
- **A shape earns a rendering when multiple conventions interact.** That criterion, not a
  census, decides what appears. `decisions.md` earns one because five conventions meet in
  it: container frontmatter, contiguous zero-padded IDs, newest-at-bottom, marker grammar,
  and a partial scope tail.
- The log example's wrapped `## Gotchas` bullet is **kept deliberately and labelled** —
  it exercises CommonMark continuation and sits exactly at the two-sentence cap.
- Regeneration is a **manual copy verified by a test**, not a generator. The test is what
  makes the coupling structural.

## Definition of done

- `pytest` green; standing DoD applies.
- Every note in `examples/` lints **clean** — zero errors, zero warnings.
- Each §13 fence is **byte-equal** to the fixture file it names. Editing either without
  the other fails the test.
- The `status: active` defect D-063 found is confirmed absent: the log example carries no
  `status` field, and neither does `decisions.md`.
- A deliberate one-character edit to a fixture fails `test_examples.py`. Asserted in the
  test suite itself, so the detector is shown to detect.
- **architecture.md re-read against shipped behaviour.** Its script-layer sections
  described unbuilt code until now; every claim is re-traced to SPEC, a decision, or
  problem.md, and any that drifted is corrected in place. `rendered-against:` bumped.
  D-067's lesson applies directly — rendering forces tracing, and tracing surfaces
  contradictions that reading does not.
- `docs/plan.md` marks T-01 through T-09 `done` and the script phase closed.

## Contract deviations

*(record here during execution — none yet)*
