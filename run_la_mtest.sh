#!/bin/bash
set -e
cd ~/repos/the-ai-telco-engineer
export MODEL_API_KEY=$(cat ~/.mistral-key)
source venv/bin/activate
python launch.py tasks/link_adaptation_mtest 2>&1 | tee run_la_mtest.log
