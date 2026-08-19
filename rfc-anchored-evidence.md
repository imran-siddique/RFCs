# Anchored Evidence for SAFE

A proposed addition to the Shared AI Findings Exchange: external anchoring of preserved incident evidence, and an offer to contribute a working reference registry to the Open Secure AI Alliance.

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

The published record contains no evidence. It contains a hash, a timestamp, and a count.

# Why this fits SAFE specifically

Three features of the current draft make anchoring more useful here than in a general assurance framework.

**The timelines create a window.** SAFE gives four business days for an initial confidential report, thirty for a preliminary factual report, and ninety for remediation status. Throughout that window the evidence sits with the member, and the questions the review will ask become progressively clearer. Anchoring at the time of the incident fixes the evidence before the member can know what the review will focus on. The value comes precisely from anchoring early, which is the moment a member has the least idea what will matter.

**Confidentiality is preserved, not traded away.** SAFE's disclosure model moves from confidential rapid alert to de-identified advisory to public report, and members may face legal or investigative constraints at every stage. A hash publishes nothing. A member can anchor evidence on day zero of an incident that they are not permitted to describe for ninety days, or ever. The confidentiality model and the verifiability requirement do not have to be traded against each other, which is usually the reason frameworks drop verifiability.

**Near misses become cheap to record.** The Reporting Compact requires reporting near misses, not only events producing confirmed harm. Near misses are exactly the class of event where the incentive to preserve evidence is weakest, because nothing went wrong and the work has no visible payoff. Anchoring costs a hash. A member can anchor near-miss evidence as a matter of routine and decide later whether it is reportable.

# The mechanism

The construction below follows RFC 6962, the Certificate Transparency Merkle tree. It is specified in full at `docs/anchor-format.md` in the reference implementation, and a conforming verifier can be written from that document alone.

**Leaf.** The unit of anchoring is the complete signed evidence object, signature included. Anchoring binds the signed artifact rather than a pre-signature payload, so a change to either the body or the signature breaks the anchor.

```
leaf = SHA-256(0x00 || canonical_bytes)
```

**Tree.** Interior nodes are `SHA-256(0x01 || left || right)` over 32-byte child hashes. Construction proceeds level by level over the ordered leaves. When a level has an odd number of nodes the final node is promoted unchanged rather than duplicated, which yields the same tree as the RFC 6962 recursive split at the largest power of two. The `0x00` and `0x01` prefixes are domain separation and prevent an interior node being presented as a leaf. An empty batch is invalid and must be rejected.

**Entry.** Each anchored batch is one line of newline-delimited JSON in a dated file, with five fields:

| Field | Type | Meaning |
| ----- | ---- | ------- |
| `ts` | string | Anchoring time, ISO-8601 UTC |
| `merkle_root` | string | `sha256:` followed by 64 lowercase hex characters |
| `leaf_count` | integer | Number of leaves in the batch, at least 1 |
| `producer` | string | Party that produced and submitted the batch |
| `batch_id` | string | Producer-scoped unique identifier |

Entries are append-only. Files are never rewritten. In the reference implementation the version-control history is the tamper-evidence layer, because rewriting a published entry diverges the commit hashes that auditors and mirrors have already observed. A JSON Schema is enforced in CI on every line of every registry file.

**Verification.** A reviewer needs three things: the evidence item, the inclusion proof, and the registry entry for the batch. The reference verifier is a single standard-library file, written that way so it can be audited rather than trusted.

# One specification detail worth stating in the open

A record is usually canonicalized twice for different purposes, and the two canonicalizations are not interchangeable even when they often agree.

In the reference implementation the signature pre-image uses RFC 8785 JCS, while the anchor leaf uses sorted-key ASCII JSON. Those two agree for records whose keys and strings are ASCII and whose numbers are integers, which describes most records and is exactly why the divergence is dangerous. They part company in at least three places. RFC 8785 emits non-ASCII characters where the anchor format escapes them. RFC 8785 applies ECMAScript number serialization where the anchor format excludes non-integer numbers entirely, because cross-language float serialization is not canonical. RFC 8785 orders object keys by UTF-16 code unit where the anchor format orders by Unicode code point.

