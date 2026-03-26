# Copyright (c) Meta Platforms, Inc. and affiliates.
# Local (Docker-free) generate loop for HyperAgents with Ollama.

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime

from utils.common import file_exist_and_not_empty, load_json_file


def run_command(cmd, workdir=None, timeout=3600):
    """Run a command as subprocess with timeout. Returns (exit_code, stdout, stderr)."""
    print(f"  [CMD] {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(
            cmd, cwd=workdir, capture_output=True, text=True,
            timeout=timeout, shell=isinstance(cmd, str),
        )
        if result.stdout.strip():
            print(f"  [OUT] {result.stdout.strip()[:500]}")
        if result.returncode != 0 and result.stderr.strip():
            print(f"  [ERR] {result.stderr.strip()[:500]}")
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] after {timeout}s")
        return -1, "", "timeout"
    except Exception as e:
        print(f"  [ERROR] {e}")
        return -1, "", str(e)


def git_diff(workdir, base_commit):
    """Get git diff against base commit."""
    code, stdout, _ = run_command(["git", "diff", base_commit], workdir=workdir)
    return stdout if code == 0 else ""


def git_reset(workdir, commit):
    """Reset git to a commit."""
    run_command(["git", "reset", "--hard", commit], workdir=workdir)
    run_command(["git", "clean", "-fd"], workdir=workdir)


def git_apply_diff(workdir, diff_file):
    """Apply a diff file."""
    if os.path.exists(diff_file) and os.path.getsize(diff_file) > 0:
        code, _, _ = run_command(["git", "apply", "--allow-empty", diff_file], workdir=workdir)
        return code == 0
    return False


def get_base_commit(workdir):
    """Get current HEAD commit."""
    code, stdout, _ = run_command(["git", "rev-parse", "HEAD"], workdir=workdir)
    return stdout.strip() if code == 0 else "HEAD"


def get_score_from_report(report_path):
    """Extract accuracy score from a report.json."""
    try:
        with open(report_path, "r") as f:
            report = json.load(f)
        return report.get("overall_accuracy", None)
    except Exception:
        return None


def run_initial_eval(project_dir, domain, model, output_dir, num_samples=-1, subset="_train"):
    """Run initial evaluation of the base task agent."""
    print(f"\n{'='*60}")
    print(f"Running initial evaluation on {domain}...")
    print(f"{'='*60}")

    run_id = f"initial_{domain}{subset}_0"
    cmd = [
        sys.executable, "-m", "domains.harness",
        "--agent_path", "./task_agent.py",
        "--output_dir", output_dir,
        "--run_id", run_id,
        "--domain", domain,
        "--num_samples", str(num_samples),
        "--num_workers", "1",
        "--subset", subset,
    ]
    run_command(cmd, workdir=project_dir, timeout=1800)

    # Generate report
    eval_dir = os.path.join(output_dir, run_id)
    cmd = [
        sys.executable, "-m", "domains.report",
        "--domain", domain,
        "--dname", eval_dir,
    ]
    run_command(cmd, workdir=project_dir, timeout=300)

    score = get_score_from_report(os.path.join(eval_dir, "report.json"))
    print(f"  Initial score: {score}")
    return score


def run_meta_agent(project_dir, model, output_dir, base_commit, evals_folder, iterations_left=5):
    """Run the meta agent to produce modifications."""
    print(f"\n  Running meta agent (model={model})...")

    agent_output_dir = os.path.join(output_dir, "agent_output")
    os.makedirs(agent_output_dir, exist_ok=True)
    chat_history_file = os.path.join(agent_output_dir, "meta_agent_chat_history.md")

    cmd = [
        sys.executable, "run_meta_agent.py",
        "--model", model,
        "--chat_history_file", chat_history_file,
        "--repo_path", project_dir + "/",
        "--evals_folder", evals_folder,
        "--git_dir", project_dir,
        "--base_commit", base_commit,
        "--outdir", agent_output_dir,
        "--iterations_left", str(iterations_left),
    ]
    code, _, _ = run_command(cmd, workdir=project_dir, timeout=3600)

    patch_file = os.path.join(agent_output_dir, "model_patch.diff")
    success = code == 0 and file_exist_and_not_empty(patch_file)
    print(f"  Meta agent {'succeeded' if success else 'failed'}, patch: {os.path.exists(patch_file)}")
    return success, patch_file


def run_eval(project_dir, domain, model, output_dir, gen_id, num_samples=-1, subset="_train"):
    """Evaluate the current task agent."""
    print(f"  Evaluating generation {gen_id}...")

    run_id = f"{domain}_eval"
    eval_output_dir = os.path.join(output_dir, run_id)
    os.makedirs(eval_output_dir, exist_ok=True)

    cmd = [
        sys.executable, "-m", "domains.harness",
        "--agent_path", "./task_agent.py",
        "--output_dir", output_dir,
        "--run_id", run_id,
        "--domain", domain,
        "--num_samples", str(num_samples),
        "--num_workers", "1",
        "--subset", subset,
    ]
    run_command(cmd, workdir=project_dir, timeout=1800)

    # Generate report
    cmd = [
        sys.executable, "-m", "domains.report",
        "--domain", domain,
        "--dname", eval_output_dir,
    ]
    run_command(cmd, workdir=project_dir, timeout=300)

    score = get_score_from_report(os.path.join(eval_output_dir, "report.json"))
    print(f"  Score for gen {gen_id}: {score}")
    return score


def select_parent(archive, method="best"):
    """Simple parent selection from archive."""
    if not archive:
        return "initial"

    valid = [a for a in archive if a.get("score") is not None]
    if not valid:
        return archive[-1]["id"]

    if method == "best":
        return max(valid, key=lambda x: x["score"])["id"]
    elif method == "latest":
        return valid[-1]["id"]
    else:  # random/proportional
        import random
        scores = [max(a["score"], 0.01) for a in valid]
        total = sum(scores)
        probs = [s / total for s in scores]
        return random.choices(valid, weights=probs, k=1)[0]["id"]


