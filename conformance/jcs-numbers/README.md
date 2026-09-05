# JCS number-serialization conformance vectors

Written for the discussion on `OpenSecureAIAlliance/RFCs#18`, covering the areas
RFC 8785 Appendix B does not: the exponent's leading zero, the thresholds at each
end where positional notation gives way to exponential, and the integer domain.

    python run_vectors.py jcs-number-vectors.json

Point `serialize` in the runner at any implementation. It defaults to the
`rfc8785` package if that is installed. Two suites: fourteen settled
serialization vectors, and an admission profile of twenty cases that says
which JSON numbers an evidence object may carry at all.

## Why the expected values can be trusted

Three independent oracles agree on all fourteen settled vectors:

1. `rfc8785` (Python) 0.1.4
2. V8 22.22.2, which RFC 8785 section 3.2.2.3 names as a reference implementation
3. A formatter written from ECMA-262 section 7.1.12.1, taking only the
   shortest-round-trip digits from the host and applying the format rules directly

All three reproduce the single Appendix B entry available: IEEE 754 hex
`4430000000000000` serializes as `295147905179352830000`.

## Why the vectors are believed to measure something

Eight plausible-but-wrong serializers were run against the whole set, and every
vector fails at least one of them. A vector that no wrong implementation fails is
not evidence and was not kept.

    host-language-repr          fails 8 of 14
    exact-binary-expansion      fails 12 of 14
    precision-15-significant    fails 10 of 14
    exponent-without-plus       fails 11 of 14
    subnormal-flushed-to-zero   fails  9 of 14
    exponent-padded-to-two      fails  8 of 14
    negative-zero-passthrough   fails  8 of 14
    json-dumps-default          fails  8 of 14

Each vector carries the list of which ones it catches.

## Inputs are IEEE 754 hex

Following Appendix B's own convention. This is not a style preference. A float
written as a JSON literal has already been through a parser before any
implementation under test sees it, so a vector specified that way is testing the
reading parser as much as the serializer.

## Two suites, and why they are separate

A serialization vector says what bytes RFC 8785 produces for a value. An
admission case says whether an evidence profile accepts that value at all. Six
of the fourteen settled vectors, `1e16`, `1e20`, `9.999999999999999e20`, `1e21`,
`1e100` and the maximum double, serialize correctly and are integer-valued
doubles above the safe range, so under the admission rule below they are not
admissible. A serializer test passing is not evidence that a profile admits the
input. Keeping the two apart is what makes both checkable.

## The admission profile

Proposed on `OpenSecureAIAlliance/RFCs#18`, not adopted by the working group.
The rule:

> Every integer-valued JSON number in an evidence object, whatever its spelling
> or the host's numeric type, lies within -9007199254740991 to 9007199254740991.
> A verifier that finds one outside that range rejects the object before
> canonicalizing it. Numbers that are not integer-valued are outside this rule.

The bound is 2\*\*53 - 1 rather than 2\*\*53 because a verifier whose only number
type is the double sees the parsed value, not the instance: it reads
`9007199254740993` as `9007199254740992`, and under a bound of 2\*\*53 would
admit the one value the range exists to exclude. Spelling does not decide
admission, value does: `9007199254740992.0` and `9.007199254740992e15` are the
same value as `9007199254740992` and are rejected with it, and their negative
counterparts likewise. Since every double of magnitude 2\*\*53 or more is
integer-valued, the rule admits no JSON number of that magnitude.

The runner's reference check parses each token exactly, as a decimal rather than
a double, so the expectation is stated on the value the producer wrote. An
implementation that parses to a double first still gets every case right, because
each rejected value stays rejected after rounding.

## What shipped implementations do with out-of-range integers

Kept as observations, no longer as open questions, because the profile above is
what settles them.

Appendix B note 2 settles what the algorithm does: even where an integer like
`2**68` could be regarded as having extended precision, the serialization does not
take that into consideration. It is a double. `2**68` itself is a power of two
and exactly representable; what the algorithm changes is the spelling, since the
shortest decimal that round-trips to that double, `295147905179352830000`, read
back as an integer is 4144 short. That is a reason to carry such a value as a
string, per Appendix D, not a floating-point loss.

Three behaviours were observed for the same input, a field value of
`9007199254740993`. Only the first is conformant:

| implementation | canonical form | outcome |
|---|---|---|
| **conformant**: converts to a double, for example V8 | `9007199254740992` | lands on 2\*\*53, just outside the safe range |
| non-conformant: a big-integer language that skips the conversion, for example Python `int` | `9007199254740993` | exact, and diverges silently from the above |
| non-conformant: `rfc8785` (Python) 0.1.4 | refused | `IntegerDomainError` at exactly 2\*\*53 |

The first produces a collision: `9007199254740992` and `9007199254740993` are
different values that canonicalize to identical bytes and therefore one leaf hash,
`3f9d3e6edd300dd569ec99916ec6270597c7b07cea1602f4ce5216b01bac65ff` for
`{"agent_id":"a","seq":N}` under RFC 6962 leaf hashing, reproduced in V8 22.22.2
and Node 24. The second produces divergence: two implementations, neither
raising, computing different leaf hashes for the same object. The third refuses
and so does neither, which means the implementation that deviates from the spec
is the fail-closed one.

A collision is at least visible to one party holding two objects and one hash.
Divergence is two parties computing different proofs for the same object, each
certain it is right, which is the failure the RFC already names: it passes every
test the implementer writes and fails the first time a second organization writes
its own verifier.

Conforming exactly is not sufficient here, which is why the range is stated as a
constraint on the evidence object rather than left to a SHOULD aimed at producers.

The two-suite split and two corrections to the earlier text, that `2**68` is
exactly representable and that `9007199254740992` sits outside the safe range,
came from review on `OpenSecureAIAlliance/RFCs#18`.
