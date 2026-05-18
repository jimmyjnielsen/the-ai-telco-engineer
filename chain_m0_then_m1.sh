#!/bin/bash
# Run m0 (with consolidation), then m1 (no consolidation), sequentially.
# Idempotent: each run can be resumed by re-launching its run_la_m*.sh.
LOG=~/repos/the-ai-telco-engineer/chain_m0_then_m1.log
exec > >(tee -a "$LOG") 2>&1
echo "[$(date -Iseconds)] chain starting"
cd ~/repos/the-ai-telco-engineer

# Make sure nothing else is running
if pgrep -f "launch.py tasks/link_adaptation_m" > /dev/null; then
    echo "[$(date -Iseconds)] WARNING: an m0/m1 launch is already running, aborting chain"
    exit 1
fi
docker ps -a --format "{{.Names}}" | grep workspace_ | xargs -r docker rm -f

echo "[$(date -Iseconds)] launching m0 (with consolidation)"
bash run_la_m0.sh
echo "[$(date -Iseconds)] m0 exited"
docker ps -a --format "{{.Names}}" | grep workspace_ | xargs -r docker rm -f

echo "[$(date -Iseconds)] launching m1 (no consolidation)"
bash run_la_m1.sh
echo "[$(date -Iseconds)] m1 exited"
docker ps -a --format "{{.Names}}" | grep workspace_ | xargs -r docker rm -f

echo "[$(date -Iseconds)] chain complete"
