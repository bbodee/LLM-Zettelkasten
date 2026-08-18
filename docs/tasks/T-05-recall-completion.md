# T-05 — Recall completion

**Size:** M · **Depends on:** T-04 · **Status:** todo
**Binds:** SPEC §8, §8.1, §9, §11, §12 · D-001, D-010, D-019, D-020, D-021, D-024, D-032,
D-050, D-052, D-062, D-066

Closes T-01's two named seams: the index section and the flags. Delivers AC-2.

## Interface contract

```python
def index_section(slug: str, tags: Sequence[str]) -> str: ...
def build_bundle(slug: str, *,
                 logs: int = 5,
                 deep: bool = False,
                 topics: Sequence[str] | None = None) -> str: ...
def main(argv: Sequence[str] | None = None) -> int: ...
```

Vault is ambient (T-01).

CLI: `zk_recall.py <project> [--logs N] [--deep] [--topics a,b]`.

## Behaviour that must be exact

- **The index section is computed at read time, not stored** (D-010): every `index.md`
  line whose path starts with `projects/<slug>/`, plus Topics lines whose tags intersect
  the project's tags, group headers preserved. **No per-project index file exists** and
  the index format is unchanged. Recorded so a future session does not "fix" the index
  format to create the section it names.
- **Order** (§8.1): index section → `project.md` → `decisions.md` → last N logs →
  tag-matched topics. `--deep` = all logs.
- **`--topics a,b` replaces the tag join; it never unions with it** (D-070). Only the
  named topics are pulled. The tag join is D-010's computed default judgment and the flag
  is the user overruling it — a union could only add, and the union outcome is already
  reachable by omitting the flag. Naming a tag the project does not carry is **not** an
  error: reaching outside the join is the point.
- **Absent sections omitted entirely** — no empty headers, no placeholder text, no
  narration of what is missing. A project with only a charter emits a charter.
- **Hard-excludes `private/` and `archive/` regardless of flags, `--deep` included.**
- **Inventory comment** is the first line, names only what the bundle contains, and
  absent categories do not appear. It is **diagnostic by category and load-bearing by
  obligation** (D-066) — exempt from unread-deletion on **both** grounds. Its counts are
  regenerated every run and cannot go stale, which is why counts are permitted here and
  banned in a `decisions.md` summary.
- **On any skip the comment is mandatory** and names the skipped file plus the lint
  remedy (D-052). A bundle silently missing a note from the project under discussion is
  the highest-stakes omission in the system.
- **Warnings never enter the bundle** (D-024). The bundle is retrieval surface —
  everything in it is consumed as knowledge by the reading model. Vault diagnostics go to
  lint and MAY go to stderr; never to stdout, not as comments, not as headers, not as
  prose. **Bundle self-description is a different category** and is permitted (D-052).
- **Bundles never filter on status** (D-032). A completed, abandoned, or deprecated note
  is included with its status visible. Hiding content is how knowledge dies quietly.
- **Three-state messages** (§2, D-020), exit 1 on both failures:
  - UNCHARTED names the missing `project.md` and offers the charter scaffold.
  - ABSENT lists known slugs and offers a new project.
- **Empty vault gets its own message**, not a populated-vault message with an empty list
  (D-062):

  ```
  zk: this vault has no projects yet.
    Run /zk:recall <slug> to create the first one.
  ```

  `Known projects:` followed by nothing trails off and implies a lookup failed against a
  populated set. **Any message template interpolating a collection needs an
  empty-collection fixture** — the zero case is where a template degrades, and it is
  exactly the case its author never has in front of them.

## Definition of done

- `pytest` green; standing DoD applies.
- **AC-2**: `zk_recall.py` against `populated/` prints a well-formed bundle in section
  order; a note under `private/` never appears, **including with `--deep`**.
- Index section asserted to contain the project's lines and the tag-intersecting topic
  lines, and **not** another project's lines.
- `--logs N` bounds the log count; `--deep` returns all.
- `--topics a,b` **replaces** the join: a topic that the tag join would have pulled is
  **absent** unless named, and a topic outside the join is **present** when named. Both
  directions asserted — override is only proven by the narrowing case (D-070).
- Absent-section omission asserted against a charter-only project — the emitted bundle
  contains the charter and **no** `decisions.md` or topics header of any kind.
- Skip declaration asserted: a bundle built over a broken note in the target project
  carries the mandatory SKIPPED comment naming the file and the remedy.
- Empty-vault message asserted against the ground-state fixture, exit 1.
- Nothing on stdout but the bundle. Banner and diagnostics on stderr, asserted by
  capturing the streams separately.
- `tests/test_exclusion.py`'s **bundle arm** is live, closing D-053's suite. All three
  arms — read, index, bundle — now assert zero excluded paths.

## Contract deviations

*(record here during execution — none yet)*
