#!/bin/bash
set -e
cd /home/jjn/repos/the-ai-telco-engineer

export MODEL_API_KEY=PASTE_YOUR_KEY_HERE

/home/jjn/LLM/venv/bin/python3 launch.py tasks/cell_sleep 2>&1 | tee run5_sonnet.log
