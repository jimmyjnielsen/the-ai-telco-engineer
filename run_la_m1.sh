#!/bin/bash
set -e
cd ~/repos/the-ai-telco-engineer
export MODEL_API_KEY=$(cat ~/.mistral-key)
export DISABLE_CONSOLIDATION=1
source venv/bin/activate
python launch.py tasks/link_adaptation_m1 2>&1 | tee run_la_m1.log
