---
title: "Structural Review — PRD: Project Asgard"
type: structure-review
target: prd.md
reviewed: 2026-08-28
---

# Structural and Internal-Consistency Review

Mechanical pass over `prd.md` (972 lines), cross-checked against
`briefs/brief-homelab-2026-08-28/brief.md` (132 lines) and
`briefs/brief-homelab-2026-08-28/addendum.md` (292 lines).

Scope: structural integrity and internal coherence only — vocabulary discipline, ID
continuity, cross-reference validity, coverage roundtrips, and cross-document
contradiction. Prose quality is out of scope.

**Verdict up front:** the numbering spine is clean and the requirement set is
genuinely coherent, but three mechanical contracts the document declares about
itself are broken — the `[ASSUMPTION]` tagging promised in §0 does not exist
anywhere in the body, one Success Metric cites a requirement that has nothing to
do with it, and a cut-scope survivor ("LAN-and-VPN platform") sits in §7.2
contradicting §6, §7.2's own next bullet, and NFR-14.

---

## 1. Glossary Discipline (§3)

§3 line 71 states: *"Downstream workflows and readers use these terms exactly.
Introducing a synonym anywhere in this document is a discipline violation."*
§0 line 16 scopes the obligation: *"vocabulary is fixed in the Glossary (§3) and
used verbatim everywhere after."* Findings below are therefore weighted to §4–§12;
§1–§2 usages are noted at **low** because they precede the Glossary, but they are
still the first thing a reader meets.

### 1a. Cluster / Yggdrasil conflation (the deliberately-distinct pair)

- **[high]** Yggdrasil called "a working Kubernetes cluster" (§9, line 919) — the S6 epic row reads `| S6 | Yggdrasil, minimal | A working Kubernetes cluster with storage from Nidavellir |`. "Kubernetes cluster" is precisely the phrase the Glossary reserves Yggdrasil for, and "cluster" unqualified is the Proxmox **Cluster**. The epic row simultaneously uses the right term in one column and the banned synonym in the next. *Fix:* "A working Yggdrasil with storage from Nidavellir."
- **[high]** "Everything in the cluster" used to mean Yggdrasil (§6, line 839) — `- **Not a Kubernetes-only platform.** Guests running outside Yggdrasil are legitimate … "Everything in the cluster" is not an objective.` Read literally against §3 line 78, this says guests running outside the Proxmox Cluster, which is incoherent (every Guest runs on the Cluster by definition). *Fix:* `"Everything in Yggdrasil" is not an objective.`
- **[medium]** "cluster rebuild" used for Yggdrasil rebuild (§4.8, lines 515 and 542) — FR-37 consequence "The lost Control Plane Guest rejoins without cluster rebuild" and FR-40 consequence "Persistent Volume data survives cluster rebuild". Both mean Yggdrasil; both read as Cluster. *Fix:* "without rebuilding Yggdrasil" / "survives Yggdrasil rebuild".
- **[medium]** "cluster authorization rules" (FR-39 consequence, line 531) — means Yggdrasil RBAC. *Fix:* "Yggdrasil authorization rules."
- **[medium]** Seam list conflates three planes (§9, line 922) — "hypervisor to storage, storage to Kubernetes, Directory to IdP, IdP to Kubernetes, IdP to application, Repository to running Workload" uses *hypervisor* for Cluster, *storage* for Nidavellir, *Kubernetes* (twice) for Yggdrasil, and *application* for Workload. Five synonyms in one sentence. *Fix:* "Cluster to Nidavellir, Nidavellir to Yggdrasil, Directory to IdP, IdP to Yggdrasil, IdP to Workload, Repository to running Workload."
- **[medium]** "the Kubernetes API" (§4.7 description, line 433) — the Glossary's own **Relying Party** entry (line 91) says "Yggdrasil's API". The PRD contradicts its own glossary wording eight lines of prose later. *Fix:* "Yggdrasil's API".
- **[medium]** Section heading "### 4.8 Kubernetes Platform" (line 502) — the feature is Yggdrasil; every other §4 heading uses either a Glossary term or a neutral capability name. *Fix:* "### 4.8 Yggdrasil".
- **[low]** "Multi-cluster or staging Yggdrasil" (§7.2, line 873) — "multi-cluster" is ambiguous between Cluster and Yggdrasil. *Fix:* "A second Yggdrasil (staging)".
- **[low]** "the Kubernetes storage model" (§11 Q2, line 958) — mechanism-space phrasing; acceptable in an open question but inconsistent. *Fix:* "Yggdrasil's storage model".
- **[low]** "Kubernetes" in §1 (line 20) — pre-Glossary narrative; noted for completeness only.

### 1b. Nidavellir vs "the NAS"

- **[high]** "the NAS" in a testable consequence (FR-19, line 325) — "Drive failure produces an alert without the operator inspecting the NAS." This is inside a **Consequences (testable)** block, i.e. the part downstream story generation reads literally. *Fix:* "…without the operator inspecting Nidavellir."
- **[medium]** "NAS failure" in the Risks table (§10, line 946) — the same row uses "Nidavellir" in the Risk column and "NAS" in the Impact column. *Fix:* "Platform-wide disruption on Nidavellir failure."
- **[medium]** "storage" as a stand-in for Nidavellir (§9 line 922; NFR-7 line 807) — NFR-7 reads "leaves sufficient capacity to run all identity, storage, and Yggdrasil control functions", but Nidavellir is not a Node and consumes no Cluster capacity, so "storage" here is either a synonym for Nidavellir (wrong — Node loss cannot affect it) or a synonym for the Share-serving path (undefined). *Fix:* drop "storage" from NFR-7 or name what capacity is meant.
- **[low]** "a NAS" in §1 (line 20) and "the NAS powers off last" in UJ-4 (line 61) — pre-Glossary; UJ-4 in particular is worth aligning since FR-56/FR-57 cite it.

### 1c. Cluster vs "hypervisor" / "hypervisor UI" — an undefined term used six times

- **[high]** "hypervisor UI" is a load-bearing noun with no Glossary entry — used at lines 433, 457 (FR-32 requirement text), 855 (§7.1), 887 (SM-3), 937 (§9 D10), 968 (§12). It names a Relying Party, appears in a Success Metric, and is the subject of an indexed assumption, yet it is not defined. *Fix:* add a Glossary entry, e.g. **Cluster Management Interface** — the Cluster's administrative web interface; a Relying Party.
- **[high]** The same interface has two names (FR-10 line 210 vs FR-32 line 457) — FR-10 says "the Cluster management interface"; FR-32 says "the hypervisor UI". These are the same surface, and FR-10/FR-32 are directly coupled (FR-10 is break-glass for exactly what FR-32 puts behind the IdP). A downstream reader cannot tell whether they are one component or two. *Fix:* pick one term and use it in both.
- **[medium]** "hypervisor" as a bare noun (§4.2 description line 171; §9 line 922) — "Four Nodes running a hypervisor" duplicates the Glossary's Node definition (line 76) rather than using **Cluster**/**Node**. *Fix:* "Four Nodes joined into one Cluster, providing the substrate…".
- **[medium]** "Proxmox Cluster" (§7.1, line 850) — the only product name in §7.1, and §0 line 16 explicitly says "Technology choices and mechanism decisions live in `addendum.md`, not here". *Fix:* "Cluster across four Nodes, declaratively provisioned."

### 1d. Account / Group / Break-glass Account

