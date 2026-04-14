use anyhow::Result;
use std::path::Path;

pub fn extract_json_blocks(text: &str) -> Vec<serde_json::Value> {
    let mut results = Vec::new();
    let mut search = text;
    while let Some(start) = search.find("<json>") {
        let after_open = &search[start + 6..];
        if let Some(end) = after_open.find("</json>") {
            let json_str = after_open[..end].trim();
            if let Ok(val) = serde_json::from_str(json_str) { results.push(val); }
            search = &after_open[end + 7..];
        } else { break; }
    }
    let mut search2 = text;
    while let Some(start) = search2.find("```json") {
        let after_open = &search2[start + 7..];
        if let Some(end) = after_open.find("```") {
            let json_str = after_open[..end].trim();
            if let Ok(val) = serde_json::from_str(json_str) { results.push(val); }
            search2 = &after_open[end + 3..];
        } else { break; }
    }
    results
}

pub fn file_exists_and_not_empty(path: &Path) -> bool {
    std::fs::metadata(path).map(|m| m.len() > 0).unwrap_or(false)
}

pub fn read_file(path: &Path) -> Result<String> {
    Ok(std::fs::read_to_string(path)?)
}

pub fn get_score_from_report(report_path: &Path) -> Option<f64> {
    let text = std::fs::read_to_string(report_path).ok()?;
    let val: serde_json::Value = serde_json::from_str(&text).ok()?;
    val.get("overall_accuracy")?.as_f64()
}
