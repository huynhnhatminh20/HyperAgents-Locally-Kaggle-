#!/usr/bin/env python3
"""Kaggle entrypoint for running the factory loop with local Transformers 4-bit inference."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


WORK_ROOT = Path("/kaggle/working")
REPO_DST = WORK_ROOT / "HyperAgents-Locally"
REPO_URL = os.environ.get("HYPERAGENTS_REPO_URL", "https://github.com/quantumnic/HyperAgents-Locally.git")
REPO_REF = os.environ.get("HYPERAGENTS_REPO_REF", "")
DEFAULT_MODEL = "hf-local/Qwen/Qwen2.5-7B-Instruct"
EXTRA_PACKAGES = [
    "backoff",
    "transformers>=4.45.0",
    "accelerate>=0.34.0",
    "bitsandbytes>=0.43.0",
    "sentencepiece>=0.2.0",
]


HF_LOCAL_HELPER = '''
# --- Hugging Face local 4-bit models (GPU inference) ---
HF_LOCAL_QWEN_7B = "hf-local/Qwen/Qwen2.5-7B-Instruct"
_hf_local_cache = {}


def _get_hf_local_response(messages, model_id, max_tokens, temperature):
    """Generate a response using Transformers 4-bit inference."""
    try:
        import torch
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
        )
    except ImportError:
        raise ImportError(
            "transformers + accelerate + bitsandbytes are required for hf-local models."
        )

    model_name = model_id.removeprefix("hf-local/")
    if model_name not in _hf_local_cache:
        print(f"  [HF-LOCAL] Loading model from {model_name} ...")
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        model_obj = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            quantization_config=quant_config,
            torch_dtype=torch.float16,
            trust_remote_code=True,
        )
        _hf_local_cache[model_name] = (model_obj, tokenizer)

    model_obj, tokenizer = _hf_local_cache[model_name]

    chat_kwargs = dict(tokenize=False, add_generation_prompt=True)
    try:
        prompt = tokenizer.apply_chat_template(messages, **chat_kwargs, enable_thinking=False)
    except TypeError:
        prompt = tokenizer.apply_chat_template(messages, **chat_kwargs)

    inputs = tokenizer(prompt, return_tensors="pt").to(model_obj.device)
    with torch.no_grad():
        output_ids = model_obj.generate(
            **inputs,
            max_new_tokens=min(max_tokens, 512),
            do_sample=temperature > 0,
            temperature=max(temperature, 1e-5),
            pad_token_id=tokenizer.eos_token_id,
        )

    generated_ids = output_ids[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
'''


HF_LOCAL_BRANCH = '''
    # ----- Hugging Face local path (Transformers 4-bit on GPU) -----
    if model.startswith("hf-local/"):
        response_text = _get_hf_local_response(
            new_msg_history, model, max_tokens=min(max_tokens, 512),
            temperature=temperature,
        )
        new_msg_history.append({"role": "assistant", "content": response_text})
        new_msg_history = [
            {**m, "text": m.pop("content")} if "content" in m else m
            for m in new_msg_history
        ]
        return response_text, new_msg_history, {}

'''


def get_secret(name: str) -> str | None:
    value = os.environ.get(name)
    if value:
        return value

    try:
        from kaggle_secrets import UserSecretsClient

        return UserSecretsClient().get_secret(name)
    except Exception:
        return None


def ensure_repo_copy() -> None:
    print(f"[setup] Cloning repo from {REPO_URL}")
    if REPO_DST.exists():
        shutil.rmtree(REPO_DST)
    subprocess.run(["git", "clone", REPO_URL, str(REPO_DST)], check=True)
    if REPO_REF:
        print(f"[setup] Checking out ref {REPO_REF}")
        subprocess.run(["git", "checkout", REPO_REF], cwd=REPO_DST, check=True)


def patch_llm_backend() -> None:
    llm_path = REPO_DST / "python" / "agent" / "llm.py"
    text = llm_path.read_text(encoding="utf-8")

    if "HF_LOCAL_QWEN_7B" not in text:
        marker = 'OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")'
        text = text.replace(marker, HF_LOCAL_HELPER + "\n" + marker)

    if 'if model.startswith("hf-local/"):' not in text:
        marker = '    # ----- litellm path (Ollama / Cloud) -----'
        text = text.replace(marker, HF_LOCAL_BRANCH + marker)

    default_marker = 'DEFAULT_MODEL = os.environ.get("MODEL_NAME", OLLAMA_LLAMA)'
    if default_marker in text:
        text = text.replace(
            default_marker,
            'DEFAULT_MODEL = os.environ.get("MODEL_NAME", "hf-local/Qwen/Qwen2.5-7B-Instruct")',
        )

    llm_path.write_text(text, encoding="utf-8")
    print(f"[setup] Patched local HF backend into {llm_path}")


def configure_hf_token() -> None:
    hf_token = get_secret("HF_TOKEN") or get_secret("HUGGINGFACE_HUB_TOKEN")
    if hf_token:
        os.environ["HF_TOKEN"] = hf_token
        os.environ["HUGGINGFACE_HUB_TOKEN"] = hf_token
        print("[setup] Hugging Face token found and exported for model downloads")
    else:
        print("[setup] HF_TOKEN/HUGGINGFACE_HUB_TOKEN not found; public models may still work")


def write_env_file() -> str:
    env_path = REPO_DST / ".env"
    model_name = os.environ.get("MODEL_NAME", DEFAULT_MODEL)
    max_tokens = os.environ.get("MAX_TOKENS", "512")
    lines = [
        f"MODEL_NAME={model_name}",
        f"MAX_TOKENS={max_tokens}",
        "ENABLE_META_FALLBACK=0",
    ]
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[setup] Wrote runtime env to {env_path}")
    return model_name


def install_runtime_dependencies() -> None:
    print("[setup] Installing repo requirements")
    subprocess.run(["python", "-m", "pip", "install", "--upgrade", "pip"], cwd=REPO_DST, check=True)
    subprocess.run(["python", "-m", "pip", "install", "-r", "requirements.txt"], cwd=REPO_DST, check=True)
    subprocess.run(["python", "-m", "pip", "install", *EXTRA_PACKAGES], cwd=REPO_DST, check=True)


def run_loop(model_name: str) -> None:
    cmd = [
        "python",
        "python/loop.py",
        "--domain",
        os.environ.get("HYPERAGENTS_DOMAIN", "factory"),
        "--model",
        model_name,
        "--max-generation",
        os.environ.get("HYPERAGENTS_MAX_GENERATION", "1"),
        "--num-samples",
        os.environ.get("HYPERAGENTS_NUM_SAMPLES", "3"),
        "--num-workers",
        os.environ.get("HYPERAGENTS_NUM_WORKERS", "1"),
        "--verbose",
    ]
    print(f"[run] Running loop with model={model_name}")
    subprocess.run(cmd, cwd=REPO_DST, check=True)


def main() -> None:
    ensure_repo_copy()
    configure_hf_token()
    patch_llm_backend()
    model_name = write_env_file()
    install_runtime_dependencies()
    run_loop(model_name)


if __name__ == "__main__":
    main()