- **[medium]** "Local administrative accounts" (FR-32 consequence, line 462) — "Local administrative accounts remain available for break-glass but are not used routinely." The Glossary term is **Break-glass Account** (line 93). Using "local administrative account" leaves it ambiguous whether FR-32 means the same accounts FR-24 mandates. *Fix:* "Break-glass Accounts remain available but are not used routinely."
- **[medium]** "break-glass" lowercase as an adjective, three places (line 462; FR-39 line 533; FR-55 title line 692 and consequences line 697) — the Glossary capitalizes **Break-glass Account**; "break-glass credentials" is used lowercase-adjective in FR-7 (line 188), FR-39, FR-55, SM-1 (line 885), NFR-13 (line 816), NFR-21 (line 830), §10 (line 952). This is probably intentional (a credential is not an Account) but it is nowhere stated. *Fix:* add **Break-glass Credential** to the Glossary, or state that the lowercase adjectival form is sanctioned.
- **[medium]** "user"/"users" for Account (§4.11 line 629 "rather than from a user"; SM-4 line 888 "authenticates users against Forseti"; §6 line 837 "no anonymous users"; §7.2 line 868 "one user") — SM-4 is a **primary success metric** and uses the synonym in the measurable clause. *Fix:* "authenticates Accounts against the IdP".
- **[low]** "no per-host local account" (FR-20 line 338) and "a named local account, not the root account" (FR-24 line 378) — lowercase "account" here means an OS account, not an **Account**. Legitimate but collides with the defined term. *Fix:* say "local OS account".
- **[low]** §2.3 UJ-5 (line 64) "He disables a single directory account" — lowercase, pre-Glossary.

### 1e. Node / Guest / Workload

- **[high]** The Glossary itself uses "node" for a Guest — line 80 "**Control Plane Guest** — a Yggdrasil server node" and line 81 "**Worker Guest** — a Yggdrasil agent node running Workloads." **Node** is defined one line earlier (line 76) as *a physical machine*. The Glossary violates its own discipline in the two entries where Node/Guest confusion is most costly. *Fix:* "a Yggdrasil server member" / "a Yggdrasil agent member", or "server-role Guest" / "agent-role Guest".
- **[medium]** Lowercase "node" in a testable-adjacent Notes block (FR-65, line 267) — "wireless variance is indistinguishable from node loss … while every node still appears up". *Fix:* capitalize to **Node**.
- **[medium]** Lowercase "nodes" in §6 (line 844) and §10 (line 951) — "additional nodes are possible futures"; "1 GbE nodes bottleneck all storage traffic", "per-Node adapters" in the same cell. Inconsistent within one table row. *Fix:* Node throughout.
- **[medium]** "application" used where **Workload** is defined (FR-44 title/text lines 577–584; §7.1 line 864 "A reference application"; §9 S7 line 920; SM-4 line 888; SM-10 line 897 uses Workload correctly) — SM-10 and FR-44 describe the same thing with different nouns, which makes SM-10's "Validates FR-44" harder to verify mechanically. *Fix:* either define **Reference Application** in the Glossary or normalize to Workload.
- **[low]** §1 (line 22) "Every node, guest, and service" — all lowercase, pre-Glossary.

### 1f. Draupnir / IdP / Directory instance names

- **[medium]** "Forseti" used as a bare proper noun where **IdP** is the term (§7.1 line 855; SM-4 line 888; §9 S5 line 918 and S7 line 920) — the Glossary (line 88) introduces `forseti` only as a parenthetical instance name for the **Identity Provider**. §7.1 and §8 then use "Forseti" as the primary noun, and §9 mixes both ("IdP federated to the Directory" and "authenticating via Forseti" are in adjacent rows). Casing also differs from the Glossary's backticked lowercase. *Fix:* use **IdP** in requirement/metric text; reserve `forseti` for the naming registry.
- **[medium]** "Draupnir" is defined (line 94) but §9 S5 (line 918) says "Internal CA" — "CA" appears nowhere in the Glossary. *Fix:* "Draupnir issuing internal TLS".
- **[medium]** "an internal certificate authority" (§6, line 837) — lowercase generic where **Draupnir** is the sole issuer by definition. *Fix:* "Draupnir".
- **[low]** `mimir` (§9 S4, line 917) is used where **Directory** is the term; `andvari` (D7), `huginn`/`muninn`/`gjallarhorn` (D6) likewise (see 1g).

### 1g. Domain nouns used in §4–§12 that are NOT in the Glossary and should be

Each of these carries requirement weight — it appears in an FR, an NFR, a Success
Metric, an epic, or the Assumptions Index — and none is defined in §3.

