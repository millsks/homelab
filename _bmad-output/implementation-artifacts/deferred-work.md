# Deferred Work

Findings that are real but not the responsibility of the story that surfaced them.
Append-only. Do not edit existing entries.

**One permitted amendment: a `resolution:` line.** A later story that closes an entry appends that
line to it, naming itself and what it did. Nothing already written is reworded or removed — the
finding and its evidence stay exactly as the story that surfaced them left them. Without this, a
ledger only grows and stops being readable as a work list, which is the failure this file exists to
avoid; with it, closure is visible beside the finding rather than inferred from silence. Story 1.1
already did this informally by editing a summary in place; making it a named field is the same
thing done in a way that preserves the original text.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-repository-skeleton-with-layered-ownership.md`
  summary: `pixi run bootstrap` is broken — the task runs `pre-commit install --install-hooks` but no `.pre-commit-config.yaml` exists.
  evidence: Pre-existing from the pixi workspace commit, not caused by story 1.1. Anyone following the README onboarding hits it. Natural home is story 1.3, which owns the convergence harness — pre-commit is where a commit-time check for AD-15's plaintext-secret rule would live.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-repository-skeleton-with-layered-ownership.md`
  summary: No `.github/workflows/` — the CI gate runs only on a developer machine, so "the gate is the definition of done" holds locally and nowhere else.
  evidence: `.github/` contains only vendored agent definitions. The project scaffold standard expects a CI workflow and a status badge. Pre-existing.
  resolution: CLOSED by story 1.3. `.github/workflows/ci.yml` runs `pixi run ci` on every push and pull request to `main`, across a matrix of every interpreter in the supported range, plus two scheduled jobs (`drift`, `converge`) whose records are uploaded as artifacts. `fetch-depth: 0` is deliberate — the stale-provenance detector asks git which commit last touched `epics.md`, and a shallow clone cannot answer, so the check would degrade to SKIP, which does not fail the gate. Actions are pinned to commit SHAs rather than floating `@v4` tags, and `pixi-version` is pinned exactly, because AD-20 prohibits `latest` and a moving tag is `latest` wearing a version number. The status badge is still absent; that is cosmetic and stays open below.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-repository-skeleton-with-layered-ownership.md`
  summary: Dev dependencies are pinned `*` in `pixi.toml` while the same repository declares `latest` prohibited under AD-20.
  evidence: `ruff`, `mypy`, `pre-commit`, `yamllint`, `ansible-lint` are all unpinned. Sharpened by story 1.1: the `.yamllint` rules added there are shaped to satisfy whatever ansible-lint currently wants, so an unpinned ansible-lint can silently break the gate. Pre-existing from the pixi workspace commit.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-repository-skeleton-with-layered-ownership.md`
  summary: No LICENSE file in a public repository, so the default is all-rights-reserved.
  evidence: Repository visibility is public. README's License section reads "Not yet declared". A deliberate choice is fine; an accidental one is not.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-repository-skeleton-with-layered-ownership.md`
  summary: `tofu-validate` scans exactly one level (`tofu/*/`), so a root module nested deeper is skipped silently.
  evidence: Same class of defect as the one story 1.1 fixed, one level down — a validator that reports success over configuration it never read. Harmless while the tree holds no `.tf` files; must be revisited the moment real OpenTofu configuration lands, which is story 2.6.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-repository-skeleton-with-layered-ownership.md`
  summary: RESOLVED during story 1.1 — `_bmad-output/` is now excluded from yamllint rather than having its document-start marker maintained by hand.
  evidence: The predicted failure occurred within minutes of being predicted: the sprint-status sync rewrote the file without `explicit_start` and `yamllint --strict` failed on it. Kept here because the lesson generalises — generated artifacts should never be held to a house style that the generating tool does not know about, or two tools end up fighting over one file.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-repository-skeleton-with-layered-ownership.md`
  summary: Nothing enforces the upward-dependency prohibition that the design calls its single enforceable claim.
  evidence: No check inspects a layer directory for references to a higher layer. The README now states the claim is enforceable in principle rather than enforced. Natural home is story 1.3's harness.
  resolution: CLOSED by story 1.3. `asgard_harness.checks_crossdoc.check_layer_dependencies` walks every `<tool root>/l<N>-*/` directory and fails on any file referencing an `l<M>-` layer where `M > N`, naming the file and the layers. It counts only files it actually decoded, and names any it could not, because in this harness the count is the claim. The detector is textual: it matches layer tokens, not resolved dependencies. That cuts both ways, and both were observed during this story — it caught a genuine upward reference in a fixture, and it also fired on this story's own Runbook when a sample output block quoted the push-based layer names in prose. The Runbook was reworded rather than the detector relaxed, but a Runbook that legitimately needs to name a higher layer in prose will hit this, and the answer will have to be a scoping rule rather than an exemption list.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-repository-skeleton-with-layered-ownership.md`
  summary: No Markdown or intra-repository link checking anywhere in the gate.
  evidence: Story 1.1 added roughly 500 lines of Markdown whose entire value is cross-references, and the gate lints Python, YAML, Ansible and OpenTofu — none of which touch it. A link checker would have caught the three dangling references the review found by hand.
  resolution: PARTIALLY CLOSED by story 1.3. The audit now resolves the cross-references that carry meaning: every Index Runbook and Automation path against the filesystem, every ownership `Procedure` cell against the Index's key set, every Runbook's front matter against its Index entry and back, and every Runbook's headings against the template. What is still unchecked is ordinary Markdown link syntax — a `[text](path)` to a file that does not exist, anywhere outside those columns. Left open deliberately rather than folded in: a general link checker is a different tool with a different failure mode (it wants to be right about anchors and external URLs), and bolting it onto the harness would blur what the harness is for.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-repository-skeleton-with-layered-ownership.md`
  summary: No per-(tool root x layer) mapping records which layer directories are expected-empty by design.
  evidence: 24 directories were created; roughly half will never hold anything — Kubernetes manifests for physical racking do not exist. Nothing distinguishes expected-empty from an unowned defect, so the audit cannot tell them apart. README was softened to stop claiming OWNERSHIP.md answers this.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-convergence-test-harness.md`
  summary: The spec's Intent says `PROCEDURE-INDEX.md` defines nine defect classes; it defines sixteen.
  evidence: Counted from § "Defects this Index reports": six entry-level, two namespace-level, four Index-to-story, four cross-document. `docs/OWNERSHIP.md` § Audit defines four more, one of which is the Index's incomplete-Procedure rule named for completeness, so five ownership-side rules in total including verification-present. The harness implements every one of them except the unowned defect, which is separately recorded below. The figure in the spec is stale rather than wrong-headed — it predates the Index's final defect list — but a spec that undercounts what it requires by seven is a spec someone will later read as complete when it is not. Flagged rather than silently corrected: the Intent block is frozen and human-owned.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-convergence-test-harness.md`
  summary: The unowned defect in `docs/OWNERSHIP.md` § Audit cannot be implemented as defined, and is reported by the harness rather than approximated.
  evidence: "A configurable resource class present in the platform and absent from this table" needs an enumeration of the platform's resource classes that is independent of the table — and the table is the only such enumeration. Nothing the harness can read distinguishes an unowned class from a class nobody has thought of. `pixi run audit` therefore reports it as `[SKIP]` with that reason rather than as a pass; a check that cannot see the defect it is named for must not report success. Closing it needs a second enumeration — plausibly a discovered inventory from running systems, which is a much later epic — or a human decision to rescope the rule. Surfaced under the spec's "Ask First" clause; no definition was narrowed.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-convergence-test-harness.md`
  summary: The unwritten-human-form detector was implemented as an agreement check against the Index's own record, not as a bare "the file is absent" failure. This is an interpretation and needs human confirmation.
  evidence: The Index defines the defect as "an entry whose Runbook path does not exist" and then says most are unwritten today and that is expected while their owning stories are unstarted. Taken literally the audit must fail on seven of the nine `manual-by-decision` entries today, which contradicts the spec's own acceptance criterion that a clean repository exits 0. The Index resolves this itself: it says Runbook presence for these entries "is tracked in Deliberately manual work", which has a `Human form written?` column, and Totals carries a `Human forms written` figure. The detector therefore fails when that column disagrees with disk in either direction, and Totals recomputes the count from the filesystem — so the number cannot quietly stop shrinking, which is the reason the Index gives for the rule existing. If the human intent was the literal reading, the fix is a change to the Index's wording, not to the detector.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-convergence-test-harness.md`
  summary: `pixi run bootstrap` is still broken — no `.pre-commit-config.yaml` exists. The story that was expected to close it did not.
  evidence: Deliberate. The entry above nominates story 1.3 because "pre-commit is where a commit-time check for AD-15's plaintext-secret rule would live" — but that check is story 1.4's, and shipping a hook configuration whose only real hook belongs to the next story means shipping one that has never enforced anything. A pre-commit config also pulls its own tool environments over the network at install time, independent of `pixi.lock`, which is a second unpinned toolchain in a repository that prohibits `latest`. Both are 1.4's problems to weigh when it adds the plaintext-secret hook it actually needs.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-convergence-test-harness.md`
  summary: Compiled Python bytecode is committed under `.agents/` and `.claude/`.
  evidence: Ten `__pycache__/*.pyc` files from vendored BMAD skill scripts, built by CPython 3.11 — not even this workspace's interpreter. Story 1.3 added `__pycache__/` and `*.py[cod]` to `.gitignore`, which stops any new ones, but `.gitignore` does not untrack what is already tracked. Untracking them is `git rm --cached` over paths the story's spec marks read-only, so it was not done here. It is a one-line change whenever someone is deliberately touching the vendored trees.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-convergence-test-harness.md`
  summary: `src/asgard_harness/__main__.py` is the one file the test suite does not execute.
  evidence: Coverage is 98% overall with that module at 0%: its body only runs under `python -m asgard_harness`, which the tests reach through `cli.main` instead. The module is five lines with no branch of its own, so the risk is a typo in the module-level wiring rather than logic — and `pixi run audit`, `selfcheck`, and `drift` all invoke it for real in the gate, so a broken `__main__` fails CI immediately. Recorded because "98%" should not read as "everything ran".

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-convergence-test-harness.md`
  summary: RESOLVED during story 1.3 review — the convergence checks read a failed tool run as a clean one, the fourth instance of this project's recurring defect.
  evidence: `check_idempotence` and `check_drift` branched only on `run.changed`. Every parser set an exit code and no decision consulted it, and the ansible runner discarded it outright, so `tofu plan` in an uninitialised module, `kubectl diff` with no reachable cluster, and a missing binary all produced `changed=()` and reported PASS. Invisible only because no Automation exists yet; it would have gone live with the first OpenTofu module. Fixed by encoding each tool's own exit-code convention in its own parser (tofu 2=changes/1=error, kubectl 1=differences/>1=error, ansible any non-zero=error), adding `RunResult.error`, and refusing to judge a run that carries it. Seven runner fixtures and 24 tests now fail if the behaviour is reverted, verified by mutation.
  pattern: This is the same error as story 1.1's `&& cmd || echo` gate guard, the review's own `pixi run ci && echo PASS || echo FAIL`, and the self-check's untested failure branch — treating "no positive evidence of a problem" as "evidence of no problem". A tool that could not run, a branch never taken, and a genuinely clean result all produce the same shape, and nothing distinguished them. The general defence adopted here: the test to write is the one that breaks the thing and asserts the break is reported, never the one that runs it clean and asserts success.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-convergence-test-harness.md`
  summary: A SKIPPED check does not fail the gate, so any detector degrading to SKIP would leave the gate green with one rule silently unenforced.
  evidence: `AuditReport.exit_code` counts only FAILED, by design — an honest skip is not a defect. But that makes SKIP a silent-degradation channel: a shallow clone silences the provenance check, a missing template silences the Runbook-shape check, and the gate stays green. Mitigated rather than closed: `audit.EXPECTED_AUDIT_SKIPS` names the one legitimate skip, and an integration test asserts the skipped set equals exactly that, so a new skip fails CI. Not closed because the mitigation is a pinned list a human maintains; a structural fix would need skips to carry an expiry or an owner.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-convergence-test-harness.md`
  summary: The merge gate would have reached live infrastructure the moment the first role landed.
  evidence: The convergence suite sat inside `run_audit`, which is in `pixi run ci`. Every pull request would have shelled out to `ansible-playbook`, `tofu plan`, or `kubectl diff` against managed hosts — contradicting this Procedure's own Runbook, whose preconditions said "no credentials of any kind" and whose rollback said the harness "does not write to any managed system". RESOLVED: `run_audit` is now a pure reader and the convergence suite moved to `run_convergence`, scheduled alongside `drift`. `cli.GATE_COMMANDS` pins what `all` runs, and an integration test monkeypatches `run_command` to raise if the audit shells out at all. The Runbook's precondition table was corrected rather than left to be believed.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-convergence-test-harness.md`
  summary: GitHub Actions are pinned to commit SHAs, which nothing renews.
  evidence: AD-20 prohibits `latest`, and `actions/checkout@v7` is a moving tag, so the actions are pinned to SHAs with the version in a trailing comment. The cost is that security fixes to those actions now require a deliberate bump, and nothing in this repository reminds anyone. Dependabot or Renovate is the usual answer and neither is configured. Same class as the unpinned `*` dev dependencies recorded above, and probably wants solving once for both.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-convergence-test-harness.md`
  summary: `src/asgard_harness/__main__.py` remains the one file no test executes.
  evidence: Coverage is 98.89% with that module at 0%: its body only runs under `python -m asgard_harness`, which the tests reach through `cli.main` instead. It is five lines with no branch of its own, and `pixi run audit` and `selfcheck` invoke it for real in the gate, so a broken `__main__` fails CI immediately. Recorded because "98.89%" should not read as "everything ran" — which is the same conflation this story's review was about.
