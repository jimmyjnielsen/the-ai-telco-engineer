#!/bin/bash
set -e
# Load ANTHROPIC_API_KEY from ~/.bashrc (which has a non-interactive early-return)
eval "$(grep "^export ANTHROPIC_API_KEY" ~/.bashrc)"
cd ~/repos/the-ai-telco-engineer
export MODEL_API_KEY=local
~/LLM/venv/bin/python3 launch.py tasks/link_adaptation_g0 2>&1 | tee run_la_g0.log
