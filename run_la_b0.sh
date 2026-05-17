#!/bin/bash
set -e
cd ~/repos/the-ai-telco-engineer
# Qwen3 vLLM must be running on port 8004 before starting this
export MODEL_API_KEY=local
~/LLM/venv/bin/python3 launch.py tasks/link_adaptation_b0 2>&1 | tee run_la_b0.log
