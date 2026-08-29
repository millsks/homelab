---
title: 'Story 1.1 — Repository skeleton with layered ownership'
type: 'feature'
created: '2026-08-28'
status: 'done'
review_loop_iteration: 0
baseline_commit: 'f5471f8c8cd3454659b2db7de1685fd3a340b167'
context:
  - _bmad-output/implementation-artifacts/epic-1-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The repository has no home for automation, runbooks, or platform declarations, and no record of which tool declares which resource. Without that record the provisioning and configuration tools will both legitimately claim the same attributes — a guest's address and its emergency account can be set by either — producing two authoritative declarations that the convergence test structurally cannot detect.

**Approach:** Create the directory tree that every later story writes into, and an ownership table naming exactly one declaring owner for every configurable resource class, with the provisioning/configuration boundary drawn by **attribute** rather than by moment in time.

## Boundaries & Constraints

**Always:**
- Coverage is total. Every configurable resource class gets an owner, including ones no tool obviously claims: the hypervisor host OS, the storage appliance, the managed switch, firmware settings, and the provisioning tool's own state.
- Exactly one owner per class. Zero owners and two owners are both defects.
- The provisioning tool declares virtual hardware, guest existence, and **one** bootstrap SSH key. It must not set in-guest addressing, accounts, or passwords, even though the mechanism allows it.
- The configuration tool declares everything inside the operating system, including addressing and accounts.
- Layer order L0–L5 is the organizing principle; dependencies point only downward.
- Classes with no automation owner are recorded as human-executed rather than left blank.

**Ask First:**
- Any deviation from the layer names or the six-layer model.
- Adding a tool root beyond `ansible/`, `tofu/`, and `k8s/`.

**Never:**
- Do not create the Procedure Index — that is story 1.2. A placeholder reference is acceptable; content is not.
- Do not write any role, module, manifest, or runbook content. This story creates structure and the ownership record only.
- Do not add secret material, encrypted or otherwise — that is story 1.4.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Ownership lookup | A resource class named in the table | Exactly one owner, one declaring mechanism | N/A |
| Two-owner defect | A class appearing in two owner rows | Audit fails and names the class | Fail loudly; do not pick a winner |
| Unowned defect | A class present in the platform but absent from the table | Audit fails and names the class | Fail loudly |
| Manual-only class | Physical placement, firmware, appliance setup | Owner recorded as human runbook, verification automated where possible | N/A |
| Empty tree | Fresh clone | Every layer directory exists and is tracked | `.gitkeep` in otherwise-empty directories |

</frozen-after-approval>

## Code Map

- `pixi.toml` -- task guards already assume `ansible/` and `tofu/` at repository root (`lint-ansible`, `tofu-validate`, `fmt`); the tree must match or the CI gate silently skips
- `_bmad-output/planning-artifacts/architecture/.../ARCHITECTURE-SPINE.md` -- AD-22 ownership rule; "Structural Seed" section carries a repository shape that is explicitly seed, revisable once code exists
- `_bmad-output/implementation-artifacts/epic-1-context.md` -- distilled epic constraints; load instead of raw planning docs
- `.yamllint` -- ignores vendored trees; new directories are linted, so any YAML added must pass
- `.gitignore` -- needs `.ruff_cache/` added; it appeared during tooling setup and is untracked noise
- `README.md` -- currently one line; the tree needs an orientation section

**Read-only (do not modify):** `_bmad/`, `.claude/`, `.agents/`, `.bmad-loop/`, `.github/` — vendored.

## Tasks & Acceptance

**Execution:**
- [x] `ansible/`, `tofu/`, `k8s/` -- create tool roots, each subdivided by layer -- ansible-lint, `tofu validate` and kustomize each expect one root per tool; six layer-scattered roots would mean six lint invocations and would break the existing pixi task guards
- [x] `runbooks/l0-physical/` … `runbooks/l5-workloads/` -- create the human-form tree by layer -- runbooks are organized by layer because that is how an operator navigates during an incident
- [x] `docs/OWNERSHIP.md` -- the ownership table: resource class, owner, declaring mechanism, notes -- the story's substantive deliverable
- [x] `docs/` -- create as the home for platform records that are neither runbook nor automation (address plan, escrow index) -- keeps declarations out of tool roots
- [x] `PROCEDURE-INDEX.md` -- stub only, pointing at story 1.2 -- referenced by the ownership table; content belongs to 1.2
- [x] `.gitignore` -- add `.ruff_cache/` -- untracked tooling noise
- [x] `README.md` -- add tree orientation and the layer model -- first thing a reader meets
- [x] `.gitkeep` in every otherwise-empty directory -- git does not track empty directories, so the tree would not survive a clone

