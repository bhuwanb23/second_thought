#!/usr/bin/env bash
# scripts/v5_two_jars.sh — V5 over a real socket, with two real cookie jars.
#
# Everything here is done with `curl` and `-c/-b` jars, because that is what the
# gate asks for: two separate sessions, not one process pretending to be two.
#
#   bash scripts/v5_two_jars.sh
#
# Exit code 0 means all six checks passed. The server is always stopped.

set -u
cd "$(dirname "$0")/.." || exit 1

PORT=${PORT:-8123}
PIDFILE=/tmp/st_v5_$$.pid
LOG=/tmp/st_v5_$$.log
JAR_A=/tmp/st_jar_a_$$.txt
JAR_B=/tmp/st_jar_b_$$.txt
JAR_C=/tmp/st_jar_c_$$.txt
BASE="http://127.0.0.1:${PORT}"
PASS=0
FAIL=0
TEST_SECRET="v5-known-secret-value-$$"   # so /healthz can be grepped for a real secret

stop_server() {
  if [ -f "$PIDFILE" ]; then
    local pid; pid=$(cat "$PIDFILE" 2>/dev/null)
    [ -n "${pid:-}" ] && kill "$pid" 2>/dev/null
    for _ in 1 2 3 4 5 6 7 8 9 10; do kill -0 "$pid" 2>/dev/null || break; sleep 0.2; done
    kill -9 "$pid" 2>/dev/null
    rm -f "$PIDFILE"
  fi
}
trap 'stop_server; rm -f "$JAR_A" "$JAR_B" "$JAR_C" "$LOG" /tmp/st_body_$$' EXIT

start_server() {
  PORT="$PORT" APPROVAL_SECRET="$TEST_SECRET" python3 scripts/serve.py --port "$PORT" --pidfile "$PIDFILE" >"$LOG" 2>&1 &
  for _ in $(seq 1 50); do
    if curl -fsS -m 1 "${BASE}/healthz" >/dev/null 2>&1; then return 0; fi
    sleep 0.2
  done
  echo "server did not start; log:"; cat "$LOG"; return 1
}

check() {  # check <label> <expected> <actual>
  if [ "$2" = "$3" ]; then printf '  \033[32m✓\033[0m %-58s %s\n' "$1" "$3"; PASS=$((PASS+1))
  else printf '  \033[31m✗\033[0m %-58s got %s, want %s\n' "$1" "$3" "$2"; FAIL=$((FAIL+1)); fi
}

contains() {  # contains <label> <needle> <haystack>
  case "$3" in
    *"$2"*) printf '  \033[32m✓\033[0m %-58s found\n' "$1"; PASS=$((PASS+1));;
    *) printf '  \033[31m✗\033[0m %-58s missing: %s\n' "$1" "$2"; FAIL=$((FAIL+1));;
  esac
}

code() { curl -s -o /tmp/st_body_$$ -w '%{http_code}' "$@"; }

echo "── starting server on ${PORT} ─────────────────────────────────────────"
start_server || exit 1

echo
echo "── 1. two cookie jars ────────────────────────────────────────────────"
code -c "$JAR_A" -b "$JAR_A" "${BASE}/api/session" >/dev/null
code -c "$JAR_B" -b "$JAR_B" "${BASE}/api/session" >/dev/null
SID_A=$(grep -o 'st_sid.*' "$JAR_A" | awk '{print $NF}' | tail -1 | cut -d. -f1)
SID_B=$(grep -o 'st_sid.*' "$JAR_B" | awk '{print $NF}' | tail -1 | cut -d. -f1)
if [ "$SID_A" != "$SID_B" ] && [ -n "$SID_A" ]; then
  printf '  \033[32m✓\033[0m %-58s %s… vs %s…\n' "two jars, two sessions" "${SID_A:0:8}" "${SID_B:0:8}"
  PASS=$((PASS+1))
else
  printf '  \033[31m✗\033[0m %s\n' "the jars hold the same session"; FAIL=$((FAIL+1))
fi

echo
echo "── 2. A saves a profile and executes; B must still see the default ───"
BEFORE=$(curl -s -b "$JAR_B" "${BASE}/api/quote?persona=maya" | python3 -c 'import sys,json;print(json.load(sys.stdin)["verdict"])')
curl -s -b "$JAR_A" -c "$JAR_A" -X POST -H 'Content-Type: application/json' \
  -d '{"profile":{"opening_balance":1000000,"paydays":[{"due":"2026-11-04","amount_minor":9000000}],"obligations":[{"label":"rent","due":"2026-11-09","amount_minor":4000000,"essential":true}]}}' \
  "${BASE}/api/profile" >/dev/null
PLAN=$(curl -s -b "$JAR_A" -c "$JAR_A" -X POST -H 'Content-Type: application/json' \
  -d '{"persona":"me"}' "${BASE}/api/plan")
TOOL=$(echo "$PLAN" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("tool",""))')
TOKEN=$(echo "$PLAN" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("token",""))')
ARGS=$(echo "$PLAN" | python3 -c 'import sys,json;print(json.dumps(json.load(sys.stdin).get("proposal",{})))')
STATE=$(curl -s -b "$JAR_A" -X POST -H 'Content-Type: application/json' \
  -d "{\"tool\":\"$TOOL\",\"args\":$ARGS,\"token\":\"$TOKEN\"}" "${BASE}/api/execute" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin).get("state",""))')