A verifier must use the canonicalization declared for the context it is checking. Reusing one for the other is non-conforming even when a particular record happens to produce identical bytes.

Any evidence framework SAFE adopts will hit this. It is raised here because it is the class of defect that passes every test written by the implementer and fails the first time a second organization writes its own verifier, which is the moment independent verification was supposed to start working.

# What anchoring proves, and what it does not

Stating the limits precisely matters more than the mechanism, because an overstated assurance property is worse than none.

**Inclusion proves that the exact bytes provided were recorded at the entry's timestamp and cannot be quietly un-recorded.** That is the whole claim.

It does not validate a signature against a producer key. That is a separate step against the producer's published keys.

It does not establish that the anchored evidence is true. A member can anchor an inaccurate record, and the anchor will faithfully prove they recorded that inaccuracy at that time. What it removes is the ability to revise it later without detection.

**It does not establish completeness.** This is the most important limit and it is the one raised in issue #11 by @bobleer. Anchoring what you have does not prove you anchored everything you had. A member can begin anchoring after the interesting action and present a continuous, correctly proven chain of everything after it. Anchoring is a necessary component of a completeness argument and is not one by itself. It becomes one only when run boundaries are themselves anchored, so that a missing interval is visible as a gap rather than as an absence.

It does not authenticate the recording environment. A record anchored from a runtime the member modified is an unalterable record of whatever that runtime chose to write. Anchoring narrows the window during which evidence can be shaped, from the full ninety-day review period down to the moment of recording. It does not close it.

# Proposed additions to the draft

**Evidence Preservation.** Add to the required properties of preserved evidence, alongside the existing list of contents:

> For each preserved evidence item, members should record its anchoring status: `anchored`, where a digest of the item was published to an external append-only record at a stated time and an inclusion proof is retained and provided alongside the item; `unanchored`, where the item was preserved but its existence at a given time cannot be independently established; or `unavailable`, where anchoring status cannot be determined.

The requirement is that the status is stated, not that it is `anchored`. Most members will not anchor initially, and mandating it would either exclude them or produce false declarations. An unanchored item remains usable evidence provided it is labelled as such. A reviewer weighing a member's account against a third party's needs to know which parts of that account are independently fixed in time and which rest on the member's word, and today the framework gives them no way to tell.

**Review Framework.** The Monitoring layer asks whether operators could detect and interrupt unexpected behavior in real time. Add whether the evidence supporting that determination was anchored at the time of the events or assembled during the review. The two produce very different confidence in the same answer.

**From Lessons to Controls.** Recommendations must specify a reproducible verification method and the evidence to retain. Where a recommendation's verification depends on records produced by the party being verified, that recommendation should state whether those records are anchored. A verification method whose inputs the verified party can revise is not reproducible in the sense the section intends.

# Governance: why this belongs to the alliance and not to us

A registry operated by the party that issues records into it is not an independent registry. This is the central weakness of the reference implementation and there is no version of the argument in which we resolve it ourselves.

The implementation's own roadmap names three gaps, all of them structural rather than technical. Production claim volume from producers other than the reference gateway, where the current count is one. An independent mirror operated by someone else, because a mirror we run checks almost nothing and the value comes entirely from an operator with no incentive to cover for us. Maintainers from outside the originating company, for the same reason.

Each of those is a thing a consortium is for and a thing a vendor cannot supply. That is the reason this comes to the alliance as a contribution rather than as a product.

We therefore offer to contribute the registry to the Open Secure AI Alliance: the anchor format specification, the reference tooling, the schema and CI validation, the mirroring documentation and checks, and the operational pipeline. The code is Apache-2.0 and the registry data is CC BY 4.0. We would prefer the alliance or its members to operate it, with mirrors held by parties who have no relationship with us, and we do not require that operation stay with us in any form.

