#!/bin/bash
# Watch for LA-F2 to complete, then clean up and launch LA-C2.
# Idempotent: safe to re-run if it dies; will skip already-completed phases.

LOG=~/repos/the-ai-telco-engineer/chain_f2_then_c2.log
exec > >(tee -a "$LOG") 2>&1

echo "[$(date -Iseconds)] chain script started"

# ── 1. Wait for F2 launch.py to exit ──────────────────────────────────
F2_PATTERN="launch.py tasks/link_adaptation_f2"
echo "[$(date -Iseconds)] waiting for F2 process matching: $F2_PATTERN"
while pgrep -f "$F2_PATTERN" > /dev/null 2>&1; do
    sleep 60
done
echo "[$(date -Iseconds)] F2 process exited"

# ── 2. Sanity check that F2 finished cleanly ──────────────────────────
F2_LB=~/repos/the-ai-telco-engineer/tasks/link_adaptation_f2/workspaces/leaderboard.json
if [ ! -f "$F2_LB" ]; then
    echo "[$(date -Iseconds)] WARNING: F2 leaderboard not found — F2 may have died early. Launching C2 anyway."
fi

# ── 3. Clean up orphan workspace containers from F2 ──────────────────
echo "[$(date -Iseconds)] cleaning orphan workspace containers"
docker ps -a --format "{{.Names}}" | grep workspace_ | xargs -r docker rm -f
echo "[$(date -Iseconds)] cleanup done"

# ── 4. Guard against double-launch of C2 ─────────────────────────────
if pgrep -f "launch.py tasks/link_adaptation_c2" > /dev/null 2>&1; then
    echo "[$(date -Iseconds)] WARNING: C2 already running — exiting chain"
    exit 0
fi

# ── 5. Launch C2 via its run script ──────────────────────────────────
echo "[$(date -Iseconds)] launching LA-C2"
cd ~/repos/the-ai-telco-engineer
nohup bash run_la_c2.sh > run_la_c2.nohup.log 2>&1 &
C2_PID=$!
disown
echo "[$(date -Iseconds)] C2 launched (PID $C2_PID)"
sleep 5
pgrep -af "launch.py tasks/link_adaptation_c2"
