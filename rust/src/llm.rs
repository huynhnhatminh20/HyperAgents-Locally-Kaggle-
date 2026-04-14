use anyhow::{anyhow, Result};
use serde::{Deserialize, Serialize};
use std::io::{BufRead, BufReader};
use std::time::Duration;

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct Message {
    pub role: String,
    pub content: String,
}

pub struct LlmClient {
    pub model: String,
}

impl LlmClient {
    pub fn new(model: &str) -> Self {
        Self { model: model.to_string() }
    }

    pub fn chat(&self, messages: &[Message]) -> Result<String> {
        let max_retries = 3;
        let mut delay_secs = 2u64;
        for attempt in 0..max_retries {
            match self.chat_once(messages) {
                Ok(text) => return Ok(text),
                Err(e) => {
                    if attempt + 1 == max_retries {
                        return Err(e);
                    }
                    eprintln!("  [LLM] attempt {} failed: {}. Retrying in {}s", attempt + 1, e, delay_secs);
                    std::thread::sleep(Duration::from_secs(delay_secs));
                    delay_secs *= 2;
                }
            }
        }
        Err(anyhow!("LLM chat failed after {} retries", max_retries))
    }

    pub fn chat_stream(&self, messages: &[Message]) -> Result<String> {
        if !self.model.starts_with("ollama/") {
            return self.chat(messages);
        }
        let model_name = self.model.strip_prefix("ollama/").unwrap_or(&self.model);
        let ollama_base = std::env::var("OLLAMA_BASE_URL")
            .unwrap_or_else(|_| "http://localhost:11434".to_string());
        let url = format!("{}/api/chat", ollama_base);

        #[derive(Serialize)]
        struct OllamaReq<'a> { model: &'a str, messages: &'a [Message], stream: bool }
        let body = OllamaReq { model: model_name, messages, stream: true };

        let client = reqwest::blocking::Client::builder()
            .timeout(Duration::from_secs(300))
            .build()?;
        let response = client.post(&url).json(&body).send()
            .map_err(|e| anyhow!("Ollama stream request failed: {}", e))?;
        if !response.status().is_success() {
            let status = response.status();
            let text = response.text().unwrap_or_default();
            return Err(anyhow!("Ollama returned {}: {}", status, &text[..text.len().min(500)]));
        }

        let reader = BufReader::new(response);
        let mut full_text = String::new();
        for line in reader.lines() {
            let line = line?;
            if line.is_empty() { continue; }
            if let Ok(val) = serde_json::from_str::<serde_json::Value>(&line) {
                if let Some(token) = val.get("message").and_then(|m| m.get("content")).and_then(|c| c.as_str()) {
                    print!("{}", token);
                    full_text.push_str(token);
                }
                if val.get("done").and_then(|d| d.as_bool()).unwrap_or(false) { break; }
            }
        }
        println!();
        Ok(full_text)
    }

    fn chat_once(&self, messages: &[Message]) -> Result<String> {
        if self.model.starts_with("ollama/") {
            self.chat_ollama(messages)
        } else if self.model.starts_with("anthropic/") {
            self.chat_anthropic(messages)
        } else if self.model.starts_with("openrouter/") {
            self.chat_openrouter(messages)
        } else {
            self.chat_openai(messages)
        }
    }

    fn chat_ollama(&self, messages: &[Message]) -> Result<String> {
        let model_name = self.model.strip_prefix("ollama/").unwrap_or(&self.model);
        let ollama_base = std::env::var("OLLAMA_BASE_URL")
            .unwrap_or_else(|_| "http://localhost:11434".to_string());
        let url = format!("{}/api/chat", ollama_base);
        #[derive(Serialize)]
        struct OllamaReq<'a> { model: &'a str, messages: &'a [Message], stream: bool }
        let body = OllamaReq { model: model_name, messages, stream: false };
        let client = reqwest::blocking::Client::builder().timeout(Duration::from_secs(300)).build()?;
        let response = client.post(&url).json(&body).send()
            .map_err(|e| anyhow!("Ollama request failed: {}", e))?;
        if !response.status().is_success() {
            let status = response.status();
            let text = response.text().unwrap_or_default();
            return Err(anyhow!("Ollama returned {}: {}", status, &text[..text.len().min(500)]));
        }
        let val: serde_json::Value = response.json()?;
        val.get("message").and_then(|m| m.get("content")).and_then(|c| c.as_str())
            .map(|s| s.to_string())
            .ok_or_else(|| anyhow!("Unexpected Ollama response shape"))
    }

