# Review lenses and the shard prompt

Four lenses, ranked. A small diff uses the first N; a deadline cuts from the bottom. The ranking is by how
expensive the class of bug is to find later, not by how often it fires.

| # | File | Lens | Normative docs the shard must read first |
|---|---|---|---|
| 01 | `01-correctness.md` | Correctness and the forms/views boundary | [AGENTS.md](../../../../AGENTS.md) (hard rule), [architecture.md](../../../../docs/ai/architecture.md) § Forms vs Views |
| 02 | `02-django-data.md` | Data layer, querysets and migrations | [architecture.md](../../../../docs/ai/architecture.md) |
| 03 | `03-tests.md` | Test honesty and coverage substance | [testing.md](../../../../docs/ai/testing.md) |
| 04 | `04-frontend.md` | HTMX/Tailwind conformance and spec/simplification | [design.md](../../../../docs/ai/design.md), [architecture.md](../../../../docs/ai/architecture.md) |

### What each lens is looking for

**01 Correctness and the forms/views boundary.** Logic that is wrong for inputs the story will actually
produce. Off-by-one and inverted conditions in the changed code. And the project's one hard rule:
`ModelForm.save()` must only validate and persist - a `transaction.atomic()` boundary or a
`handle_message()`/side-effect call inside `save()` instead of the view's `form_valid()` (called after the
atomic block exits) is a confirmed finding every time, not a judgement call (see #333,
docs/ai/architecture.md § Forms vs Views).

**02 Data layer, querysets and migrations.** N+1 queries in a loop. Missing `select_related`/
`prefetch_related` on a path the story made hot. A migration that will not apply on an existing database,
or model changes with no migration at all. Two migrations in the same app both claiming the next leaf
number (`migration-numbers.sh` catches the cross-worktree case; this lens catches it within the diff
itself). Money/decimal fields handled with float arithmetic anywhere in the change.

**03 Test honesty and coverage substance.** Coverage that is reached without asserting anything.
First-party code mocked where the real object could be exercised. Branches covered by patching the thing
under test rather than exercising it. Tests that would still pass if the story's change were reverted.

**04 HTMX/Tailwind conformance and spec/simplification.** A template or view that doesn't follow this
project's htmx/design conventions in `docs/ai/design.md` (existing component patterns, the palette, the
established htmx request/response shape). Requirements in `spec.md` that the diff does not actually
satisfy, and behaviour in the diff that nothing in `spec.md` asked for. Code duplicated from somewhere it
could have been reused. Abstraction introduced for one caller. Dead branches left behind by the change.

## Shard prompt template

Fill the placeholders and pass this as the `Agent` prompt. Keep the wording - the incremental-write rule
and the verify stage are what make a dying shard cheap and a surviving shard trustworthy.

---

You are reviewing one lens of a code change in the yamsa repository at `<REPO_ROOT>`.

**Your deliverable is the file `<RUN_DIR>/review/<SHARD_FILE>`, not your reply.** Nothing you return in
chat is read. Write findings into that file as you confirm them, one at a time, appending - never buffer
them to the end. If you are killed halfway through, everything already written still counts, and that is
the point.

The change under review is `git diff <BASE>...HEAD`<SCOPE_NOTE>. Review only that diff. Problems on lines
this change did not touch are out of scope.

**Your lens: <LENS_NAME>.** <LENS_DESCRIPTION>

Read these before you review - they are normative for this project: <LENS_DOCS>. Also read
`<RUN_DIR>/spec.md` for what the change was supposed to do.

Work in two stages, per finding:

1. **Find.** Scan the diff through your lens and note candidates.
2. **Verify.** For each candidate, go back to the actual code and try to *refute* it. Read the
   surrounding function, the callers, the tests. Then score your confidence 0-100 that it is a real defect
   a reviewer should raise: 100 you confirmed it end to end, 80 you verified it and it will bite in
   practice, 50 real but a nitpick, 25 you could not verify it, 0 refuted. **Write it to the file only if
   it scores 80 or higher.** Default to refuting when you are unsure - a false positive costs the
   maintainer more time than a missed nitpick.

Do not report: anything ruff, djlint or pytest coverage already catches (they run before you and are
green); formatting and import order; pre-existing problems; style a senior engineer would not raise in
review; changes that are obviously intentional parts of the story.

Append each surviving finding in exactly this format:

```finding
file: apps/transaction/forms/transaction.py
line: 42
severity: high | medium | low
category: <short-kebab-slug>
claim: One sentence stating the defect.
scenario: Concrete inputs or state, then the wrong output or crash that follows.
confidence: 85
```

When you have finished the whole lens, append this line and nothing after it:

`<!-- shard-complete -->`

If you find nothing, still append the sentinel - a complete file with no findings is a real result and
stops the orchestrator from retrying you.

---

## Retry variant

On the single permitted retry, keep the prompt identical but replace `<SCOPE_NOTE>` with:

> , narrowed for this retry to these files only: `<FILE_LIST>` (the largest by changed lines; the rest of
> the diff is out of scope for you).

and note in the merged `findings.md` that the lens ran at reduced scope.
