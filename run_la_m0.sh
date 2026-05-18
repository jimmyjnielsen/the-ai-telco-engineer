#!/bin/bash
set -e
cd ~/repos/the-ai-telco-engineer
export MODEL_API_KEY=$(cat ~/.mistral-key)
source venv/bin/activate
# Consolidation enabled (default)
python launch.py tasks/link_adaptation_m0 2>&1 | tee run_la_m0.log