    fn chat_openai(&self, messages: &[Message]) -> Result<String> {
        let api_key = std::env::var("OPENAI_API_KEY").map_err(|_| anyhow!("OPENAI_API_KEY not set"))?;
        let model_name = self.model.strip_prefix("openai/").unwrap_or(&self.model);
        #[derive(Serialize)]
        struct OpenAiReq<'a> { model: &'a str, messages: &'a [Message], max_tokens: u32 }
        let body = OpenAiReq { model: model_name, messages, max_tokens: 4096 };
        let client = reqwest::blocking::Client::builder().timeout(Duration::from_secs(300)).build()?;
        let response = client.post("https://api.openai.com/v1/chat/completions")
            .bearer_auth(&api_key).json(&body).send()
            .map_err(|e| anyhow!("OpenAI request failed: {}", e))?;
        if !response.status().is_success() {
            let status = response.status();
            let text = response.text().unwrap_or_default();
            return Err(anyhow!("OpenAI returned {}: {}", status, &text[..text.len().min(500)]));
        }
        let val: serde_json::Value = response.json()?;
        val.get("choices").and_then(|c| c.get(0)).and_then(|c| c.get("message"))
            .and_then(|m| m.get("content")).and_then(|c| c.as_str())
            .map(|s| s.to_string())
            .ok_or_else(|| anyhow!("Unexpected OpenAI response shape"))
    }

    fn chat_openrouter(&self, messages: &[Message]) -> Result<String> {
        let api_key = std::env::var("OPENROUTER_API_KEY")
            .map_err(|_| anyhow!("OPENROUTER_API_KEY not set"))?;
        let model_name = self.model.strip_prefix("openrouter/").unwrap_or(&self.model);
        #[derive(Serialize)]
        struct Req<'a> { model: &'a str, messages: &'a [Message], max_tokens: u32 }
        let body = Req { model: model_name, messages, max_tokens: 4096 };
        let client = reqwest::blocking::Client::builder().timeout(Duration::from_secs(300)).build()?;
        let response = client
            .post("https://openrouter.ai/api/v1/chat/completions")
            .bearer_auth(&api_key)
            .json(&body)
            .send()
            .map_err(|e| anyhow!("OpenRouter request failed: {}", e))?;
        if !response.status().is_success() {
            let status = response.status();
            let text = response.text().unwrap_or_default();
            return Err(anyhow!("OpenRouter returned {}: {}", status, &text[..text.len().min(500)]));
        }
        let val: serde_json::Value = response.json()?;
        val.get("choices").and_then(|c| c.get(0)).and_then(|c| c.get("message"))
            .and_then(|m| m.get("content")).and_then(|c| c.as_str())
            .map(|s| s.to_string())
            .ok_or_else(|| anyhow!("Unexpected OpenRouter response shape"))
    }

    fn chat_anthropic(&self, messages: &[Message]) -> Result<String> {
        let api_key = std::env::var("ANTHROPIC_API_KEY").map_err(|_| anyhow!("ANTHROPIC_API_KEY not set"))?;
        let model_name = self.model.strip_prefix("anthropic/").unwrap_or(&self.model);
        let mut system_content = String::new();
        let mut user_messages: Vec<serde_json::Value> = Vec::new();
        for msg in messages {
            if msg.role == "system" {
                system_content = msg.content.clone();
            } else {
                user_messages.push(serde_json::json!({"role": msg.role, "content": msg.content}));
            }
        }
        let mut body = serde_json::json!({"model": model_name, "max_tokens": 4096, "messages": user_messages});
        if !system_content.is_empty() { body["system"] = serde_json::Value::String(system_content); }
        let client = reqwest::blocking::Client::builder().timeout(Duration::from_secs(300)).build()?;
        let response = client.post("https://api.anthropic.com/v1/messages")
            .header("x-api-key", &api_key).header("anthropic-version", "2023-06-01")
            .json(&body).send()
            .map_err(|e| anyhow!("Anthropic request failed: {}", e))?;
        if !response.status().is_success() {
            let status = response.status();
            let text = response.text().unwrap_or_default();
            return Err(anyhow!("Anthropic returned {}: {}", status, &text[..text.len().min(500)]));
        }
        let val: serde_json::Value = response.json()?;
        val.get("content").and_then(|c| c.get(0)).and_then(|c| c.get("text"))
            .and_then(|t| t.as_str()).map(|s| s.to_string())
            .ok_or_else(|| anyhow!("Unexpected Anthropic response shape"))
    }
}
