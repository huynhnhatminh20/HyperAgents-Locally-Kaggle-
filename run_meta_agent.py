import argparse
import ast
import os

from agent.llm import DEFAULT_MODEL
from meta_agent import MetaAgent
from utils.git_utils import diff_versus_commit, reset_paths_to_commit


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help="Model to use for the agent",
    )
    parser.add_argument(
        "--chat_history_file",
        type=str,
        default="./outputs/chat_history.md",
        help="Path to chat history file",
    )
    parser.add_argument(
        "--repo_path", type=str, default="./", help="Path to the agent file"
    )
    parser.add_argument(
        "--evals_folder",
        type=str,
        default="./outputs/",
        help="Path to the folder containing the evaluation files",
    )
    parser.add_argument(
        "--iterations_left",
        type=int,
        default=None,
        help="The number of remaining iterations in which the meta agent will be invoked in future.",
    )
    parser.add_argument(
        "--git_dir", required=True, help="Path to git repository directory"
    )
    parser.add_argument(
        "--base_commit", required=True, help="Base commit hash to compare against"
    )
    parser.add_argument(
        "--outdir", required=False, default="./outputs/", help="Output directory"
    )
    args = parser.parse_args()

    # Run meta agent
    meta_agent = MetaAgent(
        model=args.model,
        chat_history_file=args.chat_history_file,
    )
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
                source = f.read()
            ast.parse(source)
            print("[syntax-check] task_agent.py: OK")
        except SyntaxError as e:
            print(f"[syntax-check] task_agent.py: SYNTAX ERROR — {e}")
            print("  The meta agent produced invalid Python. Patch will be empty.")
            # Restore the file so the diff is clean
            reset_paths_to_commit(
                git_dname=args.git_dir, commit=args.base_commit, paths=["task_agent.py"]
            )

    # Reset unwanted diffs
    reset_paths_to_commit(
        git_dname=args.git_dir, commit=args.base_commit, paths=["domains/"]
    )

    # Save git diff
    model_patch = diff_versus_commit(args.git_dir, args.base_commit)
    model_patch_outfile = (
        os.path.join(args.outdir, "model_patch.diff")
        if args.outdir
        else "model_patch.diff"
    )
    if args.outdir:
        os.makedirs(args.outdir, exist_ok=True)
    with open(model_patch_outfile, "w") as f:
        f.write(model_patch)


if __name__ == "__main__":
    main()
