import argparse
import ast
import os
import sys

# Make agent/, utils/, meta_agent.py importable from python/
_PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
if _PYTHON_DIR not in sys.path:
    sys.path.insert(0, _PYTHON_DIR)

from agent.llm import DEFAULT_MODEL
from meta_agent import MetaAgent
from utils.git_utils import diff_versus_commit, reset_paths_to_commit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--chat_history_file", type=str, default="./outputs/chat_history.md")
    parser.add_argument("--repo_path", type=str, default="./",
                        help="Path to the python/ directory (where task_agent.py lives)")
    parser.add_argument("--evals_folder", type=str, default="./outputs/")
    parser.add_argument("--iterations_left", type=int, default=None)
    parser.add_argument("--git_dir", required=True, help="Path to git repository root")
    parser.add_argument("--base_commit", required=True)
    parser.add_argument("--outdir", required=False, default="./outputs/")
    args = parser.parse_args()

    # Run meta agent — it reads task_agent.py from repo_path and edits it
    meta_agent = MetaAgent(model=args.model, chat_history_file=args.chat_history_file)
    meta_agent.forward(
        repo_path=args.repo_path,
        eval_path=args.evals_folder,
        iterations_left=args.iterations_left,
    )

    # Syntax-check task_agent.py before accepting the patch
    task_agent_path = os.path.join(args.repo_path, "task_agent.py")
    if os.path.exists(task_agent_path):
        try:
            with open(task_agent_path) as f:
                ast.parse(f.read())
            print("[syntax-check] task_agent.py: OK")
        except SyntaxError as e:
            print(f"[syntax-check] task_agent.py: SYNTAX ERROR — {e}")
            print("  Restoring original to keep diff clean.")
            reset_paths_to_commit(
                git_dname=args.git_dir,
                commit=args.base_commit,
                paths=["python/task_agent.py"],
            )

    # Reset any unintended changes to domains/ (meta agent should only touch task_agent.py)
    reset_paths_to_commit(
        git_dname=args.git_dir,
        commit=args.base_commit,
        paths=["python/domains/"],
    )

    # Save the git diff as the patch
    model_patch = diff_versus_commit(args.git_dir, args.base_commit)
    if args.outdir:
        os.makedirs(args.outdir, exist_ok=True)
    outfile = os.path.join(args.outdir, "model_patch.diff") if args.outdir else "model_patch.diff"
    with open(outfile, "w") as f:
        f.write(model_patch)


if __name__ == "__main__":
    main()
