#!/usr/bin/env bash
# PRECILLA preflight -- everything free, in one command.
#
# Runs the whole no-cost half of the pipeline and prints ONE compact report
# block at the end. Copy that block back to Claude; it is ~40 lines and tells
# him whether to spend anything.
#
#   ./preflight.sh context/*.md
#
# Nothing here contacts a paid API. The last step is a DRY RUN.

set -uo pipefail

DOCS=("$@")
if [ ${#DOCS[@]} -eq 0 ]; then
  echo "usage: ./preflight.sh context/*.md" >&2
  exit 2
fi

: "${PRECILLA_MAILTO:=}"
if [ -z "$PRECILLA_MAILTO" ]; then
  echo "note: PRECILLA_MAILTO unset -- OpenAlex will throttle you harder." >&2
  echo "      export PRECILLA_MAILTO='you@example.com'" >&2
fi

PY=${PYTHON:-python3}
OUT=preflight_report.txt
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

j() { $PY -c "import json,sys;d=json.load(sys.stdin);print($1)" 2>/dev/null; }

echo "=== 0. offline batteries ==========================================="
for t in test_offline test_check test_derive; do
  if $PY "tests/$t.py" >"$TMP/$t.log" 2>&1; then
    echo "  $t: PASS"
  else
    echo "  $t: FAIL  (see $TMP/$t.log)"; tail -5 "$TMP/$t.log"
  fi
done

echo
echo "=== 1. can we reach the bibliographic providers? ==================="
$PY -m precilla cite doctor >"$TMP/doctor.json" 2>"$TMP/doctor.err"
DOCTOR=$(j 'd["verdict"]' <"$TMP/doctor.json")
echo "  $DOCTOR"
$PY - "$TMP/doctor.json" <<'EOF'
import json,sys
d=json.load(open(sys.argv[1]))
for c in d["checks"]:
    print("    %-10s ok=%-5s %sms  %s" % (
        c["provider"], c.get("ok"), c.get("latency_ms","?"),
        c.get("error") or ("parsed=%s" % c.get("parser_sane"))))
EOF

echo
echo "=== 2. calibrate the citation instrument (positive control) ========"
$PY -m precilla cite calibrate --verbose --promote \
    --report calibration_report.json >"$TMP/cal.json" 2>"$TMP/cal.err"
CAL=$(j 'd["verdict"]' <"$TMP/cal.json")
echo "  verdict: $CAL"
$PY - "$TMP/cal.json" <<'EOF'
import json,sys
d=json.load(open(sys.argv[1]))
for k,v in (d.get("by_class") or {}).items():
    print("    %-9s %d/%d" % (k, v["pass"], v["n"]))
print("    note:", (d.get("note") or "")[:150])
bad=[r for r in d.get("rows",[]) if not r.get("pass")]
for r in bad[:10]:
    print("    ! %-9s %-24s got=%-12s %s" % (
        r["class"], r["cid"], r["got"], (r.get("reason") or "")[:60]))
EOF

echo
echo "=== 3. resolve the real citations =================================="
$PY -m precilla cite verify "${DOCS[@]}" --bibtex --log \
    >bib.json 2>"$TMP/ver.err"
$PY - bib.json <<'EOF'
import json,sys
d=json.load(open(sys.argv[1]))
if d.get("refused"):
    print("  REFUSED:", d.get("reason")); raise SystemExit
print("  n=%d  summary=%s" % (d.get("n",0), d.get("summary")))
for r in d.get("results",[]):
    if r["status"] not in ("VERIFIED",):
        print("    %-22s %-20s %s" % (
            (r.get("cid") or "")[:22], r["status"], (r.get("reason") or "")[:56]))
EOF

echo
echo "=== 4. confirm the model slugs ====================================="
# NOTE: an earlier version piped into `$PY - <<'EOF'`, where the heredoc IS
# stdin -- python consumed it as the program text and the piped JSON never
# arrived, while a bare `except: raise SystemExit` hid the failure. Read the
# file instead of the pipe.
cat > "$TMP/slugs.py" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
ms = d.get("models", [])
if not ms:
    print("    (none matched -- or %s)" % (d.get("error") or "empty result"))
for m in ms[:8]:
    print("    %-44s in=%-8s out=%s" % (m["id"][:44], m["usd_per_m_in"],
                                        m["usd_per_m_out"]))
PYEOF
for f in glm deepseek kimi; do
  echo "  --filter $f"
  $PY -m precilla derive models --filter "$f" >"$TMP/m.json" 2>"$TMP/m.err" \
    && $PY "$TMP/slugs.py" "$TMP/m.json" \
    || echo "    (failed: $(head -1 "$TMP/m.err"))"
done

echo "=== 5. dry run: what the first paid call would cost ================"
$PY -m precilla derive lead --docs "${DOCS[@]}" --bib bib.json \
    --out draft.md --dry-run >"$TMP/dry.json" 2>"$TMP/dry.err"
$PY - "$TMP/dry.json" <<'EOF'
import json,sys
try: d=json.load(open(sys.argv[1]))
except Exception:
    print("    (dry run failed -- see stderr)"); raise SystemExit
print("    model          :", d.get("model"))
print("    input tokens   :", d.get("input_tokens_est"))
print("    projected cost : $%s" % d.get("projected_usd"))
print("    spent so far   : $%s over %s calls" % (
    d.get("spent_so_far_usd"), d.get("calls_so_far")))
EOF

{
  echo "PRECILLA PREFLIGHT $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "doctor    : $DOCTOR"
  echo "calibrate : $CAL"
  $PY - "$TMP/cal.json" bib.json "$TMP/dry.json" <<'EOF'
import json,sys
try:
    c=json.load(open(sys.argv[1]))
    print("by_class  :", {k:"%d/%d"%(v["pass"],v["n"]) for k,v in (c.get("by_class") or {}).items()})
except Exception: print("by_class  : unavailable")
try:
    b=json.load(open(sys.argv[2])); print("cite      :", b.get("summary"))
except Exception: print("cite      : unavailable")
try:
    d=json.load(open(sys.argv[3]))
    print("dryrun    : %s tok -> $%s (%s)" % (
        d.get("input_tokens_est"), d.get("projected_usd"), d.get("model")))
except Exception: print("dryrun    : unavailable")
EOF
} | tee "$OUT"

echo
echo "-------------------------------------------------------------------"
echo "Wrote $OUT, bib.json and calibration_report.json."
echo "Paste the block above (it is ~6 lines) back to Claude."
echo "NOTHING has been charged. The first paid call is:"
echo "  python3 -m precilla derive lead --docs ${DOCS[*]} --bib bib.json --out draft.md"
