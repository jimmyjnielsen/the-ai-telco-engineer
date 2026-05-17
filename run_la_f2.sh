#!/bin/bash
set -e
# Load ANTHROPIC_API_KEY from ~/.bashrc (non-interactive guard there blocks plain source)
eval "$(grep "^export ANTHROPIC_API_KEY" ~/.bashrc)"
cd ~/repos/the-ai-telco-engineer
export MODEL_API_KEY=local
export DISABLE_CONSOLIDATION=1
~/LLM/venv/bin/python3 launch.py tasks/link_adaptation_f2 2>&1 | tee run_la_f2.log
