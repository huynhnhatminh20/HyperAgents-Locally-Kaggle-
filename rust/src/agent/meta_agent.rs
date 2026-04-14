use anyhow::Result;
use std::path::{Path, PathBuf};
use crate::agent::task_agent::DEFAULT_PROMPT;
use crate::llm::{LlmClient, Message};
use crate::utils::common::get_score_from_report;

pub struct MetaAgent {
    pub model: String,
    pub chat_history_file: PathBuf,
}

impl MetaAgent {
    pub fn new(model: &str, chat_history_file: PathBuf) -> Self {
        Self { model: model.to_string(), chat_history_file }
    }

    pub fn forward(&self, repo_path: &Path, eval_path: &Path, iterations_left: usize, domain: &str) -> Result<()> {
        let prompt_file = repo_path.join("agent_prompt.txt");
        let current_prompt = if prompt_file.exists() {
            std::fs::read_to_string(&prompt_file).unwrap_or_else(|_| DEFAULT_PROMPT.to_string())
        } else {
            DEFAULT_PROMPT.to_string()
        };
        let score_str = self.find_latest_score(eval_path);

        let (task_desc, labels) = match domain {
            "emotion" => (
                "emotion detection (classify the primary emotion in a sentence)",
                "joy, anger, sadness, fear, surprise",
            ),
            "factory" => (
                "factory operations optimization (decide on the best action for a factory setup)",
                "expedite, prioritize_urgent, rebalance, batch_production, optimize_throughput",
            ),
            "search_arena" => (
                "search result comparison (decide which search response is better)",
                "a, b",
            ),
            "paper_review" => (
                "academic paper outcome prediction (decide if a paper should be accepted or rejected)",
                "accept, reject",
            ),
            _ => (
                "sentiment classification",
                "positive, negative, neutral",
            ),
        };

        let user_msg = format!(
            "You are a Meta-Agent improving a {task_desc} prompt.\n\n\
            Current system prompt for the classifier:\n---\n{current_prompt}\n---\n\n\
            Latest evaluation accuracy: {score_str}\n\
            Iterations remaining after this: {iterations_left}\n\n\
            The classifier must output ONLY one of these labels: {labels}\n\n\
            Your task: Write an improved system prompt that achieves higher accuracy.\n\
            The prompt should:\n\
            - Clearly state the valid labels: {labels}\n\
            - Tell the model to respond with ONLY one word (the label)\n\
            - Include brief guidance for distinguishing similar emotions if helpful\n\
            - Not include any code or markdown formatting\n\n\
            Output ONLY the new prompt text. No explanations, no code blocks, no markdown."
        );
        let messages = vec![Message { role: "user".to_string(), content: user_msg.clone() }];
        println!("  [MetaAgent] Calling LLM (model={})...", self.model);
        let client = LlmClient::new(&self.model);
        let new_prompt = client.chat_stream(&messages)?;
        let new_prompt = new_prompt.trim().to_string();
        if new_prompt.is_empty() {
            return Err(anyhow::anyhow!("MetaAgent: LLM returned empty prompt"));
        }
        std::fs::write(&prompt_file, &new_prompt)?;
        println!("  [MetaAgent] Wrote improved prompt to {}", prompt_file.display());
        self.log_conversation(&user_msg, &new_prompt)?;
        Ok(())
    }

    fn find_latest_score(&self, eval_path: &Path) -> String {
        let mut best: Option<(std::time::SystemTime, f64)> = None;
        if let Ok(entries) = std::fs::read_dir(eval_path) {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.is_dir() {
                    let report = path.join("report.json");
                    if let Some(score) = get_score_from_report(&report) {
                        if let Ok(meta) = std::fs::metadata(&report) {
                            if let Ok(modified) = meta.modified() {
                                let is_newer = best.as_ref().map_or(true, |(t, _)| modified > *t);
                                if is_newer { best = Some((modified, score)); }
                            }
                        }
                    }
                }
            }
        }
        let top_report = eval_path.join("report.json");
        if let Some(score) = get_score_from_report(&top_report) {
            if let Ok(meta) = std::fs::metadata(&top_report) {
                if let Ok(modified) = meta.modified() {
                    let is_newer = best.as_ref().map_or(true, |(t, _)| modified > *t);
                    if is_newer { best = Some((modified, score)); }
                }
            }
        }
        match best {
            Some((_, score)) => format!("{:.4}", score),
            None => "N/A".to_string(),
        }
    }

    fn log_conversation(&self, user_msg: &str, assistant_msg: &str) -> Result<()> {
        if let Some(parent) = self.chat_history_file.parent() {
            std::fs::create_dir_all(parent)?;
        }
        let timestamp = chrono::Utc::now().format("%Y-%m-%d %H:%M:%S UTC");
        let entry = format!(
            "\n\n---\n## [{timestamp}] Meta Agent Turn\n\n**User:**\n{user_msg}\n\n**Assistant:**\n{assistant_msg}\n"
        );
        use std::io::Write;
        let mut file = std::fs::OpenOptions::new().create(true).append(true).open(&self.chat_history_file)?;
        file.write_all(entry.as_bytes())?;
        Ok(())
    }
}
