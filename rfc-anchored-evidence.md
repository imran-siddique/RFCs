# Anchored Evidence for SAFE

A proposed addition to the Shared AI Findings Exchange: independently checkable anchoring of preserved incident evidence, with a public reference registry available for evaluation.

Status: proposed, not adopted. Implementation status below was checked on September 15, 2026. This revision incorporates review discussion; it does not establish an Alliance acceptance decision.

# Background

SAFE states that trust is not a control, and that shared evidence and verifiable improvement are how trust is earned. Evidence Preservation gives that principle its operational form by listing what members must retain and provide after an incident.

The list is right. What it does not yet establish is when the evidence came into being, and whether the set provided is the set that existed.

Every item in Evidence Preservation is produced by systems the reporting member owns, retained in storage the member controls, and handed to reviewers on a schedule that runs from four business days to ninety. Nothing in the current draft lets a reviewer distinguish evidence recorded as an incident unfolded from evidence assembled afterwards with the review's questions already known.

This is not an accusation of bad faith. It is a statement about what the record can carry. The Review Framework already anticipates the tension when it says the affected organization may correct factual errors but should not have veto power over learnings or recommendations. That instruction assumes the facts are independently establishable. Under the current draft they are not.

# Scope of this proposal

This proposal is deliberately narrow. It concerns one property of preserved evidence: that its existence at a given time can be established by someone other than the member who produced it.

It does not propose a schema for evidence, an evidence format, a collection agent, an attestation envelope, a policy engine, or a transparency service with a business model attached. Those are separate questions, several of which are already under discussion elsewhere in this repository.

It proposes a requirement, describes a mechanism that satisfies it, and offers a working implementation of that mechanism to the alliance.

# The property

A reviewer should be able to establish, without trusting the member under review, that a given item of preserved evidence existed in its provided form at a stated time.

Call this anchoring. A member computes a digest of an evidence item, publishes that digest to a record it cannot retroactively alter, and retains a proof linking the two. Later, a reviewer holding the evidence and the proof recomputes the digest and checks it against the published record.

The public entry carries a batch root, a claimed timestamp, a count, and producer/batch metadata; it does not carry the evidence payload. Inclusion alone does not authenticate the timestamp. The reviewer also needs an independently checkable basis for the timing and history claims, described below.

# Why this fits SAFE specifically

Three features of the current draft make anchoring more useful here than in a general assurance framework.

**The timelines create a window.** SAFE gives four business days for an initial confidential report, thirty for a preliminary factual report, and ninety for remediation status. Throughout that window the evidence sits with the member, and the questions the review will ask become progressively clearer. Anchoring at the time of the incident fixes the evidence before the member can know what the review will focus on. The value comes precisely from anchoring early, which is the moment a member has the least idea what will matter.

**Payload disclosure can be separated from anchoring.** A member can publish a digest while retaining the evidence privately. That does not make publication free of disclosure risk: hashes of guessable material can support confirmation attacks, and producer identifiers and timing can reveal relationships. The disclosure model needs to account for those risks before any public anchor is written.

**Near misses become cheap to record.** The Reporting Compact requires reporting near misses, not only events producing confirmed harm. Near misses are exactly the class of event where the incentive to preserve evidence is weakest, because nothing went wrong and the work has no visible payoff. A member can anchor near-miss evidence routinely and decide later whether it is reportable. This still requires collection, retention, and operation of an anchoring service; it does not create a missing near-miss detection or reporting trigger.

# The mechanism

