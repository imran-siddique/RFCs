"""Run the vectors against any JCS number serializer.

    python run_vectors.py jcs-number-vectors.json

Point `serialize` at whatever produces the canonical form of a single number.
The default uses the rfc8785 package if it is installed.
"""
import json, struct, sys

def serialize(x):
    import rfc8785
    return rfc8785.dumps(x).decode()

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

print("\npending, no answer asserted:")
for v in doc["pending_working_group"]:
    kind = v["input"]["kind"]
    if kind == "integer":
        got, err = attempt(int(v["input"]["decimal"]))
        spec = v.get("expect_per_spec")
        if spec:
            print("  %-46s spec %-24s here %s" % (v["name"], spec, got or err))
        else:
            print("  %-46s here %s" % (v["name"], got or err))
            for o in v.get("observed", []):
                print("      %-72s %s" % (o["implementation"], o["canonical"]))
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
