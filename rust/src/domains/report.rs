use anyhow::{Context, Result};
use std::collections::HashMap;
use std::path::Path;

pub fn generate_report(eval_dir: &Path, _domain: &str) -> Result<f64> {
    let predictions_path = eval_dir.join("predictions.csv");
    let mut reader = csv::Reader::from_path(&predictions_path)
        .with_context(|| format!("Cannot open {}", predictions_path.display()))?;

    let mut rows: Vec<(String, String, String)> = Vec::new();
    for result in reader.records() {
        let record = result?;
        let id = record.get(0).unwrap_or("").to_string();
        let label = record.get(1).unwrap_or("").trim().to_lowercase();
        let prediction = record.get(2).unwrap_or("").trim().to_lowercase();
        if prediction.is_empty() { continue; }
        rows.push((id, label, prediction));
    }

    if rows.is_empty() {
        write_report(eval_dir, 0.0, 0, 0, HashMap::new(), HashMap::new(), HashMap::new(), vec![], vec![])?;
        return Ok(0.0);
    }

    let total = rows.len();
    let correct = rows.iter().filter(|(_, l, p)| l == p).count();
    let accuracy = correct as f64 / total as f64;
    println!("  Accuracy: {:.3}, Total correct: {} / {}", accuracy, correct, total);

    let labels: std::collections::HashSet<String> = rows.iter().map(|(_, l, _)| l.clone()).collect();
    let mut label_report: HashMap<String, serde_json::Value> = HashMap::new();
    for label in &labels {
        let tp = rows.iter().filter(|(_, l, p)| l == label && p == label).count() as f64;
        let fp = rows.iter().filter(|(_, l, p)| l != label && p == label).count() as f64;
        let fn_ = rows.iter().filter(|(_, l, p)| l == label && p != label).count() as f64;
        let precision = if tp + fp > 0.0 { tp / (tp + fp) } else { 0.0 };
        let recall = if tp + fn_ > 0.0 { tp / (tp + fn_) } else { 0.0 };
        let total_label = rows.iter().filter(|(_, l, _)| l == label).count();
        println!("    Label: {} - Precision: {:.3}, Recall: {:.3}, Correct: {} / {}", label, precision, recall, tp as usize, total_label);
        label_report.insert(label.clone(), serde_json::json!({"precision": precision, "recall": recall, "correct": tp as usize, "total": total_label}));
    }

    let mut gt_dist: HashMap<String, f64> = HashMap::new();
    let mut pred_dist: HashMap<String, f64> = HashMap::new();
    for (_, label, pred) in &rows {
        *gt_dist.entry(label.clone()).or_insert(0.0) += 1.0;
        *pred_dist.entry(pred.clone()).or_insert(0.0) += 1.0;
    }
    for v in gt_dist.values_mut() { *v /= total as f64; }
    for v in pred_dist.values_mut() { *v /= total as f64; }

    let failed: Vec<String> = rows.iter().filter(|(_, l, p)| l != p).map(|(id, _, _)| id.clone()).collect();
    let passed: Vec<String> = rows.iter().filter(|(_, l, p)| l == p).map(|(id, _, _)| id.clone()).collect();

    write_report(eval_dir, accuracy, correct, total, label_report, gt_dist, pred_dist, failed, passed)?;
    Ok(accuracy)
}

fn write_report(
    eval_dir: &Path, accuracy: f64, correct: usize, total: usize,
    label_report: HashMap<String, serde_json::Value>,
    gt_dist: HashMap<String, f64>, pred_dist: HashMap<String, f64>,
    failed: Vec<String>, passed: Vec<String>,
) -> Result<()> {
    let random_guess_accuracy: f64 = gt_dist.values().map(|p| p * p).sum();
    let report = serde_json::json!({
        "overall_accuracy": accuracy, "total_correct": correct, "total": total,
        "accuracy_by_ground_truth": label_report,
        "label_distribution": {"ground_truth": gt_dist, "prediction": pred_dist},
        "random_guess_accuracy": random_guess_accuracy,
        "question_ids_failed": failed, "question_ids_passed": passed,
    });
    let report_path = eval_dir.join("report.json");
    std::fs::write(&report_path, serde_json::to_string_pretty(&report)?)?;
    println!("  Report written to {}", report_path.display());
    Ok(())
}