def generate_loop_local(
    domain="text_classify",
    model=None,
    max_generation=5,
    num_samples=-1,
    output_dir_parent=None,
    parent_selection="best",
):
    """Main local generation loop — no Docker required."""

    if model is None:
        from agent.llm import DEFAULT_MODEL
        model = DEFAULT_MODEL

    # Set the model in env so all subprocesses pick it up
    os.environ["MODEL_NAME"] = model

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    if output_dir_parent is None:
        output_dir_parent = os.path.join(os.getcwd(), "outputs_local")
    output_dir = os.path.join(output_dir_parent, f"run_{run_id}")
    os.makedirs(output_dir, exist_ok=True)

    project_dir = os.getcwd()
    base_commit = get_base_commit(project_dir)
    archive = []
    archive_file = os.path.join(output_dir, "archive.jsonl")

    print(f"{'='*60}")
    print(f"HyperAgents Local Loop")
    print(f"  Model:      {model}")
    print(f"  Domain:     {domain}")
    print(f"  Gens:       {max_generation}")
    print(f"  Output:     {output_dir}")
    print(f"  Base commit:{base_commit[:8]}")
    print(f"{'='*60}")

    # --- Initial evaluation ---
    subset = "_train" if domain == "text_classify" else ""
    initial_score = run_initial_eval(
        project_dir, domain, model, os.path.join(output_dir, "gen_initial"),
        num_samples=num_samples, subset=subset,
    )
    archive.append({"id": "initial", "parent": None, "score": initial_score, "gen": 0})
    with open(archive_file, "a") as f:
        f.write(json.dumps(archive[-1]) + "\n")

    # --- Generation loop ---
    for gen_id in range(1, max_generation + 1):
        print(f"\n{'='*60}")
        print(f"Generation {gen_id}/{max_generation}")
        print(f"{'='*60}")

        parent_id = select_parent(archive, method=parent_selection)
        print(f"  Parent: {parent_id}")

        gen_output_dir = os.path.join(output_dir, f"gen_{gen_id}")
        os.makedirs(gen_output_dir, exist_ok=True)

        # Reset to base
        git_reset(project_dir, base_commit)

        # Apply parent diffs (lineage)
        parent_entry = next((a for a in archive if a["id"] == parent_id), None)
        if parent_entry and "patch_file" in parent_entry:
            git_apply_diff(project_dir, parent_entry["patch_file"])

        # Run meta agent
        evals_folder = output_dir  # meta agent can see previous gen results
        success, patch_file = run_meta_agent(
            project_dir, model, gen_output_dir, base_commit,
            evals_folder, iterations_left=max_generation - gen_id,
        )

        score = None
        if success:
            # Apply the new diff and evaluate
            git_reset(project_dir, base_commit)
            # Re-apply parent lineage
            if parent_entry and "patch_file" in parent_entry:
                git_apply_diff(project_dir, parent_entry["patch_file"])
            # Apply new modifications
            git_apply_diff(project_dir, patch_file)

            score = run_eval(
                project_dir, domain, model, gen_output_dir,
                gen_id, num_samples=num_samples, subset=subset,
            )
        else:
            print(f"  Meta agent failed, skipping evaluation.")

        # Store in archive
        entry = {
            "id": gen_id,
            "parent": parent_id,
            "score": score,
            "gen": gen_id,
            "patch_file": patch_file if success else None,
            "meta_success": success,
        }
        archive.append(entry)
        with open(archive_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        # Save metadata
        metadata = {
            "gen_id": gen_id,
            "parent_id": parent_id,
            "score": score,
            "model": model,
            "domain": domain,
            "meta_success": success,
        }
        with open(os.path.join(gen_output_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"  Gen {gen_id} done — score: {score}, parent: {parent_id}")

    # --- Final reset ---
    git_reset(project_dir, base_commit)

    # --- Summary ---
    print(f"\n{'='*60}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*60}")
    for entry in archive:
        marker = " ⭐" if entry.get("score") == max(
            (a.get("score", 0) or 0 for a in archive)
        ) else ""
        print(f"  Gen {entry['id']:>8} | Score: {entry.get('score', 'N/A'):>8} | Parent: {entry.get('parent', '-'):>8}{marker}")

    best = max((a for a in archive if a.get("score") is not None), key=lambda x: x["score"], default=None)
    if best:
        print(f"\n  Best: Gen {best['id']} with score {best['score']:.3f}")

    print(f"\n  Output saved to: {output_dir}")
    return output_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HyperAgents Local Loop (Docker-free)")
    parser.add_argument("--domain", type=str, default="text_classify",
                        choices=["text_classify", "search_arena", "paper_review"],
                        help="Domain to optimize on")
    parser.add_argument("--model", type=str, default=None,
                        help="Model to use (e.g., ollama/llama3.2, mlx/BeastCode/Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit)")
    parser.add_argument("--max-generation", type=int, default=5,
                        help="Number of evolution generations")
    parser.add_argument("--num-samples", type=int, default=-1,
                        help="Number of samples to evaluate (-1 for all)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory")
    parser.add_argument("--parent-selection", type=str, default="best",
                        choices=["best", "latest", "proportional"],
                        help="Parent selection method")
    args = parser.parse_args()

    generate_loop_local(
        domain=args.domain,
        model=args.model,
        max_generation=args.max_generation,
        num_samples=args.num_samples,
        output_dir_parent=args.output_dir,
        parent_selection=args.parent_selection,
    )
