# Deferred Work

Findings that are real but not the responsibility of the story that surfaced them.
Append-only. Do not edit existing entries.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-repository-skeleton-with-layered-ownership.md`
  summary: `pixi run bootstrap` is broken — the task runs `pre-commit install --install-hooks` but no `.pre-commit-config.yaml` exists.
  evidence: Pre-existing from the pixi workspace commit, not caused by story 1.1. Anyone following the README onboarding hits it. Natural home is story 1.3, which owns the convergence harness — pre-commit is where a commit-time check for AD-15's plaintext-secret rule would live.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-repository-skeleton-with-layered-ownership.md`
  summary: No `.github/workflows/` — the CI gate runs only on a developer machine, so "the gate is the definition of done" holds locally and nowhere else.
  evidence: `.github/` contains only vendored agent definitions. The project scaffold standard expects a CI workflow and a status badge. Pre-existing.

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

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-repository-skeleton-with-layered-ownership.md`
  summary: No Markdown or intra-repository link checking anywhere in the gate.
  evidence: Story 1.1 added roughly 500 lines of Markdown whose entire value is cross-references, and the gate lints Python, YAML, Ansible and OpenTofu — none of which touch it. A link checker would have caught the three dangling references the review found by hand.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-repository-skeleton-with-layered-ownership.md`
  summary: No per-(tool root x layer) mapping records which layer directories are expected-empty by design.
  evidence: 24 directories were created; roughly half will never hold anything — Kubernetes manifests for physical racking do not exist. Nothing distinguishes expected-empty from an unowned defect, so the audit cannot tell them apart. README was softened to stop claiming OWNERSHIP.md answers this.
