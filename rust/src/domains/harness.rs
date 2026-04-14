use anyhow::Result;
use rayon::prelude::*;
use std::path::{Path, PathBuf};
use crate::agent::task_agent::TaskAgent;
use crate::domains::{text_classify, emotion};

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

    let (ids_labels, inputs): (Vec<(String, String)>, Vec<serde_json::Value>) = match domain {
        "text_classify" => {
            let s = text_classify::get_split(subset);
            (s.iter().map(|x| (x.id.clone(), x.label.clone())).collect(),
             s.iter().map(|x| text_classify::format_input(x)).collect())
        }
        "emotion" => {
            let s = emotion::get_split(subset);
            (s.iter().map(|x| (x.id.clone(), x.label.clone())).collect(),
             s.iter().map(|x| emotion::format_input(x)).collect())
        }
        other => return Err(anyhow::anyhow!("Domain '{}' not supported", other)),
    };

    let mut combined: Vec<(String, String, serde_json::Value)> = ids_labels
        .into_iter().zip(inputs).map(|((id, lbl), inp)| (id, lbl, inp)).collect();
    if num_samples > 0 { combined.truncate(num_samples as usize); }
    println!("  Running {} samples for domain={} subset={}...", combined.len(), domain, subset);

    let results: Vec<(String, String, String)> = combined.par_iter().map(|(id, label, input)| {
        let pred = agent.forward(input).unwrap_or_else(|e| {
            eprintln!("  [WARN] agent.forward failed for {}: {}", id, e);
            String::new()
        });
        (id.clone(), label.clone(), pred)
    }).collect();

    let predictions_path = eval_dir.join("predictions.csv");
    let mut wtr = csv::Writer::from_path(&predictions_path)?;
    wtr.write_record(["id", "label", "prediction"])?;
    for (id, label, pred) in &results { wtr.write_record([id, label, pred])?; }
    wtr.flush()?;
    println!("  Predictions saved to {}", predictions_path.display());
    Ok(eval_dir)
}
