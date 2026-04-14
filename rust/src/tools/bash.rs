use anyhow::Result;
use std::process::Command;

pub struct BashTool;
impl BashTool {
    pub fn execute(command: &str) -> Result<String> {
        let output = Command::new("sh").arg("-c").arg(command).output()?;
        let combined = format!("{}{}", String::from_utf8_lossy(&output.stdout), String::from_utf8_lossy(&output.stderr));
        let result = if combined.len() > 4000 { format!("{}...[truncated]", &combined[..4000]) } else { combined };
        Ok(result)
    }
}
