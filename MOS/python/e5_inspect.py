"""One-off: print the recorded sub-claims and pushes for a chosen question."""
import json, sys
import console
console.setup()

want = sys.argv[1] if len(sys.argv) > 1 else "Q-ikeda"
for line in open("e5_elicitations.jsonl", encoding="utf-8"):
    rec = json.loads(line)
    if "pairs" not in rec or rec["qid"] != want:
        continue
    print("=" * 76)
    print(f"{rec['qid']}  repeat {rec['repeat']}")
    for p in rec["pairs"]:
        print(f"  {p['u']:8s}({p['push_u']:+.2f})  {p['v']:8s}({p['push_v']:+.2f})  "
              f"eta={p['push_v'] - p['push_u']:+.2f}  conf={p['confidence']:.2f}")
        print(f"      claim: {p['sub_claim']}")