If the working group would rather specify the requirement and have members implement it independently, that is a good outcome too. The requirement is what matters. The implementation is offered because a working one shortens the argument, not because it needs to be the one adopted.

# Status of the reference implementation

Stated plainly, because the alternative invites a correction later.

The anchor format is specified and stable enough to implement against. The reference verifier is published and is standard-library only. Anchoring runs on a schedule and verifies producer signatures before anchoring anything. Mirroring is documented and checked. Schema validation runs in CI on every registry line.

The registry currently holds one real entry, from one producer, and there is no mirror we do not operate. The machinery is live and the format is real. The volume is not there. Nothing above should be read as operating at scale, and a long gap between entries reflects claim volume rather than a stalled pipeline.

The registry's own history is witnessed by version control and mirrors, which is still a record we host. Anchoring the registry into an external transparency log, so its history is witnessed by something outside it, is designed but not built.

The repository is currently private and would be made public as part of this contribution.

# Open questions for the working group

**Anchoring unit.** Should members anchor individual evidence items, run boundaries, or the incident report itself? Item-level anchoring gives the finest verification granularity. Run-boundary anchoring is what makes gap detection possible. These are complementary and the working group may want both, but the requirement should say which.

**Retention against append-only.** An anchor is permanent by construction. Preserved evidence is not, and members have deletion obligations under data protection law and under their own retention policies. A digest of deleted evidence persisting in a public registry is probably acceptable, since a hash of destroyed material reveals nothing and cannot be reversed. It should be examined rather than assumed, because it interacts directly with member sovereignty and the answer may differ across jurisdictions.

**Producer identity against de-identification.** A registry entry names its producer. SAFE's disclosure model de-identifies at the advisory stage. If a member anchors evidence during an incident and the advisory is later de-identified, the anchor timestamps may correlate with the advisory and partly undo that. Pseudonymous or rotating producer identifiers would address it at some cost to accountability, and the working group should decide where that trades out.

**Anchoring by the reporting member or by SAFE.** A member could anchor to a public registry directly, or submit digests to SAFE which anchors on their behalf. The first requires no trust in SAFE. The second is easier for members and gives SAFE a role in establishing timing, at the cost of making SAFE a party to the record.

# Relationship to existing discussion

This proposal builds on issue #11 and is intended to complement rather than replace the discussion there.

Issue #11 established that Evidence Preservation specifies contents without integrity properties, and its thread converged on three determinations a reviewer should be able to make: that records were not altered, that the record set is continuous or its gaps declared and bounded, and that the point at which recording began was fixed independently of the operating member. External anchoring was named there as a requirement, by @bobleer, without a mechanism attached. This proposal supplies one and takes no position on the other two.

Issue #14 proposes a per-item provenance grade. Anchoring status is orthogonal to that grade and complements it, since a provenance claim is more useful when the time at which it was made is externally fixed.

Issue #6 proposes signed, offline-recomputable tool-trust verdicts. Those verdicts are evidence and can be anchored, which addresses when a verdict was issued rather than only who issued it.

Issue #4 concerns verification methods that fail open. An anchored record of a verification result does not stop the method failing open, and the two should not be confused.

# Disclosure

Submitted by Imran Siddique, Opaque Systems. Opaque Systems maintains TRACE, an open specification for verifiable agent evidence records, and the reference registry described here. TRACE is not an adopted standard at any body and this proposal does not ask the alliance to adopt it. The registry is offered as a contribution, including operation and maintenance passing to others, because an accountability layer operated by its own largest producer is the specific thing that does not work.

The RFC 6962 construction described here is not our invention. Certificate Transparency has run this design in production for a decade, and the contribution is the application to agent incident evidence, not the cryptography.
