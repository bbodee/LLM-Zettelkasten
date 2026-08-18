# T-11 — Skill: `zk-log`

**Size:** L · **Depends on:** T-08, T-10 · **Status:** todo
**Binds:** SPEC §5, §7.0, §7.2, §7.4, §10 · D-002, D-003, D-004, D-009, D-020, D-022,
D-025, D-027, D-032, D-035, D-037, D-039, D-044, D-045, D-048, D-055, D-056

The write path, and the only place in v1 where an LLM decides what is durable. Delivers
AC-6.

## Interface contract

`skills/zk-log/SKILL.md`

```yaml
---
name: zk-log
description: >
  Records the current session into the zk vault as a dated log note, promotes durable
  choices into the project's decisions.md, updates cross-project topics, then lints and
  reindexes. Use at session wrap-up, when the user asks to log or save the session, and
  on /zk:log.
---
```

## Contract — ordered, and the order is load-bearing

1. **Draft the log** from the live conversation using the fixed sections, in order:
   `## Done`, `## Decisions`, `## Gotchas`, `## Next`. Empty sections omitted entirely.
   Directive style — terse bullets, no paragraph over two sentences, no narrative.
2. **Append to `decisions.md` BEFORE finalizing the log** (D-045). The `D-NNN` must exist
   by the time the log's pointer is written; otherwise ZK042's false positive is real and
   the check cannot do its job. Same step:
   - Read the whole file first — required anyway to detect supersession (D-002).
   - Append at the **bottom**, ID contiguous and zero-padded to three digits.
   - Write `superseded-by: D-NNN (YYYY-MM-DD)` on any entry the new one replaces, with a
     ` — <scope>` tail when the supersession is **partial** (D-056).
   - **Refresh the file's `summary:` in the same step** (D-009). It MUST be phrased as a
     **domain list** — "decisions on save format, tilemap storage, input rebinding" —
     **never a count**. A count is wrong on the very next append; a domain list only goes
     stale when a genuinely new domain appears. This refresh is the guard for an
     otherwise traceless drift (D-048).
   - Entry body ≤ 4 lines: Decision / Why / Rejected.
3. **Finalize the log.** `## Decisions` bullets are **pointers carrying a `D-NNN`**, not
   records — restatement duplicates, citation indexes.
4. **Topics**: if a cross-project insight emerged, write or update `topics/<slug>.md` —
   **reading the current version first** (D-004). Never regenerate from conversation
   context alone; never append a section that already exists.
5. **Offer `status` transitions conversationally** when the session suggests one (D-032).
   A status field nobody is prompted to update is a status field that rots.
6. **Run `zk_lint.py --fix`**, then **act on errors and mention warnings** (D-039).
   Surface the ~20-warning accumulation announcement on the **mention** rung (D-055).
7. **Run `zk_index.py`.**
8. **Report files written**, one line each. Incorporate corrections if offered, then
   re-lint and re-index.

## Behaviour that must be exact

- **Refuses to write against a non-`CHARTED` slug** (D-020) — a log has nowhere to record
  what the project is. Redirect to `/zk:recall`.
- **Never writes into `private/`.** If the user says content is sensitive, tell them to
  place it there themselves and record only a pointer-free stub.
- **Log writes are create-only** (D-027). Collisions take `-2`, `-3`, chosen as **highest
  existing plus one** — never filling a gap left by a deleted file, because filenames are
  identity and identities are not reissued. **Nothing may parse the suffix**: no script or
  skill infers collision order, count, or sequence from a filename.
- **`updated` equals the filename date, always** — it is the tamper detector for
  immutability, not a duplicate.
- **Logs are immutable testimony.** A correction is a **new log**, never an edit.
- **`summary:` is drafted dense at write time** (D-003) — state what was decided,
  learned, or changed, not that work happened; name the concrete nouns a future question
  will match against. It **must add retrieval information beyond what the heading and
  filename already carry** (D-037's routed intent). Lint's floor is a backstop for hand
  edits, not a target.
- **Skills act on errors and mention warnings** — never both alike. This is the guard
  against **skill-amplified false positives**: a human seeing a spurious warning shrugs; a
  skill told to resolve complaints *obeys*, rewriting correct prose to satisfy a miscount,
  and the vault degrades in the exact direction the rule was meant to prevent.
  This **supersedes problem.md's original unscoped "fix any residual complaints"**, which
  is already amended in place (D-040).
- **Section order is `zk-log`'s drafting contract** (ZK040's failure class is emitter
  conformance). If lint reports it, the fix is here, upstream — not in the note.
- **Duplicate sections are surfaced, never silently concatenated** — ordering and context
  between two blocks is a content decision.
- **May offer the `zk.toml` `ignore` edit conversationally** when lint reports ZK025 or
  ZK026 (D-022). Scripts state the remedy and never prompt; the skill is the rung that
  may act.
- **Slugs normalized upstream in conversation** (D-025), same as T-10.

## Definition of done

- SKILL.md exists, under 200 lines, frontmatter valid, scripts executed not pasted.
- **AC-6 end to end, live**: recall on a fresh project → scaffold → work → `/zk:log` →
  files exist, lint-clean, index updated → a **new session's** recall reflects the log.
  The new-session half is the point; verifying in the same session proves nothing about
  cross-session memory.
- The `decisions.md`-before-log sequencing is observable: the appended `D-NNN` exists on
  disk before the log file does.
- A supersession writes the marker on the old entry, with a scope tail when partial, and
  refreshes the domain-list summary in the same step.
- A non-CHARTED slug is refused with a redirect, not worked around.
- A written log lints clean, and `zk_index.py --check` is clean immediately after.
- A second log on the same date and topic lands at `-2` without overwriting the first.
- Warnings are mentioned and not acted on. Asserted by inducing a ZK012 warning on
  correct prose and confirming the text survives.

## Contract deviations

*(record here during execution — none yet)*
