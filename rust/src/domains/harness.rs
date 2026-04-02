use anyhow::Result;
use rayon::prelude::*;
use std::path::{Path, PathBuf};
use crate::agent::task_agent::TaskAgent;
use crate::domains::text_classify;

pub fn run_harness(
    agent: &TaskAgent,
    domain: &str,
    output_dir: &Path,
    run_id: &str,
    num_samples: i64,
    subset: &str,
    _num_workers: usize,
) -> Result<PathBuf> {
    let eval_dir = output_dir.join(run_id);
    std::fs::create_dir_all(&eval_dir)?;

    let mut samples = match domain {
        "text_classify" => text_classify::get_split(subset),
        other => return Err(anyhow::anyhow!("Domain '{}' not supported in Rust harness", other)),
    };
    if num_samples > 0 { samples.truncate(num_samples as usize); }
    println!("  Running {} samples for domain={} subset={}...", samples.len(), domain, subset);

    let results: Vec<(String, String, String)> = samples.par_iter().map(|sample| {
        let input = text_classify::format_input(sample);
        let prediction = agent.forward(&input).unwrap_or_else(|e| {
            eprintln!("  [WARN] agent.forward failed for {}: {}", sample.id, e);
            "neutral".to_string()
        });
        (sample.id.clone(), sample.label.clone(), prediction)
    }).collect();

    let predictions_path = eval_dir.join("predictions.csv");
    let mut wtr = csv::Writer::from_path(&predictions_path)?;
    wtr.write_record(["id", "label", "prediction"])?;
    for (id, label, prediction) in &results { wtr.write_record([id, label, prediction])?; }
    wtr.flush()?;
    println!("  Predictions saved to {}", predictions_path.display());
    Ok(eval_dir)
}
