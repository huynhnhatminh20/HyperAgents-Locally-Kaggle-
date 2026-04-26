#!/usr/bin/env bash
set -e

cd /kaggle/working/HyperAgents-Locally
cp .env.kaggle .env
bash install.sh

python python/loop.py \
  --domain factory \
  --model llamacpp/qwen2.5-coder-7b \
  --max-generation 2 \
  --num-samples 20 \
  --num-workers 1 \
  --verbose