The batch tree follows the [RFC 6962 construction](https://www.rfc-editor.org/rfc/rfc6962.html#section-2.1). The [reference format](https://github.com/agentrust-io/trace-spec/blob/main/spec/registry-anchor-v1.md) describes the original sorted-key profile. The registry's [construction documentation](https://github.com/agentrust-io/trace-registry/blob/main/docs/anchor-format.md) and [entry schema](https://github.com/agentrust-io/trace-registry/blob/main/schema/registry-entry.schema.json) describe the current implementation's additive fields. These documents are not yet fully synchronized; this RFC does not treat the older five-field table as the complete current schema.

**Leaf.** The unit is the complete signed evidence object, including its signature. For the current implementation:

```
leaf = SHA-256(0x00 || leaf_bytes)
```

The entry's `canonicalization_id` selects how `leaf_bytes` is obtained:

- `sorted-key`: sorted-key ASCII JSON under the reference profile, which excludes non-integer numbers and integers outside the safe-integer range.
- `as-transmitted`: the exact signed bytes, without reserialization.

The two constructions bind different representations. A sorted-key proof binds the canonical representation, not every original whitespace or property-order choice. An as-transmitted proof binds the retained bytes. A verifier must retain the appropriate representation and must not silently substitute the signing canonicalizer.

**Tree.** Interior nodes are `SHA-256(0x01 || left || right)` over 32-byte child hashes. An unmatched final node is promoted unchanged rather than duplicated. The leaf and interior prefixes separate the two node types. Empty batches are rejected.

**Entry.** The current implementation uses newline-delimited JSON. The following lists its basic batch fields; optional checkpoint fields are defined in the linked schema.

| Field | Type | Meaning |
| ----- | ---- | ------- |
| `ts` | string | Publisher's claimed anchoring time, ISO-8601 UTC |
| `merkle_root` | string | `sha256:` followed by 64 lowercase hex characters |
| `leaf_count` | integer | Number of leaves, at least 1 |
| `producer` | string | Registered producer identifier in the implementation |
| `batch_id` | string | Producer-scoped batch identifier |
| `canonicalization_id` | string | Leaf construction, `sorted-key` or `as-transmitted` |

The earlier draft called the construction field `canonicalization`. This revision uses the implemented name, `canonicalization_id`. For historical entries that omit it, the reference implementation infers `sorted-key`, the construction used before the field existed. That is a documented compatibility rule, not permission to guess an unknown identifier or reinterpret an old entry under a new construction.

**Verification.** A reviewer needs the evidence representation, inclusion proof, and batch entry to check inclusion. Producer-key trust, signatures, authenticated timing, and history consistency are separate checks. The published `trace-verify` tooling exposes inclusion/signature, chain, and witness-receipt checks. The witness check has additional dependencies; the package should no longer be described as entirely standard-library-only.

Append-only history must be supported by retained observations, checkpoints, or independently held copies. Git history alone cannot expose a rewrite to a first-time observer who has no earlier or independent view.

# Canonicalization and the proposed number admission profile

Signing and anchor-leaf construction are separate layers. TRACE signing uses RFC 8785 JCS; the current registry leaf constructions above are not JCS. The earlier claim that cross-language floating-point serialization cannot be canonical was incorrect: [RFC 8785 section 3.2.2.3](https://www.rfc-editor.org/rfc/rfc8785.html#section-3.2.2.3) specifies ECMAScript number serialization. The sorted-key profile's number exclusion is a profile constraint, not a general limitation of JCS.

The discussion developed candidate material for a possible JCS leaf profile. It separates number serialization from evidence admission. In the proposed `safe-integer-admission` profile, admission is decided on the IEEE 754 binary64 value used by JCS: reject non-finite values and integer-valued values outside `[-(2^53 - 1), 2^53 - 1]` before canonicalization and hashing. A host language's integer/float type or the token's decimal spelling does not replace that rule. Exact quantities requiring a different numeric representation need an explicit encoding, such as a string.

The [candidate vectors at 8783ca10](https://github.com/lywinged/RFCs/tree/8783ca1036a16d0f7b497275e68997181ac73dcd/conformance/jcs-numbers) and [September 5 reproduction report](https://github.com/OpenSecureAIAlliance/RFCs/pull/18#issuecomment-5555129338) distinguish fourteen serialization cases from twenty-seven admission cases. These are reported numeric-primitive results, not a full JCS verifier, an end-to-end registry test, or an adopted SAFE requirement.

This revision does not change existing leaf hashes, register a JCS construction, or merge the candidate test bundle. Selection of a new leaf profile and its admission rules remains a working-group decision. Existing entries retain their original construction.

# What anchoring proves and what it does not

**Inclusion proves membership under a particular root.** It establishes that the evidence representation selected by the declared construction is a leaf in that batch, under the hash assumptions. It does not independently establish an honest wall-clock timestamp, append-only publication, or a single history seen by everyone.

**Timing and history need their own evidence.** Identify the checkpoint or timestamp witness, trusted keys, retained observations, and consistency checks actually used. A timestamp asserted by the registry operator is not automatically an independently authenticated time. A single receipt does not establish continuity or rule out split views; see [RFC 6962 section 7.3](https://www.rfc-editor.org/rfc/rfc6962.html#section-7.3).

**Signatures and truth remain separate.** Inclusion does not verify the producer signature or determine whether its key belongs to the claimed producer. A valid signature and anchor can still accompany false evidence.

**Anchoring does not establish completeness.** A member can omit events, start collection late, or anchor only a subset. Anchored run boundaries may help expose gaps within a declared capture model, but cannot by themselves prove that collection could not be bypassed or that all events were recorded.

**Attestation does not supply the missing properties automatically.** A reviewer must appraise measurements under declared roots and reference values, check freshness, and establish the binding to the producer key and evidence-producing instance. Attestation is not continuous observation of every event and does not establish complete capture or correct policy decisions. Physical-access exclusions and platform assumptions must be stated in the threat model; see the [RATS trust model](https://www.rfc-editor.org/rfc/rfc9334.html#section-7) and [freshness discussion](https://www.rfc-editor.org/rfc/rfc9334.html#section-10.4).

# Proposed additions to the draft

**Evidence Preservation.** Add to the required properties of preserved evidence, alongside the existing list of contents:

> For each preserved evidence item, members should record its anchoring status: `anchored`, where an inclusion proof and an independently checkable basis for the claimed timing and history are retained and provided alongside the item; `unanchored`, where the item is preserved but those properties cannot be independently established; or `unavailable`, where the status cannot be determined. The report should identify the leaf construction, checkpoint or witness, trusted keys, and checks actually performed. Valid inclusion with only an operator-asserted timestamp must not be silently upgraded to independently established time.

The requirement is that the status is stated, not that it is `anchored`. Most members will not anchor initially, and mandating it would either exclude them or produce false declarations. An unanchored item remains usable evidence provided it is labelled as such. A reviewer weighing a member's account against a third party's needs to know which parts of that account are independently fixed in time and which rest on the member's word, and today the framework gives them no way to tell.

**Producer basis.** Producer relationship, signing control, certification, runtime attestation, and temporal anchoring are composable dimensions. The earlier ordered `self` / `distinct-party` / `certified` / `attested` field conflated them. This revision proposes reporting the supporting evidence separately, following the [September 4 review](https://github.com/OpenSecureAIAlliance/RFCs/pull/18#issuecomment-5547780665):

- Identify the party under review, evidence producer, key custodian, permitted signing principals, and evidence supporting any claimed separation. Describe who can change signing policy or use administrative and recovery paths.
- Where certification is offered, identify the evaluated architecture or deployment, evaluator, scope, and validity evidence.
- Where runtime attestation is offered, retain the measurement, reference values or appraisal policy, freshness evidence, and binding to the producer key and evidence-producing instance.
- Report temporal inclusion, timing, and history checks independently of those producer properties.

A self-operated producer may be attested; a distinct-party producer may also be certified and attested. None of these combinations proves complete capture. A key held in the reviewed party's KMS does not establish separation from that party merely because the governance platform cannot export it.

Where a claim depends on cooperative signing, specify what prevents either party from producing an accepted record unilaterally, including policy changes and recovery paths. A certification of the architecture does not establish that a particular running instance preserved those controls. The wire representation and conformance requirements remain proposed.

**Review Framework.** The Monitoring layer asks whether operators could detect and interrupt unexpected behavior in real time. Add whether the evidence supporting that determination was anchored at the time of the events or assembled during the review. The two produce very different confidence in the same answer.

**From Lessons to Controls.** Recommendations must specify a reproducible verification method and the evidence to retain. Where a recommendation's verification depends on records produced by the party being verified, that recommendation should state whether those records are anchored. A verification method whose inputs the verified party can revise is not reproducible in the sense the section intends.

# Governance and contribution scope

The public reference registry is available for evaluation under its published licenses: Apache-2.0 for code and CC BY 4.0 for registry data, proofs, schemas, and documentation. We are asking Alliance members to review the requirement, evaluate interoperability, and identify independent producers, mirrors, and maintainers.

OPAQUE currently operates the registry and produced both entries. An independently operated witness has observed one checkpoint, but there is still no independent mirror or independent production contributor. A consortium can help address these operational gaps.

The earlier contribution offer included operation passing to others. This revision makes its scope explicit: any ownership transfer, hosting commitment, or ongoing maintenance obligation requires a separate agreement. This RFC does not transfer TRACE specification governance or ask SAFE to adopt TRACE. The working group may specify an interoperable requirement and use other implementations.

# Status of the reference implementation

As checked on September 15, 2026:

- The [repository](https://github.com/agentrust-io/trace-registry) is public. The format, reference tooling, schema validation, and scheduled anchoring pipeline are available. This update describes published artifacts; it does not report a new execution of the pipeline.
- It holds two entries, both produced by OPAQUE: the June 12 software example and the September 1 conference demonstration. Neither is a production Trust Record. There is no independent producer or independently operated mirror.
- Signed MMR checkpoints and chain-verification tooling are present. Checkpoint 1 covers the September entry. The June entry predates checkpointing and is outside that chain.
- The [September 7 evidence packet](https://github.com/agentrust-io/trace-registry/tree/main/docs/evidence/witness-2026-09-07) carries an offline-verifiable receipt from an independently operated witness for checkpoint 1's signing-body digest. Its protected header does not carry a witness timestamp or signed grade; `witness_time_established` and `grade_cryptographically_bound` remain false for that capture.
- That receipt does not certify registry continuity, prevent split views, cover the June entry, or prove payload retention. Future checkpoints are not automatically submitted to the witness. Independent observation of one checkpoint is not continuous witnessing.
- The [limitations document](https://github.com/agentrust-io/trace-registry/blob/main/LIMITATIONS.md) distinguishes inclusion, registered producer-key trust, checkpoints, witness receipts, and operational independence.

These artifacts support evaluation of the proposed mechanism. They do not demonstrate production scale or that the current deployment fully satisfies the independently established timing property proposed above.

# Open questions for the working group

**Anchoring unit.** Should members anchor individual evidence items, run boundaries, or the incident report itself? Item-level anchoring gives the finest verification granularity. Run-boundary anchoring is what makes gap detection possible. These are complementary and the working group may want both, but the requirement should say which.

**Retention against append-only.** The profile needs a retention and removal policy for public digests and metadata, separately from retained evidence payloads. Hashing is not a general guarantee of anonymity or confidentiality. The working group should obtain an appropriate privacy review rather than assume a public digest is always safe to retain.

**Producer identity against de-identification.** A registry entry names its producer. SAFE's disclosure model de-identifies at the advisory stage. If a member anchors evidence during an incident and the advisory is later de-identified, the anchor timestamps may correlate with the advisory and partly undo that. Pseudonymous or rotating producer identifiers would address it at some cost to accountability, and the working group should decide where that trades out.

**What certifies the evidence producer's independence.** The certification dimension above requires an identified evaluator but does not select a certification body. Two different evaluations are involved and they may need different evaluators: product architecture certification, establishing that the design preserves independence, and deployment configuration certification, establishing that the running instance still does. The second is the harder one, because it is a continuous property and certification schemes sample it at audit-time intervals. This proposal names the question rather than answering it. Attestation is another input to deployment appraisal, subject to the freshness and instance-binding limits above; it is not continuous observation. Raised by @victor-davidenko.

**Anchoring by the reporting member or by SAFE.** A member could anchor to a public registry directly, or submit digests to SAFE which anchors on their behalf. The first requires no trust in SAFE. The second is easier for members and gives SAFE a role in establishing timing, at the cost of making SAFE a party to the record.

# Relationship to existing discussion

This proposal builds on issue #11 and is intended to complement rather than replace the discussion there.

The authors' discussion identifies #18 as the temporal-anchoring and producer-basis component, with #27 covering linked handling, transformation, and durable acceptance. This is a proposed interface boundary. The branches remain separate and no consolidation or Alliance adoption is claimed.

Issue #11 established that Evidence Preservation specifies contents without integrity properties, and its thread converged on three determinations a reviewer should be able to make: that records were not altered, that the record set is continuous or its gaps declared and bounded, and that the point at which recording began was fixed independently of the operating member. External anchoring was named there as a requirement, by @bobleer, without a mechanism attached. This proposal supplies one and takes no position on the other two.

Issue #14 proposes a per-item provenance grade. Anchoring status is orthogonal to that grade and complements it, since a provenance claim is more useful when the time at which it was made is externally fixed.

Issue #6 proposes signed, offline-recomputable tool-trust verdicts. Those verdicts are evidence and can be anchored, which addresses when a verdict was issued rather than only who issued it.

Issue #4 concerns verification methods that fail open. An anchored record of a verification result does not stop the method failing open, and the two should not be confused.

The companion [Chain-of-Custody Receipt Profile](./rfc-evidence-custody-receipt-profile.md) adds evidence of origin, linked handling transitions, transformations and durable receiver acceptance, together with conformance cases that keep these properties separately assertable. It references this proposal for the anchoring mechanism, statuses, producer basis and their limits. An anchor does not substitute for missing custody evidence, and durable acceptance does not imply temporal anchoring.

# Disclosure

Submitted by Imran Siddique, OPAQUE Systems. OPAQUE maintains TRACE and the reference registry described here. This proposal does not claim standards-body adoption of TRACE or ask the Alliance to adopt it. The reference implementation is offered for evaluation under its published licenses, with any operational or ownership transition subject to a separate agreement.

The RFC 6962 construction described here is not our invention. Certificate Transparency has run this design in production for a decade, and the contribution is the application to agent incident evidence, not the cryptography.
