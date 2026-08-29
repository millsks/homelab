# homelab

Project Asgard — a homelab platform whose entire desired state lives in this repository.

Two claims are load-bearing, and everything in the tree exists to make them checkable:

- **Every operational activity is a Procedure with two halves** — a Runbook *and* its Automation,
  cross-referenced by name and enumerated in [`PROCEDURE-INDEX.md`](PROCEDURE-INDEX.md), which is
  the authoritative list of every Procedure the platform **requires** — one per story, except where
  the ownership table splits a story across two owners — each with its owning layer, owning story,
  both paths, and a status from a closed set. It enumerates what is required rather than what has
  been built, so it is nearly all `planned` right now; that is the honest reading, and it is the
  denominator FR-1 was missing. Start there to find out what the platform commits to. **Counts live
  in that file's Totals section and nowhere else**, this README included — a count restated is a
  count that goes stale. Neither half alone qualifies, with one carve-out: a class recorded in
  [`docs/OWNERSHIP.md`](docs/OWNERSHIP.md) as `Runbook` or `docs/ record` is **human-executed by
  decision** and has no Automation half. Racking a Node has no playbook and never will. Those
  Procedures are marked as such in the Index rather than counted as automation gaps, and they still
  carry an automated verification wherever a machine can observe the result. "Human-executed"
  is a decision recorded in the ownership table; it is never a synonym for "not yet automated".
- **Every configurable resource has exactly one declaring owner**, named in
  [`docs/OWNERSHIP.md`](docs/OWNERSHIP.md). Zero owners and two owners are both defects.

## The layer model

Six stratified dependency layers. **A layer may depend only on layers strictly below it.** That
upward-dependency prohibition is the design's single enforceable claim — every circular-dependency
failure the platform is built to avoid is an instance of it.

| Layer | Contains |
| --- | --- |
| `l0-physical` | Power, network fabric, rack, firmware, out-of-band management |
| `l1-hypervisor` | Proxmox cluster on four Nodes; Guest provisioning |
| `l2-foundation` | Directory, DNS, Kerberos, time, platform CA |
| `l3-platform` | k3s, storage classes, gateway, load balancer, storage appliance |
| `l4-services` | IdP, databases, cache, registry, CI, observability, secret store |
| `l5-workloads` | The operator's own applications |

Bring-up, upgrades, and rebuilds all proceed bottom-up, because the dependency direction is also
the safe order of operations.

## Repository shape

The tree is **tool-rooted and layer-subdivided**: one root per tool, each carrying the same six
layer directories.

```text
ansible/          in-guest and host OS configuration      l0-physical/ … l5-workloads/
tofu/             virtual hardware and Guest existence    l0-physical/ … l5-workloads/
k8s/              in-cluster manifests, reconciled        l0-physical/ … l5-workloads/
runbooks/         the human form of every Procedure       l0-physical/ … l5-workloads/
runbooks/TEMPLATE.md  the required starting point for every Runbook
docs/             platform records that are neither runbook nor automation
PROCEDURE-INDEX.md   authoritative enumeration of every Procedure
```

[`runbooks/TEMPLATE.md`](runbooks/TEMPLATE.md) is not a suggestion. Each of the four requirements
of the runbook standard is a required `####` heading inside every step block — **Command** (the
actual commands, never "run the playbook"), **Expected output** (per checkpoint, so a divergence is
locatable), **Automation task** (the bidirectional mapping), and **Failure modes** (what breaking
looks like and what to check first). They are headings rather than prose labels so a dropped one is
a hole in the outline: visible to a reader skimming, and detectable by story 1.3's audit without
parsing sentences. The failure-mode heading additionally requires the literal `No known failure
mode.` when there is none, because it is the section a writer under time pressure drops first.
Every Procedure still to be written is cut from this file; without it each would invent its own
shape.

**Why one root per tool rather than one root per layer.** `ansible-lint` and kustomize each take a
single root and walk down from it, so layer-rooting would mean six invocations apiece and six
places for the CI gate to skip something silently. The layer stays the organising principle
*inside* each root, which is where it aids navigation.

This argument does **not** extend to `tofu validate`, and the README used to claim it did.
`tofu validate` has no recursive mode: it evaluates exactly one root module directory, so it needs
one invocation per root whichever way the tree is cut, and tool-rooting produces six roots under
`tofu/` rather than one. `pixi run tofu-validate` therefore iterates the layer directories that
contain `*.tf`, validates each, fails if any fails, and prints how many it processed — a count of
zero is reported, never silent. The layout stands on the ansible-lint and kustomize argument; the
tofu task absorbs the cost.

**Why `runbooks/` is layer-first and not tool-first.** An operator mid-incident navigates by layer,
because that is how the failure presents itself. They do not know yet which tool owns the thing
that broke.

Every layer directory exists under every tool root, including combinations that will stay empty —
there are no Kubernetes manifests for rack cabling. A `.gitkeep` holds each empty directory, because
git does not track directories and the tree would otherwise not survive a clone.

An empty layer directory is therefore **not** evidence of anything on its own, in either direction.
[`docs/OWNERSHIP.md`](docs/OWNERSHIP.md) records an owner and a declaring mechanism per resource
class, not a per-(tool root × layer) expectation, so it cannot currently tell you whether
`k8s/l0-physical/` is expected-empty or an unowned defect. Answering that means reading the
ownership table for the classes at that layer and seeing whether any names that root. Making it
directly answerable — a declared expected-empty set the audit can check — is story 1.3's problem,
not a claim this README should make on its behalf.

A Procedure's Runbook and its Automation live in the same-named layer directory under their
respective roots and cross-reference each other by name.

## Development

The CI gate is the definition of done:

```sh
pixi install --locked
pixi run ci     # lint, check, tofu-validate, then the convergence harness
```

Individual steps: `pixi run lint`, `pixi run fmt`, `pixi run check`, `pixi run tofu-validate`.

### The convergence harness

`src/asgard_harness/` makes this repository's own rules executable. It reads the defect classes out
of [`PROCEDURE-INDEX.md`](PROCEDURE-INDEX.md) and [`docs/OWNERSHIP.md`](docs/OWNERSHIP.md) rather
than restating them, so changing a rule means changing the document that states it.

```sh
pixi run test        # unit tests
pixi run cov         # full suite with the coverage gate
pixi run audit       # every detector against this repository; names each defect it finds
pixi run selfcheck   # injects a known-bad fixture per defect class and proves the audit fails
pixi run drift       # AD-23's check-mode run over the push-based layers; records the result
```

`pixi run selfcheck` is the part worth understanding. A gate that cannot fail is worse than no gate,
so the harness injects a bad fixture for every defect class it claims to detect, asserts the audit
exits non-zero *and names that class*, and deletes the fixture. Fixtures land in a throwaway copy of
the repository; the working tree is never touched. A fixture that fails to provoke its defect is
itself reported as a failure.

The Procedure it implements is [`PROC-CONVERGENCE-HARNESS`](runbooks/l0-physical/convergence-harness.md).

## License

Not yet declared.
