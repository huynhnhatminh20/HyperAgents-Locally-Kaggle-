use anyhow::{anyhow, Result};
use std::path::Path;
use std::process::Command;

pub fn get_base_commit(workdir: &Path) -> Result<String> {
    let output = Command::new("git").args(["rev-parse", "HEAD"]).current_dir(workdir).output()?;
    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
    } else {
        Err(anyhow!("git rev-parse HEAD failed"))
    }
}

pub fn git_reset(workdir: &Path, commit: &str) -> Result<()> {
    let _ = Command::new("git").args(["reset", "--hard", commit]).current_dir(workdir).status()?;
    let _ = Command::new("git").args(["clean", "-fd"]).current_dir(workdir).status()?;
    Ok(())
}

pub fn git_apply_diff(workdir: &Path, diff_file: &Path) -> Result<bool> {
    if !crate::utils::common::file_exists_and_not_empty(diff_file) { return Ok(false); }
    let status = Command::new("git")
        .args(["apply", "--allow-empty", diff_file.to_str().unwrap_or("")])
        .current_dir(workdir).status()?;
    Ok(status.success())
}

pub fn git_diff(workdir: &Path, base_commit: &str) -> Result<String> {
    let output = Command::new("git").args(["diff", base_commit]).current_dir(workdir).output()?;
    if output.status.success() { Ok(String::from_utf8_lossy(&output.stdout).to_string()) }
    else { Ok(String::new()) }
}
