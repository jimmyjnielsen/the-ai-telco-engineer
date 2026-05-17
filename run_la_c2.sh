#!/bin/bash
set -e
cd ~/repos/the-ai-telco-engineer
export MODEL_API_KEY=local
# DO NOT set DISABLE_CONSOLIDATION — we want v2 consolidation active for this run.
~/LLM/venv/bin/python3 launch.py tasks/link_adaptation_c2 2>&1 | tee run_la_c2.log
