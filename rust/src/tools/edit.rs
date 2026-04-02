use anyhow::{anyhow, Result};
use std::path::Path;

pub struct EditTool;
impl EditTool {
    pub fn view(path: &Path, view_range: Option<(usize, usize)>) -> Result<String> {
        let content = std::fs::read_to_string(path)?;
        match view_range {
            None => Ok(content),
            Some((start, end)) => {
                let lines: Vec<&str> = content.lines().collect();
                let start = start.saturating_sub(1);
                let end = end.min(lines.len());
                Ok(lines[start..end].join("\n"))
            }
        }
    }
    pub fn str_replace(path: &Path, old_str: &str, new_str: &str) -> Result<String> {
        let content = std::fs::read_to_string(path)?;
        if !content.contains(old_str) { return Err(anyhow!("str_replace: old_str not found in {}", path.display())); }
        let new_content = content.replacen(old_str, new_str, 1);
        std::fs::write(path, &new_content)?;
        Ok(format!("Replaced in {}", path.display()))
    }
    pub fn create(path: &Path, content: &str) -> Result<String> {
        if let Some(parent) = path.parent() { std::fs::create_dir_all(parent)?; }
        std::fs::write(path, content)?;
        Ok(format!("Created {}", path.display()))
    }
    pub fn insert(path: &Path, after_line: usize, content: &str) -> Result<String> {
        let text = std::fs::read_to_string(path)?;
        let mut lines: Vec<String> = text.lines().map(|l| l.to_string()).collect();
        let insert_at = after_line.min(lines.len());
        for (i, line) in content.lines().enumerate() { lines.insert(insert_at + i, line.to_string()); }
        std::fs::write(path, lines.join("\n"))?;
        Ok(format!("Inserted after line {} in {}", after_line, path.display()))
    }
}
