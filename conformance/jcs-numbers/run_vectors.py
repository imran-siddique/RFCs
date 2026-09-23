"""Run the vectors against any JCS number serializer, and the admission profile
against any admission check.

    python run_vectors.py jcs-number-vectors.json

Point `serialize` at whatever produces the canonical form of a single number.
The default uses the rfc8785 package if it is installed. Point `admit` at
whatever decides whether a JSON number token is admissible in an evidence
object; the default is the reference check described in the file.
"""
import json, struct, sys

SAFE = 2 ** 53 - 1

def serialize(x):
    import rfc8785
    return rfc8785.dumps(x).decode()

def admit(token):
    """Reference admission check on the binary64 value RFC 8785 serializes, not on the token."""
    v = float(token)
    if v != v or v in (float("inf"), float("-inf")):
        return False
    if v != int(v):
        return True
    return abs(int(v)) <= SAFE

def as_double(hex_be):
    return struct.unpack(">d", int(hex_be, 16).to_bytes(8, "big"))[0]

def attempt(x):
    try:
        return serialize(x), None
    except Exception as exc:
        return None, "%s: %s" % (type(exc).__name__, exc)

path = sys.argv[1] if len(sys.argv) > 1 else "jcs-number-vectors.json"
doc = json.load(open(path))

probe, err = attempt(1.5)
if probe != "1.5":
    sys.exit("serialize() is not working: 1.5 gave %r. Point it at your implementation." % (probe or err))

failed = 0
for v in doc["settled"]:
    got, err = attempt(as_double(v["input"]["ieee754_be_hex"]))
    ok = got == v["expect"]
    failed += not ok
    print("%-5s %-40s expect %-24s got %s" % ("ok" if ok else "FAIL", v["name"], v["expect"], got or err))
print("\n%d of %d settled vectors pass" % (len(doc["settled"]) - failed, len(doc["settled"])))

prof = doc["admission_profile"]
print("\nadmission profile %s (%s):" % (prof["name"], prof["status"]))
afailed = 0
for c in prof["cases"]:
    got = "admit" if admit(c["input"]["token"]) else "reject"
    ok = got == c["expect"]
    afailed += not ok
    print("%-5s %-32s %-28s expect %-6s got %s" % ("ok" if ok else "FAIL", c["name"], c["input"]["token"], c["expect"], got))
print("\n%d of %d admission cases pass" % (len(prof["cases"]) - afailed, len(prof["cases"])))

print("\nobservations, what this serializer does with out-of-range integers:")
for v in doc["observations_on_conformant_serialization"]["cases"]:
    kind = v["input"]["kind"]
    if kind == "integer":
        got, err = attempt(int(v["input"]["decimal"]))
        spec = v.get("expect_per_spec")
        print("  %-46s spec %-24s here %s" % (v["name"], spec or "(see observed)", got or err))
    elif kind == "pair-of-objects":
        a, b = 9007199254740992, 9007199254740993
        ga, ea = attempt(a)
        gb, eb = attempt(b)
        if ga is None or gb is None:
            print("  %-34s refused, so no collision here: %s" % (v["name"], ea or eb))
        else:
            print("  %-34s %d -> %s and %d -> %s : %s" % (
                v["name"], a, ga, b, gb,
                "COLLIDE, one leaf for two objects" if ga == gb else "distinct"))

sys.exit(1 if (failed or afailed) else 0)
