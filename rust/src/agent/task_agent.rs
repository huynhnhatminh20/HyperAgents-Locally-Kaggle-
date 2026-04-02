use anyhow::Result;
use crate::llm::{LlmClient, Message};

pub const DEFAULT_PROMPT: &str = "You are a sentiment classifier. Classify the sentiment of the given text.\nRespond with ONLY one word: positive, negative, or neutral.\nDo not add any explanation or punctuation.";

pub struct TaskAgent {
    pub model: String,
}

impl TaskAgent {
    pub fn new(model: &str) -> Self {
        Self { model: model.to_string() }
    }

    fn load_system_prompt() -> String {
        let prompt_path = std::path::Path::new("agent_prompt.txt");
        if prompt_path.exists() {
            std::fs::read_to_string(prompt_path).unwrap_or_else(|_| DEFAULT_PROMPT.to_string())
        } else {
            DEFAULT_PROMPT.to_string()
        }
    }

    pub fn forward(&self, inputs: &serde_json::Value) -> Result<String> {
        let text = inputs.get("text").and_then(|v| v.as_str()).unwrap_or("");
        let instruction = inputs.get("instruction").and_then(|v| v.as_str()).unwrap_or("");
        let system_prompt = Self::load_system_prompt();
        let user_content = if instruction.is_empty() {
            format!("Text: {}", text)
        } else {
            format!("{}\n\nText: {}", instruction, text)
        };
        let messages = vec![
            Message { role: "system".to_string(), content: system_prompt },
            Message { role: "user".to_string(), content: user_content },
        ];
        let client = LlmClient::new(&self.model);
        let response = client.chat(&messages)?;
        Ok(self.parse_prediction(&response))
    }

    fn parse_prediction(&self, response: &str) -> String {
        let cleaned = response.trim().to_lowercase();
        let first = cleaned.lines().next().unwrap_or("")
            .split_whitespace().next().unwrap_or("")
            .trim_matches(|c: char| !c.is_alphabetic());
        if first == "positive" || first == "negative" || first == "neutral" {
            return first.to_string();
        }
        for label in &["positive", "negative", "neutral"] {
            if cleaned.contains(label) { return label.to_string(); }
        }
        "neutral".to_string()
    }
}