- **[high]** **Observability system / stack / interface / dashboards** — four different phrasings for one component, none defined: "the observability system" (FR-19 line 323, FR-36 line 498, NFR-20 line 829), "the observability stack" (line 433, §12 line 968), "the observability interface" (FR-32 line 457), "observability dashboards" (FR-52 line 662), "observability" bare (§7.1 line 855, SM-3 line 887, §9 D10 line 937). FR-52's "Access requires IdP authentication per FR-32" only holds if "observability dashboards" and "the observability interface" are the same thing — which the document never says. *Fix:* define **Observability System** in §3 and use it verbatim; keep `huginn`/`muninn` as instance names only.
- **[high]** **UPS** — used in FR-56 through FR-60 (§4.13), NFR-none, §7.1 line 861, §7.2 line 877, §9 D8 line 935, §11 Q5 line 961, and §6 line 844. The Glossary defines **NUT Server** and **Shutdown Sequence** but not the device they exist for. *Fix:* add **UPS**.
- **[high]** **Snapshot** — FR-9 (lines 200–206), NFR-23 (line 832), UJ-6 (line 67), §4.2 description (line 171). Central to the stated purpose ("fearlessness is the actual deliverable", line 24) and to an NFR, yet undefined and — see check 7 — delivered by no epic. *Fix:* add **Snapshot**.
- **[medium]** **Backup** / **Restore** — the whole of §4.14, FR-47, FR-61–64, SM-5, NFR-18, §9 D9. Undefined despite "Drill" and "Converged" being defined. *Fix:* add **Backup** and **Restore** (a Restore is arguably only real once verified — that distinction is the point of FR-63 and belongs in §3).
- **[medium]** **Secret** — the whole of §4.12, NFR-10, §7.1 line 860, §9 S1/D7. Undefined; "secret material", "credential", "key", "token" are used interchangeably (FR-53 line 679 uses all three; the Glossary's **Token** means something entirely different — an OIDC token). Real collision risk: NFR-10 "No credential, key, or token exists in plaintext in the Repository" reads, under the Glossary, as a statement about OIDC Tokens. *Fix:* define **Secret**, and either rename **Token** or explicitly scope NFR-10/FR-53 away from it.
- **[medium]** **Registry** (FR-43 lines 570–574; §7.1 line 857; §9 D4 line 931) — "internal registry" is required by an FR and delivered by an epic but undefined; also collides with "the Norse registry" (FR-11 line 239) and "the naming registry" (§7.2 line 873) in the same document. *Fix:* define **Image Registry**; rename the naming one to "naming registry" consistently.
- **[medium]** **Alert** (FR-19, FR-29, FR-51, FR-59, FR-61, NFR-19, SM-9, §11 Q6) — heavily load-bearing, undefined, and the delivery channel is an open question (§11 Q6). *Fix:* add **Alert**.
- **[medium]** **Household router** (§4.3 line 218 "the household router"; the §4.3 diagram line 221 labels the same device "ISP router"; FR-14 line 274 "the household router"; §7.2 line 868 "the existing router") — three names for one device, one of them inside the ASCII diagram that FR-14 depends on. *Fix:* one name, added to §3 or at least fixed in §4.3.
- **[medium]** **GitOps** (§7.1 line 857, line 864; SM-4 line 888) — a mechanism name in the scope list and a primary success metric, while FR-42 (the requirement it corresponds to) carefully avoids it in favour of "reconciles from the Repository". §0 line 16 forbids mechanism in this document. *Fix:* "reconciliation from the Repository".
- **[medium]** **SSO** (§4.11 line 629, §7.1 line 859, §9 D6/D10, §4.7 heading) — used as if defined; §3 defines **Relying Party**, **Token**, **IdP** but not SSO. *Fix:* add, or replace with "IdP authentication".
- **[low]** **NFS** — FR-18's title is "PostgreSQL does not run on NFS" and FR-65's Notes say "NFS under FR-15 and FR-17". The Glossary defines **Share** and **Off-NFS Store** (which itself embeds "NFS"), so NFS is half-defined by implication only. *Fix:* define **NFS** or restate FR-18 as "PostgreSQL does not run on a Share".
- **[low]** **PostgreSQL** / **Redis** as product names in §4.10 headings and FRs (lines 596, 600, 609, 610, 618) — mechanism leak per §0 line 16, though the brief settled both. Accept or note the exemption explicitly.
- **[low]** `huginn`, `muninn`, `gjallarhorn`, `ratatoskr`, `andvari`, `vanaheim` — instance names used in §4.10 (line 596), §4.11 (line 629), §7.2 (line 873) and §9 D5/D6/D7 (lines 932–934) with no Glossary entry, while `mimir`, `forseti`, `fafnir`, `draupnir` and `nidavellir` all have one. Asymmetric. *Fix:* either add the missing five or cite the addendum registry once and stop naming instances in §4/§9.
- **[low]** "the lab" (§4.14 description, line 753) — **Asgard** is the term. *Fix:* "Asgard".
- **[low]** "host" / "every host" — used ~15 times (FR-15 line 285, FR-20, FR-23 line 360, FR-24, FR-32, NFR-12, NFR-13, NFR-20, §7.1 line 853, SM-3 line 887, SM-7 line 894). It reliably means "Node or Guest" but is never defined; SM-3 and SM-7 are success metrics whose subject is therefore undefined. *Fix:* add **Host** — a Node or a Guest — to §3; it is the single highest-frequency undefined noun in the document.
- **[low]** **Relying Party** list drift — §3 line 91 enumerates "Yggdrasil's API, the hypervisor UI, Nidavellir, and Workloads"; §4.7 line 433 and FR-32 add the observability stack; §9 D10 adds forward-authed services. The definition's enumeration is stale relative to §4.7. *Fix:* make the Glossary list open-ended or add observability.

---

## 2. FR ID Continuity

**Enumerated from `^#### FR-` headings (65 headings, lines 127–783).**

Present, each exactly once: FR-1 … FR-65. Document order:
FR-1(127), 2(136), 3(145), 4(153), 5(161), 6(175), 7(183), 8(192), 9(200), 10(208),
11(232), 12(241), 13(249), **65(257)**, 14(269), 15(283), 16(292), 17(301), 18(310),
19(318), 20(333), 21(342), 22(350), 23(358), 24(369), 25(381), 26(393), 27(407),
28(415), 29(423), 30(437), 31(446), 32(455), 33(464), 34(474), 35(483), 36(493),
37(508), 38(517), 39(525), 40(535), 41(544), 42(559), 43(568), 44(577), 45(586),
46(600), 47(609), 48(618), 49(633), 50(642), 51(651), 52(660), 53(674), 54(683),
55(692), 56(707), 57(716), 58(725), 59(733), 60(742), 61(757), 62(766), 63(774),
64(783).

- **Gaps:** none. 1–65 is a complete contiguous set.
- **Duplicates:** none. No FR number appears as a heading twice.
- **FR-66:** fully absent — zero occurrences anywhere in `prd.md`, `brief.md`, or `addendum.md`. Confirmed gone.
- **Confirmed:** the FR-65-at-line-257 placement is the **only** ordering anomaly.

Findings:

- **[low]** Out-of-order FR-65 is undocumented as deliberate (line 257) — a reader or a diffing tool sees a numbering defect. Every other FR is in ascending order; nothing in §4 or §0 explains the exception. *Fix:* add one line to §0's structure paragraph (line 16), e.g. "FR numbers are stable and never reused; FR-65 appears out of sequence in §4.3 because it was added after renumbering was frozen."
- **[low]** FR-65's block is the only FR carrying a **Notes:** subsection inside §4.1–§4.4 (lines 267) while FR-23, FR-25 carry them in §4.5 — formatting is consistent enough, but FR-65's Notes is by far the longest and reads as a mechanism/rationale block, which §0 line 16 assigns to the addendum. *Fix:* trim to the constraint; the rationale already exists at `addendum.md:28` and `addendum.md:287`.

---

## 3. Cross-Reference Integrity

### 3a. FR-N references — all targets exist

Every `FR-N` cited outside its own heading resolves to a real requirement. Full
list of citing sites, verified: FR-2 (line 189 in FR-7; 799 NFR-1 area; 886 SM-2;
901 SM-C1; 949 §10), FR-4 (555, 591, 670, 801, 949), FR-15/FR-17 (267, FR-65 Notes),
FR-18 (596 §4.10; 953 §10; 958 §11 Q2), FR-24 (367 FR-23 Notes ×2; 391 FR-25 Notes;
947, 952 §10), FR-25 (947 §10; 957 §11 Q1), FR-27 (550 FR-41), FR-32 (665 FR-52;
887 SM-3; 968 §12), FR-36 (818 NFR-15), FR-50 (818 NFR-15), FR-51 (738 FR-59;
764 FR-61; 896 SM-9; 962 §11 Q6), FR-62 (946 §10), FR-63 (953 §10), FR-65 (951 §10),
FR-10 (952 §10), FR-16 (946 §10), FR-21 (957 §11 Q1), FR-14 (966 §12), FR-17 (967 §12),
FR-56 (969 §12), plus all SM "Validates" lists.
**No dangling FR reference exists.**

### 3b. NFR-N references — all targets exist

NFR-1 … NFR-23 all defined (§5.1–§5.5, lines 798–832). Cited at: NFR-2 (901 SM-C1),
NFR-4 (949 §10), NFR-6 (870 §7.2; 950 §10; 970 §12), NFR-8 (950), NFR-9 (950),
NFR-18 (953 §10). **No dangling NFR reference.**

### 3c. SM-N references — all targets exist

SM-1 … SM-10, SM-C1 … SM-C4 defined (lines 885–904). Cited at: SM-1 and SM-2 (901,
SM-C1 "Counterbalances"), SM-6 (902, SM-C2), SM-1 (904, SM-C4), SM-1 (938, §9 D11).
**No dangling SM reference.**

### 3d. Success Metric → FR validity (semantic check)

- **[critical]** SM-10 cites FR-22, which it cannot possibly validate (§8, line 897) — `**SM-10: The second application is boring.** Deploying a second SSO-protected Workload requires no new Procedure. Validates FR-22, FR-44.` FR-22 (line 350) is "Disabling an Account revokes host access". There is no relationship. Almost certainly a typo for **FR-33** ("Workloads can be registered as Relying Parties", line 464) or **NFR-22** ("Adding a Node, Guest, or Workload follows an existing Procedure rather than requiring a new one", line 831) — NFR-22 is a near-verbatim match for SM-10's wording. *Fix:* `Validates FR-33, FR-44, NFR-22.`
- **[high]** SM-3 asserts a 15-minute bound over a surface no FR bounds (§8, line 887) — "A single Directory Account authenticates SSH to every host, `kubectl`, the hypervisor UI, Nidavellir, and observability; **disabling it removes all of them within 15 minutes**." Of the cited FRs, only FR-35 (line 483) carries a 15-minute bound, and FR-35 scopes it to **Relying Parties**. SSH/host authentication is FR-22, which states no interval at all ("Authentication fails on every host after the Account is disabled" — line 355, unbounded). SM-3 therefore measures something no requirement specifies. *Fix:* either add a revocation-latency consequence to FR-22, or narrow SM-3 to "…removes Relying Party access within 15 minutes and host access on next authentication."
- **[medium]** SM-4 omits FR-43, which its own scenario requires (§8, line 888) — "An application written by the operator, deployed through GitOps" cannot happen without FR-43 (container image built and stored in the internal registry, line 568); §9 S7 is gated on the same. *Fix:* add FR-43 to SM-4's Validates list.
- **[medium]** SM-1's Validates list omits FR-4 (§8, line 885) — "rebuilt using only the Repository and Break-glass credentials" is precisely FR-4 ("All configuration originates in the Repository", line 153) and FR-55 (break-glass held outside Asgard, line 692). It cites FR-1, FR-3, FR-7, FR-64. *Fix:* add FR-4 and FR-55.
- **[low]** SM-6 omits FR-58 (§8, line 890) — a Drill "with mains removed" producing a completed Shutdown Sequence is exactly what FR-58 (all participants on battery-backed outlets, line 725) makes possible; without it the Drill fails. *Fix:* add FR-58.
- **[low]** SM-5 omits FR-61 and FR-62 (§8, line 889) — "Every backed-up class of data has an executed, verified restore" presupposes FR-61's enumerated coverage. *Fix:* add FR-61.
- **[low]** SM-C3 "Counterbalances nothing directly" (§8, line 903) — the only counter-metric with no target, breaking the pattern the other three establish. Not an error, but it should say so more explicitly or be moved out of the counter-metric list.

### 3e. FR → UJ "Realizes" validity (semantic check)

All 6 UJs referenced exist. Plausibility:

- **[medium]** §4.3 "Realizes UJ-3" is a stretch (line 218) — UJ-3 (line 57) is entirely about logging into an unfamiliar host with a Directory Account and finding a portable Home Directory. Name resolution is a precondition, not a realization; the journey's substance is realized by §4.4 (FR-15) and §4.5 (FR-20). *Fix:* drop the claim from §4.3, or restate UJ-3's edge case to include "reaches it by name".
- **[medium]** FR-45 "Realizes UJ-6" is a stretch (line 588) — UJ-6 (line 66) is *"He snapshots a guest, makes a change he expects to be destructive, observes the failure mode, and rolls back."* That is FR-9 (Guest snapshot/rollback), not FR-45 (Workload deployment rollback through the Repository). The two rollbacks are different mechanisms at different layers. *Fix:* either leave FR-45 unlinked or extend UJ-6 with a deployment-rollback beat.
- **[medium]** UJ-4's notification beat is realized by an FR that does not claim it (line 61 vs FR-59 line 733) — UJ-4's **Climax** is *"Kevin learns about it from a notification and a clean log"*. FR-56 and FR-57 carry "Realizes UJ-4"; FR-59 ("Power events are visible and alerted"), which is the only requirement that actually delivers the climax, does not. *Fix:* add "Realizes UJ-4" to FR-59.
- **[medium]** UJ-4's edge case has no requirement at all (line 61) — *"if power returns mid-shutdown, the sequence completes rather than racing a restart."* No FR in §4.13 states this. FR-56 (line 707) covers "sustained power loss"; nothing covers power restoration during the Shutdown Sequence. *Fix:* add a consequence to FR-57, e.g. "Mains restoration during the Shutdown Sequence does not abort or interleave with it."
- **[medium]** UJ-1's edge case is realized, but by an FR that does not cite the edge case (line 52 vs FR-3 line 145) — UJ-1's edge case ("a manual step was missing from the runbook … gets fixed in the same sitting") is exactly FR-3, which does say "Realizes UJ-1". This one is fine; noting it only because the reverse mappings below are not.
- **[low]** §4.9 "Realizes UJ-2" (line 555) and FR-44 "Realizes UJ-2" (line 579) — correct and consistent.
- **[low]** FR-39 "Realizes UJ-2, UJ-5" (line 527) — both hold (kubectl for UJ-2; the "Removing an Account from a Group removes access" consequence for UJ-5).

### 3f. Structural inconsistency in the "Realizes" convention itself

- **[medium]** Five of fourteen feature groups carry no `Realizes UJ-N` on their Description line: §4.6 (line 403), §4.10 (line 596), §4.11 (line 629), §4.12 (line 670), §4.13 (line 703), §4.14 (line 753). §4.12/§4.13/§4.14 recover it at FR level (FR-55, FR-56/57, FR-64), but **§4.6 Certificate Authority, §4.10 Stateful Services and §4.11 Observability have no UJ link at any level.** *Fix:* either link them (§4.6 → UJ-2, since UJ-2 opens an HTTPS URL; §4.11 → UJ-4, since UJ-4's climax is a notification and a clean log) or state in §0 that the convention is best-effort.

### 3g. §11/§12 references

All valid: §11 Q1 → FR-21, FR-25, §4.6 (exists); Q2 → FR-18; Q6 → FR-51.
§12 → FR-14, FR-17, FR-32, FR-56, NFR-6, §9. **No dangling reference.**

---

## 4. UJ Coverage

§2.3 defines UJ-1 … UJ-6 (lines 51–67). Realization map:

| UJ | Realized by | Verdict |
|---|---|---|
| UJ-1 | §4.1 (121), §4.2 (171), FR-3 (147), FR-7 (185), FR-55 (694), FR-64 (785) | Covered, heavily |
| UJ-2 | §4.7 (433), §4.8 (504), §4.9 (555), FR-31 (448), FR-33 (466), FR-39 (527), FR-44 (579) | Covered |
| UJ-3 | §4.3 (218), §4.4 (279), §4.5 (329), FR-15 (285), FR-20 (335) | Covered |
| UJ-4 | FR-56 (709), FR-57 (718) | Covered (partially — see 3e) |
| UJ-5 | §4.5 (329), §4.7 (433), FR-22 (352), FR-35 (485), FR-39 (527) | Covered |
| UJ-6 | §4.2 (171), FR-9 (202), FR-45 (588) | Covered |

**No orphan journeys.** Findings are about depth, not existence:

- **[medium]** UJ-4 is the thinnest-covered journey — only two FRs cite it, and neither covers its Climax (notification, FR-59) or its Edge case (mid-shutdown power return, unrequired). See 3e. *Fix:* as above.
- **[medium]** UJ-1's central promise is realized by FR-7 but not measured end-to-end by the delivery plan — UJ-1 says the rebuilt Node "rejoin[s] the cluster and pick[s] up its share of guests"; FR-7's third consequence covers it (line 190) and §9 D11 is the Drill. Fine. But UJ-1 also says "adds the node to inventory in Git" — no FR names an inventory artifact; FR-4 and FR-12 are the closest. *Fix:* accept, or add a consequence to FR-8/FR-12 naming Node inventory as Repository content.
- **[low]** UJ-6 is realized by FR-9 but FR-9 is the only FR in §4.2 with no downstream Success Metric and no epic (see checks 7 and 8). The journey exists and is claimed; the delivery evidence does not.
- **[low]** UJ-2's beat "commits manifests to the platform repository, and lets GitOps converge" is FR-42, which does **not** say "Realizes UJ-2" though its parent §4.9 does. Consistent with how the document handles group-level claims elsewhere; noted for symmetry only.

---

## 5. Assumptions Index Roundtrip (§12)

§0 line 16 states the contract: *"Inferences carry inline `[ASSUMPTION]` tags,
indexed in §12."*

- **[critical]** Zero inline `[ASSUMPTION]` tags exist in the document. A grep for `ASSUMPTION` over `prd.md` returns exactly one hit: line 16, the sentence promising them. §12 lists six entries (lines 966–971), none of which corresponds to any inline marker in §4–§11. **The declared roundtrip is broken in one direction entirely** — a reader working forward from §4 has no way to know which statements are inferences, which is precisely the affordance §0 promises. *Fix:* either insert the six `[ASSUMPTION]` tags at their cited locations (§4.3/FR-14 line 269–276, §4.4/FR-17 line 301–308, §4.7/FR-32 line 455–462, §4.13/FR-56 line 707–714, §5.2/NFR-6 line 806, §9 line 908) or amend §0 to say assumptions are collected in §12 only.
- **[high]** Both `[NOTE FOR PM]` tags are missing from §12 (lines 872 and 875) — §7.2 line 872 (`PostgreSQL high availability … [NOTE FOR PM] revisit if a Workload becomes something the operator would miss`) and line 875 (`Remote access of any kind … [NOTE FOR PM] this removes an entire plane from the design`). These are the only two inline PM-facing tags in the document and neither is indexed. The second one is the more serious omission: it flags a scope cut that check 6 shows has stale survivors. *Fix:* add a "Notes for PM" subsection to §12 listing both with their §7.2 line anchors.
- **[high]** Six genuine inferences carry no tag and no index entry:
  - **FR-35's 15-minute figure** (line 483, 488, 491) — the number appears nowhere upstream. `brief.md` and `addendum.md` never state a token lifetime. It is a PRD-originated inference elevated to an FR title and a primary success metric (SM-3). *Fix:* index it.
  - **§4.13's "eight to fifteen minutes"** (line 703) — matches no upstream figure (see check 6). *Fix:* index and reconcile.
  - **FR-13's resolver redundancy** (lines 249–255) — nothing upstream requires more than one resolver; `brief.md` and `addendum.md` are silent on DNS resilience. *Fix:* index.
  - **FR-25's Directory replica as a hard requirement** (line 381, and §7.1 line 853) — `addendum.md:127` explicitly calls the second replica *"a should-have"*. The PRD promotes it to a must-have FR plus an MVP scope bullet without tagging the promotion. *Fix:* index, or state the promotion in FR-25's Notes (line 391, which currently argues availability but does not acknowledge the upstream priority change).
  - **NFR-6's 20 GB floor** — indexed at line 970, but note the figure itself contradicts upstream (see check 6); the index entry does not acknowledge that.
  - **FR-58's inclusion of the network switch** (line 730) — sourced from `addendum.md:235/251`, so arguably not an inference; but the PRD states it as a testable consequence without citation while §4.13's description cites nothing. *Fix:* low priority.
- **[medium]** §12 entry "§4.4 / FR-17" is mis-anchored (line 967) — the assumption text is *"Nidavellir's storage is sufficient for both Home Directories and all Persistent Volumes"*. Home Directories are **FR-15** (line 283); FR-17 covers only Persistent Volumes. *Fix:* anchor to "§4.4 / FR-15, FR-17".
- **[medium]** §12 entry "§4.13 / FR-56" reintroduces a mechanism figure (line 969) — "the real ~315 W load" is an addendum number (`addendum.md:214`) that §0 line 16 assigns to the addendum. Also, the PRD nowhere else states 315 W, so the index entry is the only place the reader meets it. *Fix:* cite the addendum rather than restating the figure.
- **[low]** §12 entry "§9" (line 971) has no FR/NFR anchor, unlike the other five. *Fix:* anchor to §9 Phase 0 / S7.

---

## 6. Brief and Addendum Contradictions

### 6a. Remote access — stale survivors of a scope cut

The cut is asserted in four places: `prd.md:841` (§6 "Not remotely accessible. No
VPN, no tunnel, no inbound path"), `prd.md:875` (§7.2), `prd.md:817` (NFR-14),
`brief.md:90`, `addendum.md:141` and `addendum.md:289`. Survivors:

- **[critical]** The PRD contradicts itself six lines apart (§7.2, line 869) — `- **Public DNS and ACME certificates** — an internal authority is sufficient for **a LAN-and-VPN platform**.` The very next-but-one bullet (line 875) says "Remote access of any kind — no VPN, no inbound path", and §6 line 841 and NFR-14 line 817 say the same. This is a direct, in-document contradiction and a verbatim survivor of the pre-cut wording. *Fix:* "…sufficient for a LAN-only platform."
- **[high]** Addendum carries the identical stale phrase (`addendum.md:197`) — `| Public DNS, ACME certificates | Deferred | An internal CA is sufficient for a **LAN/VPN-only lab**. Registering a domain now keeps the option open. |` Same defect, same origin. The trailing "Registering a domain now keeps the option open" also contradicts `brief.md:90` ("No public DNS") and `prd.md:837`. *Fix:* "LAN-only lab"; drop or requalify the domain-registration clause.
- **[medium]** Addendum naming registry assigns `bifrost` to VPN entry (`addendum.md:64`) — `| bifrost | Ingress, reverse proxy, VPN entry | The bridge between realms |`. VPN entry is a cut capability. The PRD never uses `bifrost`, so nothing downstream breaks yet, but the registry is the artifact FR-11 line 239 defers to ("Names follow the Norse registry in the brief addendum"). *Fix:* "Ingress, reverse proxy".
- **[low]** Addendum inventory row for the travel router (`addendum.md:22`) — "Useful as a portable VPN client or an isolated test bench." Out-of-lab use, arguably fine, but it is the third VPN mention in a document that declares the plane cut. *Fix:* leave or annotate as out-of-scope hardware.
- **[low]** §11 Q6 depends on the cut but does not resolve it (`prd.md:962`) — "With no remote access plane, a channel reachable only from the LAN would not reach the operator when away." Correctly consistent with the cut; noted as the one place the cut is reasoned about downstream. No fix.

### 6b. UPS — model and specification survivors

Model: **SMT1500C** is consistent everywhere it is asserted as the choice
(`brief.md:124`, `addendum.md:26/202/221`, `prd.md:961`). BX1500M and BR1500MS2
appear only at `addendum.md:223`, inside an explicit selection-history narrative
that names both as rejected — **that is correct and should stay**. No stale
model survivors found. But the *numbers* did not travel cleanly:

- **[high]** Four different battery-runtime figures across three documents:
  - `prd.md:703` (§4.13) — "The UPS buys **eight to fifteen** minutes"
  - `brief.md:105` (Constraints table) — "~315 W load, **~8-12 min** runtime"
  - `brief.md:124` (Resolved Foundation Decisions) — "~315 W load, ~3.2x headroom, **~12-15 min** runtime"
  - `addendum.md:217` — "Expected runtime at ~315 W is **8-12 minutes**"; `addendum.md:264` repeats "8-12 minutes"

  The brief contradicts *itself* (8-12 vs 12-15), and the PRD's 8-15 is the union of the two brief figures rather than either source. Since FR-56's consequence is "The Shutdown Sequence completes within the battery's **proven** runtime, with margin" (line 713) and §12 line 969 indexes it as measured-not-assumed, the risk is contained — but three documents state three different unmeasured numbers. *Fix:* pick one figure (8–12 min, the addendum's derived value), correct `brief.md:124`, and restate §4.13 as "The UPS buys roughly eight to twelve minutes".
- **[medium]** Addendum contradicts its own UPS wattage (`addendum.md:217` vs `:221`) — line 217 says "Against **900 W** the unit runs at roughly a third of capacity"; line 221 says "**1500 VA / 1000 W**", and `brief.md:124` says "1500 VA / 1000 W, … ~3.2x headroom". 315 W × 3.2 = 1008 W, so 1000 W is the live figure and 900 W is stale (900/315 = 2.86x, and 315/900 is 35%, not "roughly a third" of 1000 either way). *Fix:* "Against 1000 W the unit runs at roughly a third of capacity."
- **[medium]** The brief's ~5-minute shutdown budget vanishes from the PRD (`brief.md:105`, `addendum.md:262`) — "The full stack must power down inside **~5 min**, NAS last", and the addendum's phase table (`addendum.md:256-262`) budgets 60+60+60+60+30 s = ~5 min. The PRD's FR-56 (line 713) states only "within the battery's proven runtime, with margin" and §4.13 states no budget. Given §6 line 842 ("Not optimized for build speed") governs *rebuild* time, not shutdown time, dropping the shutdown budget is a real loss of a testable bound. *Fix:* add a consequence to FR-56: "The Shutdown Sequence completes within five minutes of its start."
- **[low]** §11 Q5 states the compatibility gate as "before purchase" (`prd.md:961`) while `addendum.md:243` states it as "before the design depends on it" — the addendum's framing is weaker and the brief already lists the SMT1500C in **Resolved Foundation Decisions** (`brief.md:124`), i.e. as settled. Three different commitment levels for the same gate. *Fix:* align on the PRD's "before purchase" and demote the brief's row to conditional, or resolve the gate.

### 6c. Other cross-document contradictions

- **[medium]** Argo CD is an OIDC client upstream, absent downstream (`brief.md:44` vs `prd.md` §4.7/§4.9/§9 D10) — the brief says "the Kubernetes API server, Proxmox, Grafana, **Argo CD**, and the NAS itself all become OIDC clients", and `addendum.md:136` lists "Grafana, **Argo CD**, Harbor, Gitea, Vault | Native OIDC clients". FR-32 (line 457) enumerates only "the hypervisor UI, the observability interface, and Nidavellir", and §9 D10 (line 937) enumerates "Hypervisor UI, Nidavellir, observability, forward-auth". The GitOps controller's own interface is a Relying Party upstream and is not required anywhere downstream. *Fix:* add it to FR-32's enumeration, or record the drop as a deliberate narrowing in §7.2.
- **[medium]** Wired-only networking is in the brief's MVP scope list but not the PRD's (`brief.md:84` vs `prd.md` §7.1 lines 850–864) — the brief's in-scope list ends with "**Wired-only networking for all Nodes and the NAS, wireless disabled**". FR-65 requires it (line 257) and §10 line 951 cites it, but §7.1 In Scope never mentions it. *Fix:* add a §7.1 bullet.
- **[medium]** FR-25's Directory replica is a must in the PRD, a "should-have" in the addendum (`prd.md:381` + `:853` vs `addendum.md:127`) — see check 5. The PRD makes it a hard FR *and* an MVP scope item; the addendum says "A second directory replica is a should-have." FR-25's Notes (line 391) argue for it but never acknowledge that upstream ranked it lower. *Fix:* record the promotion.
- **[medium]** Headroom figure disagrees three ways — `prd.md:806` NFR-6 "at least **20 GB** of RAM unallocated"; `brief.md:100` "roughly **25–30 GB** headroom"; `addendum.md:46` "**~28 GB**". A floor of 20 below a modelled 28 is defensible, but §12 line 970 indexes "20 GB … is a sufficient experimentation budget" as an assumption without noting it is 8 GB below the capacity model. *Fix:* state the relationship in NFR-6 or in the §12 entry.
- **[low]** Grafana classed differently (`brief.md:12` vs `prd.md` §4.10/§4.11) — the brief calls Grafana one of "a set of stateful backing services (PostgreSQL, Redis, Grafana)"; the PRD puts PostgreSQL and Redis in §4.10 Stateful Services and Grafana (as `huginn`) in §4.11 Observability. A reasonable restructuring, not a contradiction, but it means "stateful services" means different sets in the two documents.
- **[low]** Addendum cites downstream FR numbers (`addendum.md:140` "Break-glass under FR-24"; `addendum.md:287` "recorded as FR-65") — an upstream artifact taking a dependency on PRD numbering. §0 line 16 promises FR numbers are stable, so this holds today, but it is a backward reference that will silently rot if §4 is ever renumbered. *Fix:* accept knowingly, or have the addendum cite capability names instead.
- **[low]** Addendum epic table skips 12 (`addendum.md:172-188`) — rows run 0,1,…,11,**12b**,13,14. There is no 12 and no 12a. The PRD's §9 replaces this table entirely (S1–S7, D1–D11), so nothing downstream breaks, but the addendum is left with a visible numbering hole. *Fix:* renumber to 12.
- **[low]** `hel` is a defined tier upstream and unused downstream (`addendum.md:65` "Backup and archive tier"; `addendum.md:177` epic 3 "`hel` as a backup target") — §4.14 and §9 D9 describe backups with no reference to `hel`, while FR-62 (line 766) requires "Backups are stored on a system independent of their source" without naming where. *Fix:* either name `hel` in §4.14 or drop it from the addendum's epic 3 delivery.
- **[low]** "Nodes ship Windows / all four are reimaged" (`brief.md:106`, `addendum.md:16`) has no PRD counterpart — FR-7 (Node rebuild) assumes a clean base but §7.2 line 874 explicitly permits manual hypervisor installation. Not a contradiction; a dropped constraint. *Fix:* optional.

---

## 7. Delivery Plan (§9) Coverage

Epics: Phase 0 S1–S7 (lines 914–920); Phase 1 D1–D11 (lines 928–938).

### 7a. Feature-group → epic map (every §4 group is reachable)

| §4 group | Epic(s) | Verdict |
|---|---|---|
| 4.1 Procedure Discipline | S1, D11 | Covered |
| 4.2 Hypervisor Foundation | S2 | Partly — see below |
| 4.3 Network / DNS | S2 | Partly — see below |
| 4.4 Shared Storage | S3, D1 | Covered |
| 4.5 Identity | S4, D2 | Covered |
| 4.6 Certificate Authority | S5 | Covered |
| 4.7 SSO | S5, D10 | Covered |
| 4.8 Yggdrasil | S6, D3 | Covered |
| 4.9 Continuous Delivery | S7, D4 | Covered |
| 4.10 Stateful Services | D5 | Covered |
| 4.11 Observability | D6 | Covered |
| 4.12 Secrets | S1, D7 | Covered |
| 4.13 Power Continuity | D8 | Covered |
| 4.14 Backup and Recovery | D9, D11 | Partly — see FR-64 below |

**No feature group is orphaned.** The gaps are at FR granularity:

### 7b. FRs no epic delivers

- **[high]** FR-9 (Guest snapshot and rollback, line 200) is delivered by no epic — it appears in no Phase 0 or Phase 1 row, and NFR-23 ("Snapshot-before-change is available for every Guest", line 832) has no epic either. §4.2's description (line 171) calls snapshots "a first-class safety mechanism because fearless experimentation is a stated purpose", and §1 line 24 calls fearlessness "the actual deliverable". The document's stated headline capability has no delivery vehicle and no scope bullet (see check 8). *Fix:* add snapshot capability to S2 ("four Nodes clustered, snapshot/rollback, first rebuild Runbook") or as a distinct deepen epic.
- **[high]** FR-13 (name resolution survives a single failure, line 249) is delivered by no epic — S2 delivers "Address plan, `asgard.home.arpa`, four Nodes clustered" (line 915), which is single-resolver by the skeleton's own logic ("Nothing in the skeleton is redundant", line 908). No deepen epic covers DNS. Yet §7.1 line 851 puts "**resilient** name resolution" in MVP scope. There is no D-epic for network/DNS depth at all. *Fix:* add "DNS depth" to Phase 1, or fold resolver redundancy into D2 (the Directory carries DNS if FreeIPA wins §11 Q1 — but that dependency is unstated).
- **[medium]** FR-10 (Cluster manageable when the Directory is unavailable; Guest console access, line 208) is delivered by no epic — D2 delivers "Break-glass with local homes on every host" (line 929), which is FR-24, not FR-10. FR-10's Cluster-management-realm and console path is a distinct capability, cited by §10 line 952 as a risk response. *Fix:* name it in D2 or D10.
- **[medium]** FR-64 (rebuild the whole platform from Repository + backups, line 783) is only partially delivered — D11 (line 938) is scoped to "a **Node** destroyed and restored"; D9 (line 936) delivers verified restores per data class. Neither delivers the full-platform rebuild Procedure FR-64's first consequence requires ("A full rebuild Procedure exists and states its order", line 788). Note FR-64's own third consequence hedges to "A destructive Drill on at least one Node has proven it" — which is weaker than the requirement statement. *Fix:* either add the full-platform Procedure to D9/D11, or narrow FR-64 to match.
- **[medium]** FR-65 (wired-only Ethernet, line 257) is delivered by no epic — a hard constraint with four testable consequences, cited in §10 line 951, with no epic row. *Fix:* fold into S2.
- **[medium]** FR-26 (Accounts and Groups defined in the Repository, line 393) is delivered by no epic — S4 delivers "`mimir`, single instance; one Account logging into all four Nodes" (line 917); D2 delivers replica/caching/break-glass/group-auth (line 929). Declarative Account definition appears in neither. *Fix:* add to D2.
- **[medium]** FR-29 (certificates renew without manual action, line 423) is delivered by no epic — S5 delivers "Internal CA, trust distributed" (line 918). Automated renewal plus expiry alerting is a deepen capability with no D-epic. *Fix:* add to D6 (alerting) or a CA-depth row.
- **[medium]** FR-35 (15-minute revocation bound, line 483) is delivered by no epic — it is a primary metric input (SM-3) and requires per-Relying-Party configuration ("stated in each Relying Party's configuration", line 491), so it is real work. D10 "SSO breadth" (line 937) does not mention it. *Fix:* add to D10.
- **[low]** FR-14 (household devices unaffected, line 269) — a constraint rather than a deliverable; arguably needs no epic, but it is testable and unassigned.
- **[low]** FR-19 (storage capacity/health visible and alerted, line 318) — plausibly inside D6, which says "alerting", but Nidavellir health exporting is a storage-side task that D1 does not name. *Fix:* name it in D1 or D6.
- **[low]** FR-36 (authentication events recorded, line 493) — plausibly inside D6, unnamed.
- **[low]** FR-40 (Yggdrasil rebuildable from the Repository, line 535) — D3 "Yggdrasil depth" (line 930) lists control-plane spread, OIDC kubectl, ingress; rebuildability is unnamed.
- **[low]** FR-42 (reconciliation from the Repository, line 559) — S7 says "deployed from the Repository" (line 920) and D4 covers build/registry/rollback (line 931); the reconciliation controller itself is named in neither.
- **[low]** FR-55 (break-glass escrow outside Asgard, line 692) — S1 mentions "secret handling before a secret store exists" and D7 mentions "runtime secret delivery"; off-platform escrow is unnamed. §7.1 line 860 does list it.

### 7c. Epics delivering something no FR requires

- **[medium]** S1's "secret handling before a secret store exists" (line 914) has no FR — §4.12's description explicitly raises "the bootstrap problem of holding them before a secret store exists" (line 670), but FR-53, FR-54 and FR-55 all describe the steady state. The bootstrap capability is described in a Description, delivered by an epic, and required by nothing. *Fix:* add an FR for bootstrap secret handling, or move the phrase out of S1.
- **[low]** D1's "on-demand mounting" (line 928) has no FR — it is the mechanism `addendum.md:156` recommends (autofs) and it is *implied* by FR-16's "Loss of the Share does not leave processes unkillable in uninterruptible sleep" (line 297), but §0 line 16 assigns mechanism to the addendum, so naming it in an epic is a leak in the opposite direction. *Fix:* "graceful Share unavailability" instead.
- **[low]** D6's `gjallarhorn` and D7's `andvari` (lines 933–934) name instances the PRD's Glossary does not define (see 1g). The capability behind each is required (FR-51, FR-54); the naming is the leak.
- **[low]** S1's "repository structure" (line 914) — covered by FR-4 loosely; no FR states a structure requirement. Acceptable.

### 7d. Phase-boundary consistency

- **[low]** §9's opening claim ("Nothing in the skeleton is redundant, resilient, or complete", line 908) is consistent with S4 delivering `mimir` as a "single instance" (line 917) — and correctly foreshadows the FR-13 gap in 7b: the skeleton *cannot* deliver FR-13, and no deepen epic does. This is the strongest evidence that FR-13's omission is an oversight rather than an intentional deferral.
- **[low]** §12's last assumption (line 971) says "The Walking Skeleton can reach S7 without any deepen-phase capability" — S7 requires FR-44 ("registration with the IdP, image build, declaration, and publication", line 582), but image build and the internal registry are D4 (line 931). S7 therefore appears to depend on a deepen-phase capability, which is exactly the condition the assumption says would move the phase boundary. *Fix:* either move minimal image build into S7's row or state that S7 may pull images built by hand.

---

## 8. §7.1 In Scope vs §4

Fifteen bullets, lines 850–864. Every bullet maps to at least one FR — **nothing is
in scope with no FR.** The asymmetry is in the other direction.

Bullet-by-bullet:

| §7.1 bullet (line) | FRs |
|---|---|
| Proxmox Cluster, declaratively provisioned (850) | FR-6, FR-8 |
| `asgard.home.arpa`, resilient resolution, address plan (851) | FR-11, FR-12, FR-13 |
| Nidavellir Home Dirs + PVs; PostgreSQL off-NFS (852) | FR-15, FR-17, FR-18 |
| Directory + replica, network login, Break-glass local homes (853) | FR-20, FR-24, FR-25 |
| Draupnir issuing all TLS, trust distributed (854) | FR-27, FR-28 |
| Forseti federated, fronting five surfaces (855) | FR-30, FR-32, FR-34 |
| Yggdrasil, 3 CP Guests, OIDC kubectl, name-and-TLS publication (856) | FR-37, FR-38, FR-39, FR-41 |
| GitOps reconciliation, image build and registry (857) | FR-42, FR-43 |
| PostgreSQL and Redis as shared services (858) | FR-46, FR-48 |
| Metrics, logs, alerting, SSO dashboards (859) | FR-49, FR-50, FR-51, FR-52 |
| Secrets, no plaintext, off-platform escrow (860) | FR-53, FR-54, FR-55 |
| UPS ordered Shutdown Sequence proven by Drill (861) | FR-56–FR-60 |
| Automated backup, verified restores (862) | FR-61, FR-62, FR-63 |
| Everything as a Procedure (863) | FR-1–FR-5 |
| Reference application (864) | FR-44 |

### FRs requiring something §7.1 does not list

- **[high]** FR-9 / NFR-23 — snapshots (lines 200, 832). No §7.1 bullet mentions snapshot or rollback of a Guest. Combined with 7b, the platform's stated safety mechanism is in no scope list and no epic. *Fix:* add "Guest snapshot and rollback" to §7.1.
- **[high]** FR-65 — wired-only Ethernet (line 257). A hard constraint with four testable consequences, in the brief's scope list (`brief.md:84`) and absent from the PRD's. *Fix:* add.
- **[medium]** FR-23 — credential caching for known Accounts during a Directory outage (line 358). §7.1 line 853 lists "Directory with replica, network login on every host, Break-glass access with local home directories" — caching is neither. It is delivered by D2 (line 929) and is a distinct, testable capability with its own Notes block. *Fix:* add to the line-853 bullet.
- **[medium]** FR-10 — Cluster manageable with the Directory down; Guest console reachable (line 208). §7.1's break-glass bullet is host-scoped. *Fix:* add.
- **[medium]** FR-16 — storage unavailability degrades rather than hangs (line 292). This is a named risk response (§10 line 946: "FR-16 bounds the blast radius") and is not in scope. *Fix:* add to the line-852 bullet.
- **[medium]** FR-64 — full-platform rebuild from Repository plus backups (line 783). §7.1 line 862 covers backup and restores; the rebuild Procedure is a separate deliverable and is the subject of SM-1. *Fix:* add.
- **[medium]** FR-29 — automatic certificate renewal and pre-expiry alerting (line 423). §7.1 line 854 stops at issuance and trust distribution. Renewal failure is also one of the alert conditions FR-51 enumerates (line 656), so it is doubly in scope by implication and absent by statement. *Fix:* extend the line-854 bullet.
- **[medium]** FR-35 — 15-minute revocation (line 483). Primary-metric input (SM-3, line 887), absent from scope. *Fix:* add to the line-855 bullet.
- **[low]** FR-45 — deployment rollback (line 586). Delivered by D4 (line 931), absent from §7.1's line-857 bullet.
- **[low]** FR-40 — Yggdrasil rebuildable (line 535). Absent from the line-856 bullet.
- **[low]** FR-36 — authentication events recorded (line 493). Arguably inside "Metrics, logs, alerting" (line 859), but the FR is specifically about auth events distinguishable success/failure and is cited by NFR-15 (line 818).
- **[low]** FR-19 — Nidavellir capacity/health visible and alerted (line 318). Arguably inside line 859; the storage-side half is not.
- **[low]** FR-14, FR-21, FR-26, FR-31, FR-33, FR-47 — each is implied by a §7.1 bullet but not stated. Lower priority than the above; listed for completeness.

### Scope-list phrasing issues

- **[medium]** "Proxmox Cluster … declaratively provisioned" (line 850) overstates the FRs — FR-6 (line 175) requires only that four Nodes form one manageable Cluster; FR-8 (line 192) makes *Guests* declarative. No FR requires the Cluster itself to be declaratively provisioned (FR-4 covers configuration generally). *Fix:* "Cluster across four Nodes; Guests provisioned declaratively."
- **[medium]** "resilient name resolution" (line 851) is in scope, FR-13 delivers it, and no epic implements it — see 7b. This is the one place all three checks converge on the same defect.
- **[low]** "fronting Yggdrasil, the hypervisor UI, Nidavellir, observability, and Workloads" (line 855) enumerates five Relying Parties; the Glossary's **Relying Party** entry (line 91) enumerates four (omitting observability); FR-32 (line 457) enumerates three (omitting Yggdrasil and Workloads, which are FR-39 and FR-33). Three different enumerations of the same set. *Fix:* enumerate once, in §3, and reference it.
- **[low]** §7.2 line 877 ("Additional hardware — beyond the UPS and, **optionally, 2.5 GbE adapters**") sits against §6 line 844 ("The platform targets the existing inventory plus the UPS"). §6 admits only the UPS; §7.2 admits adapters too. Minor internal drift. *Fix:* align §6.
- **[low]** §7.2 line 869's "LAN-and-VPN platform" — the critical finding from check 6a, also visible here as a scope-list defect.

---

## Cross-cutting internal contradictions (surfaced by the checks above)

Two findings do not belong to a single check but are mechanical, not editorial:

- **[high]** FR-22 and FR-23 contradict each other (lines 350–356 vs 358–365) — FR-22's consequence: "Authentication fails on **every host** after the Account is disabled." FR-23's consequence: "Credential caching permits login for a previously-authenticated Account with the Directory offline." If the Directory is offline (or the disablement has not propagated to the cache), a disabled Account still authenticates. FR-23's Notes (line 367) discuss the FR-24 interaction but never this one. SM-3 (line 887) measures FR-22's claim. *Fix:* bound FR-22 with "while the Directory is reachable", and add a cache-invalidation consequence to FR-23.
- **[high]** NFR-11 is falsified by FR-15 and FR-20 (line 814) — "**All** service-to-service and operator-to-service traffic within Asgard is encrypted with certificates chaining to Draupnir." SSH (FR-20, line 333; SM-3, line 887; SM-7) uses host keys, not Draupnir certificates; NFS Shares (FR-15, line 283; FR-17) are not TLS-bearing in the design the addendum describes (`addendum.md:148-156`). As written, NFR-11 is unachievable and would be read literally by an architecture workflow. *Fix:* "All service-to-service and operator-to-service traffic that uses TLS chains to Draupnir; no internal TLS endpoint presents a certificate outside that chain," and state the SSH/NFS exemptions.

---

## Summary of counts

| Check | critical | high | medium | low | total |
|---|---:|---:|---:|---:|---:|
| 1. Glossary discipline | 0 | 6 | 18 | 13 | 37 |
| 2. FR ID continuity | 0 | 0 | 0 | 2 | 2 |
| 3. Cross-reference integrity | 1 | 1 | 6 | 5 | 13 |
| 4. UJ coverage | 0 | 0 | 2 | 2 | 4 |
| 5. Assumptions Index roundtrip | 1 | 2 | 2 | 1 | 6 |
| 6. Brief/addendum contradictions | 1 | 2 | 5 | 6 | 14 |
| 7. Delivery plan coverage | 0 | 2 | 6 | 9 | 17 |
| 8. §7.1 In Scope vs §4 | 0 | 2 | 6 | 8 | 16 |
| Cross-cutting | 0 | 2 | 0 | 0 | 2 |
| **Total** | **3** | **17** | **45** | **46** | **111** |