**Acceptance Criteria:**
- Given a fresh clone, when the tree is inspected, then every layer directory exists under each tool root and under `runbooks/`.
- Given the ownership table, when any configurable resource class in the platform is looked up, then it appears exactly once with one declaring mechanism.
- Given the provisioning row, when its scope is read, then it is limited to virtual hardware, guest existence, and one bootstrap SSH key, and explicitly excludes in-guest addressing, accounts, and passwords.
- Given a class with no automation, when it is looked up, then it is recorded as human-executed with its verification method named, not left blank.
- Given `pixi run ci`, when it runs against the new tree, then it passes and no longer reports "no ansible/ yet" or "no tofu/ yet".

## Design Notes

**Deviation from the spine's structural seed, with reason.** The seed shows layer directories holding automation (`l1-hypervisor/ # OpenTofu for Proxmox`) *and* a top-level `ansible/`. Those are two organizing principles for the same content, and a developer would have to invent the resolution. This spec resolves it as **tool-rooted, layer-subdivided**: `ansible/`, `tofu/`, `k8s/` at the root, each carrying `l0/`…`l5/` inside.

Three reasons: linters and validators expect one root per tool; the existing pixi task guards already assume root-level `ansible/` and `tofu/`; and the layer stays the organizing principle everywhere it aids navigation. The spine labels that section "Structural Seed" and states the code owns it once it exists, so refining it here is sanctioned rather than a violation. `runbooks/` stays layer-first because an operator mid-incident navigates by layer, not by tool.

## Verification

**Commands:**
- `pixi run ci` -- expected: passes; `lint-ansible` and `tofu-validate` now find their roots rather than skipping
- `git clone` into a temp directory, then `find . -type d -empty` -- expected: no empty directories, confirming `.gitkeep` coverage survives a clone

**Manual checks:**
- Read `docs/OWNERSHIP.md` and confirm every class named in the Always constraints appears: hypervisor host OS, storage appliance, managed switch, firmware, provisioning state.
- Confirm no class appears in two rows.

## Suggested Review Order

**The ownership contract — the story's substance**

- The boundary that prevents two tools declaring one attribute; read this before any table row.
  [`OWNERSHIP.md:61`](../../docs/OWNERSHIP.md#L61)

- Closed enumeration of legal Owner values — without it story 1.3's audit cannot parse the table.
  [`OWNERSHIP.md:21`](../../docs/OWNERSHIP.md#L21)

- The two-owner defect the review caught: one owning row, with the other row naming the exclusion.
  [`OWNERSHIP.md:138`](../../docs/OWNERSHIP.md#L138)

- The control node — holds the bootstrap key and decryption key, and AD-24 forbids depending on it.
  [`OWNERSHIP.md:176`](../../docs/OWNERSHIP.md#L176)

- Both defect types the audit must detect, and why it refuses to auto-resolve either.
  [`OWNERSHIP.md:185`](../../docs/OWNERSHIP.md#L185)

**The gate that was silently passing**

- Guard rewritten so only the directory test short-circuits; failure no longer takes the echo branch.
  [`pixi.toml:16`](../../pixi.toml#L16)

- Validates each layer directory as its own root module and reports the count processed.
  [`pixi.toml:21`](../../pixi.toml#L21)

- State files excluded — the table itself calls provisioning state credential-bearing.
  [`.gitignore:22`](../../.gitignore#L22)

**Orientation**

- Layer model, repository shape, and the reasoning for tool-rooted over layer-rooted.
  [`README.md:1`](../../README.md#L1)

- Stub only; entry format belongs to story 1.2.
  [`PROCEDURE-INDEX.md:1`](../../PROCEDURE-INDEX.md#L1)
