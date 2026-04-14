import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import argparse
import importlib
import json
import pandas as pd


def report(dname, domain, suffix=""):
    """Compute accuracy metrics and save report.json for a completed harness run."""
    utils_module = importlib.import_module(f"domains.{domain}.utils")
    ground_truth_key = utils_module.GROUND_TRUTH_KEY
    question_id_col = utils_module.QUESTION_ID

    path = os.path.join(dname, f"predictions{suffix}.csv")
    df = pd.read_csv(path, dtype=str)
    df = df[df["prediction"].notna() & (df["prediction"] != "")].copy()
    df["prediction"] = df["prediction"].str.strip().str.lower()
    df[ground_truth_key] = df[ground_truth_key].str.strip().str.lower()
    df["match"] = df[ground_truth_key] == df["prediction"]

    accuracy = df["match"].mean()
    total_correct = int(df["match"].sum())
    total = len(df)
    print(f"Accuracy: {accuracy:.3f}, Total correct: {total_correct} / {total}")

    label_counts = df[ground_truth_key].value_counts()
    print("\nAccuracy by label:")
    label_report = {}
    for label in sorted(df[ground_truth_key].unique()):
        tp = ((df["prediction"] == label) & (df[ground_truth_key] == label)).sum()
        fp = ((df["prediction"] == label) & (df[ground_truth_key] != label)).sum()
        fn = ((df["prediction"] != label) & (df[ground_truth_key] == label)).sum()
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        total_label = int(label_counts.get(label, 0))
        print(f"  {label:30s} precision={precision:.3f}  recall={recall:.3f}  {tp}/{total_label}")
        label_report[str(label)] = {
            "precision": float(precision), "recall": float(recall),
            "correct": int(tp), "total": total_label,
        }

    gt_dist = df[ground_truth_key].value_counts(normalize=True).to_dict()
    pred_dist = df["prediction"].value_counts(normalize=True).to_dict()
    random_guess_acc = sum(p**2 for p in gt_dist.values())
    print(f"\nRandom-guess baseline: {random_guess_acc:.3f}")

    result = {
        "overall_accuracy": float(accuracy),
        "total_correct": total_correct,
        "total": total,
        "accuracy_by_label": label_report,
        "label_distribution": {"ground_truth": gt_dist, "prediction": pred_dist},
        "random_guess_accuracy": random_guess_acc,
        "ids_failed": [row[question_id_col] for _, row in df[~df["match"]].iterrows()],
        "ids_passed": [row[question_id_col] for _, row in df[df["match"]].iterrows()],
    }

    report_path = os.path.join(dname, f"report{suffix}.json")
    with open(report_path, "w") as f:
        json.dump(result, f, indent=4)
    return result, report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate accuracy report from harness output.")
    parser.add_argument("--dname", required=True, help="Path to harness output directory")
    parser.add_argument(
        "--domain", type=str, required=True,
        choices=["text_classify", "emotion", "rust", "factory", "search_arena", "paper_review"],
    )
    parser.add_argument("--suffix", type=str, default="", help="Predictions file suffix")
    args = parser.parse_args()
    report(dname=args.dname, domain=args.domain, suffix=args.suffix)
