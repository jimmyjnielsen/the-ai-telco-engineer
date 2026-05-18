#!/bin/bash
# Wait for chain_m0_then_m1.sh to finish, then resume mtest (which is at gen 7 of 10).
LOG=~/repos/the-ai-telco-engineer/finish_mtest_after_chain.log
exec >> "$LOG" 2>&1
echo "[$(date -Iseconds)] watcher started; waiting for chain_m0_then_m1.sh to finish"

while pgrep -f "chain_m0_then_m1|launch.py tasks/link_adaptation_m[01]" > /dev/null; do
    sleep 60
done
echo "[$(date -Iseconds)] chain finished; cleaning Docker containers"
docker ps -a --format "{{.Names}}" | grep "^workspace_" | xargs -r docker rm -f

echo "[$(date -Iseconds)] launching mtest to finish gens 7-9"
cd ~/repos/the-ai-telco-engineer
bash run_la_mtest.sh
echo "[$(date -Iseconds)] mtest done"
