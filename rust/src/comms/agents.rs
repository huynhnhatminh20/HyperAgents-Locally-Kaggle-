use anyhow::Result;
use crate::llm::{LlmClient, Message};

// ── helpers ───────────────────────────────────────────────────────────────────

fn word_count(s: &str) -> usize {
    s.split_whitespace().count()
}

fn make_history(system_prompt: &str) -> Vec<Message> {
    vec![Message { role: "system".into(), content: system_prompt.into() }]
}

// ── ExchangeEntry ─────────────────────────────────────────────────────────────

#[derive(Clone)]
pub struct ExchangeEntry {
    pub agent: char,   // 'A' or 'B'
    pub text: String,
}

// ── CommunicatingAgent ────────────────────────────────────────────────────────

pub struct CommunicatingAgent {
    pub name: char,
    client: LlmClient,
    history: Vec<Message>,
    pub tips: Vec<String>,
    pub word_counts: Vec<usize>,
}

impl CommunicatingAgent {
    pub fn new(name: char, model: &str) -> Self {
        Self {
            name,
            client: LlmClient::new(model),
            history: vec![],
            tips: vec![],
            word_counts: vec![],
        }
    }

    /// Reset conversation history for a new round, prepending accumulated tips.
    pub fn start_round(&mut self, system_prompt: &str) {
        let mut full = system_prompt.to_string();
        if !self.tips.is_empty() {
            full.push_str("\n\nOVERSEER TIPS FROM PREVIOUS ROUNDS (apply these now):\n");
            for tip in &self.tips {
                full.push_str(&format!("  • {tip}\n"));
            }
        }
        self.history = make_history(&full);
        self.word_counts.clear();
    }

    /// Send `message` to this agent and return its reply.
    pub fn receive(&mut self, message: &str) -> Result<String> {
        self.history.push(Message { role: "user".into(), content: message.into() });
        let reply = self.client.chat(&self.history)?;
        self.history.push(Message { role: "assistant".into(), content: reply.clone() });
        self.word_counts.push(word_count(&reply));
        Ok(reply)
    }

    pub fn add_tip(&mut self, tip: String) {
        self.tips.push(tip);
    }

    pub fn avg_words(&self) -> f64 {
        if self.word_counts.is_empty() {
            return 0.0;
        }
        self.word_counts.iter().sum::<usize>() as f64 / self.word_counts.len() as f64
    }
}

// ── OverseerAgent ─────────────────────────────────────────────────────────────

const OVERSEER_SYSTEM: &str = "\
You are the Overseer of a two-agent communication experiment.
Your job after each round:

1. READ the full exchange between Agent A and Agent B.
2. SCORE the round's communication efficiency on a scale 1–10 where:
   • 1 = extremely verbose, full of filler, redundancy, hedging
   • 5 = adequate but room to improve
   • 10 = perfectly compressed, every word carries signal, zero waste
3. Give SPECIFIC TIPS to each agent (2–3 bullet points each):
   • Point to exact phrases that were wasteful or unclear
   • Suggest concrete alternatives or structural improvements
   • Encourage developing shorthand, abbreviations, or schemas if appropriate
4. If the task has a verification question, VERIFY whether the information
   was transmitted correctly and completely.

Respond in this exact format:
SCORE: <1–10>
VERDICT: <one sentence on whether information was transmitted correctly>
TIPS FOR AGENT A:
• <tip 1>
• <tip 2>
• <tip 3 if needed>
TIPS FOR AGENT B:
• <tip 1>
• <tip 2>
• <tip 3 if needed>";

pub struct OverseerFeedback {
    pub score: u8,
    pub verdict: String,
    pub tips_a: Vec<String>,
    pub tips_b: Vec<String>,
    pub raw: String,
}

pub struct OverseerAgent {
    client: LlmClient,
    pub scores: Vec<u8>,
}

impl OverseerAgent {
    pub fn new(model: &str) -> Self {
        Self { client: LlmClient::new(model), scores: vec![] }
    }

    pub fn evaluate(
        &mut self,
        exchange_log: &[ExchangeEntry],
        task_context: &str,
        verification_questions: &[&str],
        agent_b_last_reply: &str,
    ) -> Result<OverseerFeedback> {
        let exchange_text: String = exchange_log
            .iter()
            .map(|e| format!("[Agent {}]: {}", e.agent, e.text))
            .collect::<Vec<_>>()
            .join("\n\n");

        let mut parts = vec![];
        if !task_context.is_empty() {
            parts.push(format!("TASK CONTEXT:\n{task_context}"));
        }
        parts.push(format!("EXCHANGE:\n{exchange_text}"));
        if !verification_questions.is_empty() {
            let qs = verification_questions
                .iter()
                .enumerate()
                .map(|(i, q)| format!("  {}. {q}", i + 1))
                .collect::<Vec<_>>()
                .join("\n");
            parts.push(format!(
                "VERIFICATION — check Agent B's replies against these questions:\n{qs}\n\
                 Agent B's last reply: {agent_b_last_reply}"
            ));
        }

        let prompt = parts.join("\n\n");
        let messages = [
            Message { role: "system".into(), content: OVERSEER_SYSTEM.into() },
            Message { role: "user".into(), content: prompt },
        ];

        let raw = self.client.chat(&messages)?;
        let fb = self.parse(&raw);
        self.scores.push(fb.score);
        Ok(fb)
    }

    fn parse(&self, raw: &str) -> OverseerFeedback {
        let mut score: u8 = 5;
        let mut verdict = String::new();
        let mut tips_a: Vec<String> = vec![];
        let mut tips_b: Vec<String> = vec![];
        let mut section = ' ';

        for line in raw.lines() {
            let s = line.trim();
            if let Some(rest) = s.strip_prefix("SCORE:") {
                let digits: String = rest.chars().filter(|c| c.is_ascii_digit()).collect();
                score = digits.parse::<u8>().unwrap_or(5).min(10).max(1);
            } else if let Some(rest) = s.strip_prefix("VERDICT:") {
                verdict = rest.trim().to_string();
            } else if s.to_uppercase().contains("TIPS FOR AGENT A") {
                section = 'A';
            } else if s.to_uppercase().contains("TIPS FOR AGENT B") {
                section = 'B';
            } else if s.starts_with('•') || s.starts_with('-') {
                let tip = s.trim_start_matches(['•', '-', ' ']).trim().to_string();
                if !tip.is_empty() {
                    match section {
                        'A' => tips_a.push(tip),
                        'B' => tips_b.push(tip),
                        _ => {}
                    }
                }
            }
        }

        OverseerFeedback { score, verdict, tips_a, tips_b, raw: raw.to_string() }
    }
}
