#!/bin/bash
set -e
cd ~/repos/the-ai-telco-engineer
export MODEL_API_KEY=local
~/LLM/venv/bin/python3 launch.py tasks/link_adaptation_a0 2>&1 | tee run_la_a0.log