AFTER=$(curl -s -b "$JAR_B" "${BASE}/api/quote?persona=maya")
AFTER_V=$(echo "$AFTER" | python3 -c 'import sys,json;print(json.load(sys.stdin)["verdict"])')
AFTER_P=$(echo "$AFTER" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("profile"))')
case "$STATE" in
  RESERVED|AUTHORISED) printf '  \033[32m✓\033[0m %-58s %s\n' "A's plan executed" "$STATE"; PASS=$((PASS+1));;
  *) printf '  \033[31m✗\033[0m %-58s %s\n' "A's plan executed" "'${STATE:-none}'"; FAIL=$((FAIL+1));;
esac
check "B's verdict unchanged" "$BEFORE" "$AFTER_V"
check "B is reading the persona default" "persona-default" "$AFTER_P"

echo
echo "── 3. 31 model calls in one session ──────────────────────────────────"
# a third jar, so the count starts at zero: session A already spent one call on its profile
code -c "$JAR_C" -b "$JAR_C" "${BASE}/api/session" >/dev/null
for i in $(seq 1 30); do
  C=$(code -b "$JAR_C" -X POST -H 'Content-Type: application/json' \
        -d '{"text":"rent 1450 on the 28th"}' "${BASE}/api/extract")
  [ "$C" = "200" ] || { printf '  throttle fired early at call %s (%s)\n' "$i" "$C"; break; }
done
check "call 30 still succeeds" "200" "$C"
C31=$(code -b "$JAR_C" -X POST -H 'Content-Type: application/json' \
  -d '{"text":"one more"}' "${BASE}/api/extract")
check "call 31 is throttled" "429" "$C31"
C_B=$(code -b "$JAR_B" -X POST -H 'Content-Type: application/json' \
  -d '{"text":"rent 1450 on the 28th"}' "${BASE}/api/extract")
check "session B is unaffected" "200" "$C_B"

echo
echo "── 4. /healthz logged out ────────────────────────────────────────────"
HEALTH=$(curl -s "${BASE}/healthz")
check "logged out, still answers" "200" "$(code "${BASE}/healthz")"
contains "/healthz has status booleans" '"status": "ok"' "$HEALTH"
for leak in "$TEST_SECRET" PAYPAL_CLIENT_SECRET llm-key-value diag-token-value; do
  case "$HEALTH" in
    *"$leak"*) printf '  \033[31m✗\033[0m leaked %s\n' "$leak"; FAIL=$((FAIL+1));;
    *) printf '  \033[32m✓\033[0m %-58s absent\n' "no ${leak:0:24}… in /healthz"; PASS=$((PASS+1));;
  esac
done

echo
echo "── 5. money tools without a valid approval ───────────────────────────"
for T in create_scheduled_invoice authorize_payment; do
  check "$T is refused outright" "400" \
    "$(code -b "$JAR_A" -X POST -H 'Content-Type: application/json' -d "{\"tool\":\"$T\"}" "${BASE}/api/execute")"
done
check "real tool with no token" "403" \
  "$(code -b "$JAR_A" -X POST -H 'Content-Type: application/json' -d "{\"tool\":\"$TOOL\",\"args\":$ARGS}" "${BASE}/api/execute")"
check "A's token replayed in B" "403" \
  "$(code -b "$JAR_B" -X POST -H 'Content-Type: application/json' -d "{\"tool\":\"$TOOL\",\"args\":$ARGS,\"token\":\"$TOKEN\"}" "${BASE}/api/execute")"
TAMPERED=$(python3 -c "import json,sys;a=json.loads(sys.argv[1]);a['amount_minor']=a.get('amount_minor',0)+50000;print(json.dumps(a))" "$ARGS")
check "A's token with an altered amount" "403" \
  "$(code -b "$JAR_A" -X POST -H 'Content-Type: application/json' -d "{\"tool\":\"$TOOL\",\"args\":$TAMPERED,\"token\":\"$TOKEN\"}" "${BASE}/api/execute")"

echo
echo "── 6. restart the process ────────────────────────────────────────────"
OLD_BOOT=$(curl -s -b "$JAR_A" "${BASE}/api/session" | python3 -c 'import sys,json;print(json.load(sys.stdin)["boot"])')
stop_server
start_server || exit 1
RESUMED=$(curl -s -b "$JAR_A" -c "$JAR_A" -w '\n%{http_code}' "${BASE}/api/session")
CODE=$(echo "$RESUMED" | tail -1)
HAS_PROFILE=$(echo "$RESUMED" | head -1 | python3 -c 'import sys,json;print(json.load(sys.stdin)["session"]["has_profile"])')
NEW_BOOT=$(echo "$RESUMED" | head -1 | python3 -c 'import sys,json;print(json.load(sys.stdin)["boot"])')
check "old cookie does not crash the new process" "200" "$CODE"
check "the old profile is gone" "False" "$HAS_PROFILE"
if [ "$OLD_BOOT" != "$NEW_BOOT" ]; then
  printf '  \033[32m✓\033[0m %-58s %s → %s\n' "the boot id changed" "$OLD_BOOT" "$NEW_BOOT"; PASS=$((PASS+1))
else
  printf '  \033[31m✗\033[0m %s\n' "the boot id did not change — stale state may be served"; FAIL=$((FAIL+1))
fi
check "personas still answer after restart" "DEFER" \
  "$(curl -s -b "$JAR_A" "${BASE}/api/quote?persona=maya" | python3 -c 'import sys,json;print(json.load(sys.stdin)["verdict"])')"

echo
echo "══════════════════════════════════════════════════════════════════════"
printf '  %s passed, %s failed\n' "$PASS" "$FAIL"
echo "══════════════════════════════════════════════════════════════════════"
[ "$FAIL" -eq 0 ] || { echo "server log:"; tail -20 "$LOG"; }
exit $([ "$FAIL" -eq 0 ] && echo 0 || echo 1)
