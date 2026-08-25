# JCS number-serialization conformance vectors

Written for the discussion on `OpenSecureAIAlliance/RFCs#18`, covering the areas
RFC 8785 Appendix B does not: the exponent's leading zero, the thresholds at each
end where positional notation gives way to exponential, and the integer domain.

    python run_vectors.py jcs-number-vectors.json

Point `serialize` in the runner at any implementation. It defaults to the
`rfc8785` package if that is installed. Fourteen settled vectors, plus a pending
section that asserts no answer.

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

## The pending section

Five cases where no answer is asserted, because the spec and a shipped reference
implementation disagree and the disagreement is not cosmetic.

RFC 8785 defers number serialization to ECMA-262, which has exactly one number
type and it is a double. So serializing an integer is not a well-defined
operation. It depends on whether the implementation converts to a double first.

Three behaviours were observed for the same input, a field value of
`9007199254740993`:

| implementation | canonical form | outcome |
|---|---|---|
| only-double languages, for example V8 | `9007199254740992` | lands on the neighbouring integer |
| big-integer languages that do not convert, for example Python `int` | `9007199254740993` | exact, and diverges from the above |
| `rfc8785` (Python) 0.1.4 | refused | `IntegerDomainError` at exactly 2\*\*53 |

The first produces a collision: `9007199254740992` and `9007199254740993` are
different values that canonicalize to identical bytes and therefore one leaf hash.
The second produces divergence: two implementations, neither raising, computing
different leaf hashes for the same object. The third refuses and so does neither,
which means the implementation that deviates from the spec is the fail-closed one.

A collision is at least visible to one party holding two objects and one hash.
Divergence is two parties computing different proofs for the same object, each
certain it is right, which is the failure the RFC already names: it passes every
test the implementer writes and fails the first time a second organization writes
its own verifier.

Deciding the integer domain decides all five. Leaving it implicit is not neutral.
