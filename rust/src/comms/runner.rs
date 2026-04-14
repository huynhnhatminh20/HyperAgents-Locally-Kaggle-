use anyhow::Result;
use chrono::Utc;
use serde_json::{json, Value};
use std::fs;
use std::path::PathBuf;

use crate::comms::agents::{CommunicatingAgent, ExchangeEntry, OverseerAgent, OverseerFeedback};
use crate::comms::tasks::{
    COLLABORATE_SCENARIOS, FREE_TOPICS, LANGUAGE_A_BOOTSTRAP, LANGUAGE_A_ENCODE,
    LANGUAGE_B_BOOTSTRAP, LANGUAGE_B_DECODE, LANGUAGE_SCENARIOS,
    PROTOCOL_A_SYSTEM, PROTOCOL_B_SYSTEM, PROTOCOL_ROUNDS, RELAY_SCENARIOS,
};

// ── ANSI colours ──────────────────────────────────────────────────────────────

const RESET: &str = "\x1b[0m";
const BOLD: &str = "\x1b[1m";
const DIM: &str = "\x1b[2m";
const CYAN: &str = "\x1b[96m";
const GREEN: &str = "\x1b[92m";
const YELLOW: &str = "\x1b[93m";
const MAGENTA: &str = "\x1b[95m";
const RED: &str = "\x1b[91m";

fn c(text: &str, codes: &[&str]) -> String {
    format!("{}{text}{RESET}", codes.join(""))
}

fn banner(title: &str) -> String {
    let width = 72usize;
    let inner = format!(" {title} ");
    let total_pad = width.saturating_sub(inner.len());
    let left = total_pad / 2;
    let right = total_pad - left;
    c(&format!("{}{inner}{}", "═".repeat(left), "═".repeat(right)), &[BOLD])
}

fn section(title: &str) -> String {
    let dashes = "─".repeat(60usize.saturating_sub(title.len() + 4));
    c(&format!("── {title} {dashes}"), &[DIM])
}

fn print_msg(from: char, to: char, text: &str, color: &str) {
    let words = text.split_whitespace().count();
    let header = format!(
        "{} → {}  {}",
        c(&format!("Agent {from}"), &[BOLD, color]),
        c(&format!("Agent {to}"), &[DIM]),
        c(&format!("[{words}w]"), &[DIM])
    );
    println!("\n{header}");
    // simple word-wrap at ~88 chars
    let mut line_len = 0usize;
    let mut buf = String::new();
    for word in text.split_whitespace() {
        if line_len + word.len() + 1 > 88 {
            println!("{}{buf}{RESET}", color);
            buf.clear();
            line_len = 0;
        }
        if !buf.is_empty() {
            buf.push(' ');
            line_len += 1;
        }
        buf.push_str(word);
        line_len += word.len();
    }
    if !buf.is_empty() {
        println!("{}{buf}{RESET}", color);
    }
}

fn print_overseer(fb: &OverseerFeedback, scores: &[u8]) {
    let score_color = if fb.score >= 7 { GREEN } else if fb.score >= 4 { YELLOW } else { RED };
    let bar = format!(
        "{}{}",
        "█".repeat(fb.score as usize),
        "░".repeat((10 - fb.score) as usize)
    );
    println!("\n{}", section("OVERSEER"));
    println!(
        "  Score: {}/10  {}",
        c(&fb.score.to_string(), &[BOLD, score_color]),
        c(&bar, &[score_color])
    );
    if !fb.verdict.is_empty() {
        println!("  {}", c(&fb.verdict, &[DIM]));
    }
    if !fb.tips_a.is_empty() {
        println!("\n  {}", c("Tips for Agent A:", &[BOLD, CYAN]));
        for tip in &fb.tips_a {
            println!("    {} {tip}", c("•", &[CYAN]));
        }
    }
    if !fb.tips_b.is_empty() {
        println!("\n  {}", c("Tips for Agent B:", &[BOLD, MAGENTA]));
        for tip in &fb.tips_b {
            println!("    {} {tip}", c("•", &[MAGENTA]));
        }
    }
    if scores.len() > 1 {
        let history: String = scores
            .iter()
            .map(|s| {
                let col = if *s >= 7 { GREEN } else if *s >= 4 { YELLOW } else { RED };
                c(&s.to_string(), &[col])
            })
            .collect::<Vec<_>>()
            .join("  ");
        let last = *scores.last().unwrap();
        let prev = scores[scores.len() - 2];
        let (trend, tcol) = if last > prev {
            ("↑", GREEN)
        } else if last < prev {
            ("↓", RED)
        } else {
            ("→", DIM)
        };
        println!(
            "\n  Score history: {}  {}",
            history,
            c(trend, &[BOLD, tcol])
        );
    }
}

// ── Config ────────────────────────────────────────────────────────────────────

pub struct CommsConfig {
    pub task: String,
    pub agent_model: String,
    pub overseer_model: String,
    pub rounds: usize,
    pub exchanges: usize,
    pub scenario_idx: usize,
    pub topic: Option<String>,
    pub output_dir: PathBuf,
}

// ── Main entry point ──────────────────────────────────────────────────────────

pub fn run(cfg: CommsConfig) -> Result<PathBuf> {
    let ts = Utc::now().format("%Y%m%d_%H%M%S");
    let run_dir = cfg.output_dir.join(format!("comms_{}_{}", cfg.task, ts));
    fs::create_dir_all(&run_dir)?;

    println!("{}", banner("AGENT COMMS — Self-Optimising Communication Loop"));
    println!("  Task:           {}", c(&cfg.task.to_uppercase(), &[BOLD]));
    println!("  Agent model:    {}", c(&cfg.agent_model, &[BOLD]));
    println!("  Overseer model: {}", c(&cfg.overseer_model, &[BOLD]));
    println!("  Rounds:         {}", cfg.rounds);
    println!("  Exchanges/rnd:  {}", cfg.exchanges);
    println!();

    let mut agent_a = CommunicatingAgent::new('A', &cfg.agent_model);
    let mut agent_b = CommunicatingAgent::new('B', &cfg.agent_model);
    let mut overseer = OverseerAgent::new(&cfg.overseer_model);
    let mut log: Vec<Value> = vec![];

    match cfg.task.as_str() {
        "relay" => {
            let scenarios = RELAY_SCENARIOS;
            let scenario = &scenarios[cfg.scenario_idx % scenarios.len()];
            println!("  {}", c(&format!("Scenario: {}", scenario.id), &[DIM]));
            println!("  {}", c("Goal: relay dense facts, overseer quizzes Agent B.", &[DIM]));
            println!();
            run_relay(
                &mut agent_a, &mut agent_b, &mut overseer,
                scenario.id, scenario.a_briefing, scenario.b_briefing,
                scenario.quiz_questions,
                cfg.rounds, cfg.exchanges, &mut log,
            )?;
        }
        "collaborate" => {
            let scenarios = COLLABORATE_SCENARIOS;
            let scenario = &scenarios[cfg.scenario_idx % scenarios.len()];
            println!("  {}", c(&format!("Scenario: {}", scenario.id), &[DIM]));
            println!("  {}", c(&format!("Goal: {}", scenario.joint_goal), &[DIM]));
            println!();
            run_collaborate(
                &mut agent_a, &mut agent_b, &mut overseer,
                scenario.id, scenario.a_briefing, scenario.b_briefing,
                scenario.joint_goal,
                cfg.rounds, cfg.exchanges, &mut log,
            )?;
        }
        "protocol" => {
            println!("  {}", c("Goal: develop compressed notation across rounds.", &[DIM]));
            println!();
            run_protocol(
                &mut agent_a, &mut agent_b, &mut overseer,
                cfg.rounds, &mut log,
            )?;
        }
        "language" => {
            let scenarios = LANGUAGE_SCENARIOS;
            let scenario = &scenarios[cfg.scenario_idx % scenarios.len()];
            println!("  {}", c(&format!("Scenario: {}  (domain: {})", scenario.id, scenario.domain), &[DIM]));
            println!("  {}", c("Goal: invent a shared symbol language; encode/decode messages.", &[DIM]));
            println!();
            run_language(
                &mut agent_a, &mut agent_b, &mut overseer,
                scenario, cfg.rounds, &mut log,
            )?;
        }
        "free" | _ => {
            let topic = cfg.topic.clone().unwrap_or_else(|| {
                let idx = (Utc::now().timestamp() as usize) % FREE_TOPICS.len();
                println!("  {}", c("(random topic selected)", &[DIM]));
                FREE_TOPICS[idx].to_string()
            });
            println!("  {}", c(&format!("Topic: {topic}"), &[DIM]));
            println!();
            run_free(
                &mut agent_a, &mut agent_b, &mut overseer,
                &topic, cfg.rounds, cfg.exchanges, &mut log,
            )?;
        }
    }

    // ── final summary ──
    print_final_summary(&overseer.scores);

    // ── save session ──
    let session = json!({
        "task": cfg.task,
        "agent_model": cfg.agent_model,
        "overseer_model": cfg.overseer_model,
        "rounds": cfg.rounds,
        "scores": overseer.scores,
        "log": log,
    });
    let out_path = run_dir.join("session.json");
    fs::write(&out_path, serde_json::to_string_pretty(&session)?)?;
    println!("  Output saved to: {}", c(out_path.to_str().unwrap_or("?"), &[BOLD]));
    println!();

    Ok(run_dir)
}

// ── relay ─────────────────────────────────────────────────────────────────────

fn run_relay(
    agent_a: &mut CommunicatingAgent,
    agent_b: &mut CommunicatingAgent,
    overseer: &mut OverseerAgent,
    scenario_id: &str,
    a_briefing: &str,
    b_briefing: &str,
    quiz_questions: &[&str],
    rounds: usize,
    exchanges: usize,
    log: &mut Vec<Value>,
) -> Result<()> {
    println!("{}", c(&format!("Task: RELAY  |  Scenario: {scenario_id}"), &[BOLD]));
    println!();

    for rnd in 1..=rounds {
        println!("{}", banner(&format!("Round {rnd} / {rounds}")));

        let a_sys = format!(
            "You are Agent A in a communication efficiency experiment.\n\n\
             YOUR TASK:\n{a_briefing}\n\n\
             Relay the above information to Agent B as efficiently as possible. \
             Every word costs — eliminate filler, hedging, and repetition. \
             Use shorthand, bullet points, or any compression you and B agree on."
        );
        let b_sys = format!(
            "You are Agent B in a communication efficiency experiment.\n\n\
             YOUR ROLE:\n{b_briefing}\n\n\
             Receive information from Agent A. Ask focused clarifying questions \
             only if something is genuinely missing. Acknowledge receipt concisely."
        );

        agent_a.start_round(&a_sys);
        agent_b.start_round(&b_sys);

        let mut exchange_log: Vec<ExchangeEntry> = vec![];

        // A sends the briefing
        let relay_msg = format!("[round {rnd}] {}", a_briefing.trim());
        print_msg('A', 'B', &relay_msg, CYAN);
        exchange_log.push(ExchangeEntry { agent: 'A', text: relay_msg.clone() });

        let mut last_msg = relay_msg;
        for _ex in 0..exchanges {
            let reply_b = agent_b.receive(&last_msg)?;
            print_msg('B', 'A', &reply_b, MAGENTA);
            exchange_log.push(ExchangeEntry { agent: 'B', text: reply_b.clone() });

            let reply_a = agent_a.receive(&reply_b)?;
            print_msg('A', 'B', &reply_a, CYAN);
            exchange_log.push(ExchangeEntry { agent: 'A', text: reply_a.clone() });
            last_msg = reply_a;
        }

        let b_last = exchange_log.iter().rfind(|e| e.agent == 'B').map(|e| e.text.as_str()).unwrap_or("");
        let fb = overseer.evaluate(&exchange_log, scenario_id, quiz_questions, b_last)?;
        print_overseer(&fb, &overseer.scores);

        agent_a.add_tip(format!("Round {rnd}: {}", fb.tips_a.join("; ")));
        agent_b.add_tip(format!("Round {rnd}: {}", fb.tips_b.join("; ")));

        log.push(json!({
            "round": rnd,
            "scenario": scenario_id,
            "exchange": exchange_log.iter().map(|e| json!({"agent": e.agent.to_string(), "text": e.text})).collect::<Vec<_>>(),
            "score": fb.score,
            "verdict": fb.verdict,
            "tips_a": fb.tips_a,
            "tips_b": fb.tips_b,
        }));
        println!();
    }
    Ok(())
}

// ── collaborate ───────────────────────────────────────────────────────────────

fn run_collaborate(
    agent_a: &mut CommunicatingAgent,
    agent_b: &mut CommunicatingAgent,
    overseer: &mut OverseerAgent,
    scenario_id: &str,
    a_briefing: &str,
    b_briefing: &str,
    joint_goal: &str,
    rounds: usize,
    exchanges: usize,
    log: &mut Vec<Value>,
) -> Result<()> {
    println!("{}", c(&format!("Task: COLLABORATE  |  Scenario: {scenario_id}"), &[BOLD]));
    println!();

    for rnd in 1..=rounds {
        println!("{}", banner(&format!("Round {rnd} / {rounds}")));

        let a_sys = format!(
            "You are Agent A in a collaborative information-sharing experiment.\n\n\
             YOUR PRIVATE INFORMATION:\n{a_briefing}\n\n\
             Share your information with Agent B efficiently. Together you must: \
             {joint_goal}\n\
             Be concise — every redundant word wastes a turn. \
             Work toward a joint answer the overseer can verify."
        );
        let b_sys = format!(
            "You are Agent B in a collaborative information-sharing experiment.\n\n\
             YOUR PRIVATE INFORMATION:\n{b_briefing}\n\n\
             Share your information with Agent A efficiently. Together you must: \
             {joint_goal}\n\
             Be concise — every redundant word wastes a turn. \
             Once you have enough information, produce the joint answer."
        );

        agent_a.start_round(&a_sys);
        agent_b.start_round(&b_sys);

        let mut exchange_log: Vec<ExchangeEntry> = vec![];
        let opener = "Let's share our information and compute the joint answer.";

        // A goes first
        let share_a = agent_a.receive(opener)?;
        print_msg('A', 'B', &share_a, CYAN);
        exchange_log.push(ExchangeEntry { agent: 'A', text: share_a.clone() });

        let mut last_msg = share_a;
        for _ex in 0..exchanges {
            let reply_b = agent_b.receive(&last_msg)?;
            print_msg('B', 'A', &reply_b, MAGENTA);
            exchange_log.push(ExchangeEntry { agent: 'B', text: reply_b.clone() });

            let reply_a = agent_a.receive(&reply_b)?;
            print_msg('A', 'B', &reply_a, CYAN);
            exchange_log.push(ExchangeEntry { agent: 'A', text: reply_a.clone() });
            last_msg = reply_a;
        }

        let b_last = exchange_log.iter().rfind(|e| e.agent == 'B').map(|e| e.text.as_str()).unwrap_or("");
        let fb = overseer.evaluate(
            &exchange_log,
            &format!("Collaborative scenario: {scenario_id}\nJoint goal: {joint_goal}"),
            &[joint_goal],
            b_last,
        )?;
        print_overseer(&fb, &overseer.scores);

        agent_a.add_tip(format!("Round {rnd}: {}", fb.tips_a.join("; ")));
        agent_b.add_tip(format!("Round {rnd}: {}", fb.tips_b.join("; ")));

        log.push(json!({
            "round": rnd,
            "scenario": scenario_id,
            "exchange": exchange_log.iter().map(|e| json!({"agent": e.agent.to_string(), "text": e.text})).collect::<Vec<_>>(),
            "score": fb.score,
            "verdict": fb.verdict,
        }));
        println!();
    }
    Ok(())
}

// ── protocol ──────────────────────────────────────────────────────────────────

fn run_protocol(
    agent_a: &mut CommunicatingAgent,
    agent_b: &mut CommunicatingAgent,
    overseer: &mut OverseerAgent,
    rounds: usize,
    log: &mut Vec<Value>,
) -> Result<()> {
    println!("{}", c("Task: PROTOCOL — develop compressed notation across rounds", &[BOLD]));
    println!();

    let mut developed: Vec<String> = vec![];

    for rnd in 1..=rounds {
        let data = &PROTOCOL_ROUNDS[(rnd - 1) % PROTOCOL_ROUNDS.len()];
        println!("{}", banner(&format!("Round {rnd} / {rounds}  [{}]", data.project)));

        let proto_note = if developed.is_empty() {
            String::new()
        } else {
            format!(
                "\n\nPROTOCOL DEVELOPED SO FAR (use and extend this):\n{}",
                developed.iter().map(|p| format!("  {p}")).collect::<Vec<_>>().join("\n")
            )
        };

        agent_a.start_round(&format!("{PROTOCOL_A_SYSTEM}{proto_note}"));
        agent_b.start_round(&format!("{PROTOCOL_B_SYSTEM}{proto_note}"));

        let blocker_str = data.blocker.unwrap_or("none");
        let data_text = format!(
            "project={} status={} blocker={} priority={} eta_days={} owner={} pct={}",
            data.project, data.status, blocker_str,
            data.priority, data.eta_days, data.owner, data.completion_pct
        );
        let a_prompt = format!(
            "New data to relay (round {rnd}):\n{data_text}\n\nSend this to Agent B as compactly as possible."
        );

        let mut exchange_log: Vec<ExchangeEntry> = vec![];

        let msg_a = agent_a.receive(&a_prompt)?;
        print_msg('A', 'B', &msg_a, CYAN);
        exchange_log.push(ExchangeEntry { agent: 'A', text: msg_a.clone() });

        let b_prompt = format!(
            "{msg_a}\n\n[Reconstruct the full report from Agent A's message above.]"
        );
        let reply_b = agent_b.receive(&b_prompt)?;
        print_msg('B', 'A', &reply_b, MAGENTA);
        exchange_log.push(ExchangeEntry { agent: 'B', text: reply_b.clone() });

        let vqs = [
            "What is the project name?",
            "What is the status?",
            "What is the completion percentage?",
            "Who is the owner?",
            "What is the ETA in days?",
        ];
        let task_ctx = format!(
            "Protocol compression task. Original data:\n{data_text}"
        );
        let fb = overseer.evaluate(&exchange_log, &task_ctx, &vqs, &reply_b)?;
        print_overseer(&fb, &overseer.scores);

        // collect any shorthand suggestions from overseer
        for tip in fb.tips_a.iter().chain(fb.tips_b.iter()) {
            let tl = tip.to_lowercase();
            if ["shorthand", "abbreviat", "schema", "notation", "code", "prefix", "symbol"]
                .iter()
                .any(|kw| tl.contains(kw))
            {
                developed.push(tip.clone());
            }
        }

        let words_a: usize = exchange_log.iter()
            .filter(|e| e.agent == 'A')
            .map(|e| e.text.split_whitespace().count())
            .sum();
        println!("\n  {} {words_a}", c("Words used by A this round:", &[DIM]));

        agent_a.add_tip(format!("Round {rnd}: {}", fb.tips_a.join("; ")));
        agent_b.add_tip(format!("Round {rnd}: {}", fb.tips_b.join("; ")));

        log.push(json!({
            "round": rnd,
            "project": data.project,
            "exchange": exchange_log.iter().map(|e| json!({"agent": e.agent.to_string(), "text": e.text})).collect::<Vec<_>>(),
            "score": fb.score,
            "words_a": words_a,
        }));
        println!();
    }
    Ok(())
}

// ── free ──────────────────────────────────────────────────────────────────────

fn run_free(
    agent_a: &mut CommunicatingAgent,
    agent_b: &mut CommunicatingAgent,
    overseer: &mut OverseerAgent,
    topic: &str,
    rounds: usize,
    exchanges: usize,
    log: &mut Vec<Value>,
) -> Result<()> {
    println!("{}", c("Task: FREE DISCUSSION", &[BOLD]));
    println!();

    let base = format!(
        "You are one of two AI agents having an efficient discussion about:\n\
         \"{topic}\"\n\n\
         Your goal: exchange maximum insight in minimum words. \
         Cut hedging ('I think', 'it seems', 'perhaps'), cut filler, \
         cut repetition of what the other agent already said. \
         Make every sentence carry new information or a new argument."
    );

    for rnd in 1..=rounds {
        println!("{}", banner(&format!("Round {rnd} / {rounds}")));

        agent_a.start_round(&format!("You are Agent A. {base}"));
        agent_b.start_round(&format!("You are Agent B. {base}"));

        let mut exchange_log: Vec<ExchangeEntry> = vec![];
        let mut last_msg = format!("Topic: {topic}");

        for _ex in 0..exchanges {
            let reply_a = agent_a.receive(&last_msg)?;
            print_msg('A', 'B', &reply_a, CYAN);
            exchange_log.push(ExchangeEntry { agent: 'A', text: reply_a.clone() });

            let reply_b = agent_b.receive(&reply_a)?;
            print_msg('B', 'A', &reply_b, MAGENTA);
            exchange_log.push(ExchangeEntry { agent: 'B', text: reply_b.clone() });
            last_msg = reply_b;
        }

        let fb = overseer.evaluate(
            &exchange_log,
            &format!("Free discussion topic: {topic}"),
            &[],
            "",
        )?;
        print_overseer(&fb, &overseer.scores);

        agent_a.add_tip(format!("Round {rnd}: {}", fb.tips_a.join("; ")));
        agent_b.add_tip(format!("Round {rnd}: {}", fb.tips_b.join("; ")));

        log.push(json!({
            "round": rnd,
            "topic": topic,
            "exchange": exchange_log.iter().map(|e| json!({"agent": e.agent.to_string(), "text": e.text})).collect::<Vec<_>>(),
            "score": fb.score,
            "verdict": fb.verdict,
        }));
        println!();
    }
    Ok(())
}

// ── language ──────────────────────────────────────────────────────────────────

/// Parse "sym = meaning" or "sym: meaning" lines out of agent messages to build
/// a cumulative lexicon that survives across rounds.
fn extract_lexicon_lines(text: &str) -> Vec<String> {
    let mut entries: Vec<String> = Vec::new();
    let mut in_block = false;
    for line in text.lines() {
        let s = line.trim();
        // section headers that start a lexicon block
        let upper = s.to_uppercase();
        if upper.starts_with("LEXICON") || upper.starts_with("NEW SYMBOLS") {
            in_block = true;
            continue;
        }
        // inline "NEW: sym = meaning"
        if upper.starts_with("NEW:") {
            let rest = s[4..].trim();
            if rest.contains('=') || rest.contains(':') {
                let e = rest.replace(':', " = ").trim().to_string();
                if !e.is_empty() && !entries.contains(&e) {
                    entries.push(e);
                }
            }
            continue;
        }
        // blank line ends the block
        if in_block && s.is_empty() {
            in_block = false;
            continue;
        }
        if in_block {
            // stop if we hit a new heading-like line that isn't an entry
            if s.len() > 60 && !s.contains('=') {
                in_block = false;
                continue;
            }
            let cleaned = s.trim_start_matches(['-', '•', '*', ' ']);
            if cleaned.contains('=') || cleaned.contains(':') {
                let e = cleaned.replace(':', " = ").trim().to_string();
                if !e.is_empty() && e.len() < 80 && !entries.contains(&e) {
                    entries.push(e);
                }
            }
        }
    }
    entries
}

fn lexicon_string(entries: &[String]) -> String {
    if entries.is_empty() {
        "(none yet)".to_string()
    } else {
        entries.iter().map(|e| format!("  {e}")).collect::<Vec<_>>().join("\n")
    }
}

fn print_lexicon(entries: &[String]) {
    const BLUE: &str = "\x1b[94m";
    println!("\n{}", section("LEXICON"));
    if entries.is_empty() {
        println!("  {}", c("(none yet)", &[DIM]));
    } else {
        for e in entries {
            println!("  {}{e}{RESET}", BLUE);
        }
    }
}

/// Free evolution round data — generated on the fly after scripted rounds are done.
struct FreeRound {
    concept_label: String,
    message: String,
    expected_meaning: String,
}

/// Ask the overseer to propose the next evolution challenge, then run it.
fn make_free_round(
    overseer: &mut OverseerAgent,
    domain: &str,
    lexicon: &[String],
    rnd: usize,
) -> Result<FreeRound> {
    let lex_str = lexicon_string(lexicon);
    let prompt = format!(
        "You are the curator of an emergent language experiment (domain: {domain}).\n\
         The agents have built this lexicon so far:\n{lex_str}\n\n\
         Design the next encoding challenge (round {rnd}).\n\
         - Choose a NEW concept cluster not yet in the lexicon that fits the domain\n\
         - Write a concrete message for Agent A to encode (10-20 natural-language words)\n\
         - Write the ground-truth meaning for verification\n\n\
         Respond in EXACTLY this format (no extra text):\n\
         CONCEPT_LABEL: <short label, e.g. \"emotions + reactions\">\n\
         MESSAGE: <the message Agent A must encode>\n\
         EXPECTED: <the ground-truth meaning for the overseer>"
    );
    let messages = [
        crate::llm::Message { role: "user".into(), content: prompt },
    ];
    let raw = overseer.client.chat(&messages)?;

    let mut concept_label = format!("free evolution round {rnd}");
    let mut message = String::new();
    let mut expected_meaning = String::new();
    for line in raw.lines() {
        if let Some(v) = line.strip_prefix("CONCEPT_LABEL:") { concept_label = v.trim().to_string(); }
        if let Some(v) = line.strip_prefix("MESSAGE:")       { message = v.trim().to_string(); }
        if let Some(v) = line.strip_prefix("EXPECTED:")      { expected_meaning = v.trim().to_string(); }
    }
    if message.is_empty() { message = format!("(round {rnd} — free evolution in domain {domain})"); }
    if expected_meaning.is_empty() { expected_meaning = message.clone(); }
    Ok(FreeRound { concept_label, message, expected_meaning })
}

fn run_language(
    agent_a: &mut CommunicatingAgent,
    agent_b: &mut CommunicatingAgent,
    overseer: &mut OverseerAgent,
    scenario: &crate::comms::tasks::LanguageScenario,
    total_rounds: usize,
    log: &mut Vec<Value>,
) -> Result<()> {
    println!("{}", c(
        &format!("Task: LANGUAGE  |  Scenario: {}  |  Domain: {}", scenario.id, scenario.domain),
        &[BOLD],
    ));
    let scripted = scenario.rounds.len();
    let extra = total_rounds.saturating_sub(scripted);
    if extra > 0 {
        println!("  {} scripted rounds + {} free-evolution rounds = {} total",
            c(&scripted.to_string(), &[BOLD]),
            c(&extra.to_string(), &[BOLD, YELLOW]),
            c(&total_rounds.to_string(), &[BOLD]),
        );
    }
    println!();

    let mut lexicon: Vec<String> = vec![];

    for rnd in 1..=total_rounds {
        let is_bootstrap = rnd == 1;
        let is_scripted  = rnd <= scripted;

        // ── pick round data (scripted or generated) ──
        let (concept_label, message, expected_meaning);
        let free_buf: FreeRound;  // keep alive for the whole iteration

        if is_scripted {
            let d = &scenario.rounds[rnd - 1];
            concept_label  = d.concept_label;
            message        = d.message;
            expected_meaning = d.expected_meaning;
        } else {
            print!("\n  {} generating free-evolution challenge…", c("Overseer:", &[DIM, YELLOW]));
            free_buf = make_free_round(overseer, scenario.domain, &lexicon, rnd)?;
            println!("  {}", c(&format!("concepts: {}", free_buf.concept_label), &[DIM]));
            concept_label    = free_buf.concept_label.as_str();
            message          = free_buf.message.as_str();
            expected_meaning = free_buf.expected_meaning.as_str();
        };

        let phase = if is_scripted { "scripted" } else { "evolved" };
        println!("{}", banner(&format!(
            "Round {rnd} / {total_rounds}  [{phase}]  ·  {concept_label}"
        )));

        let lex_str = lexicon_string(&lexicon);

        let (a_sys, b_sys) = if is_bootstrap {
            (
                LANGUAGE_A_BOOTSTRAP
                    .replace("{DOMAIN}", scenario.domain)
                    .replace("{CONCEPTS}", concept_label)
                    .replace("{MESSAGE}", message),
                LANGUAGE_B_BOOTSTRAP
                    .replace("{DOMAIN}", scenario.domain)
                    .replace("{CONCEPTS}", concept_label)
                    .replace("{MESSAGE}", message),
            )
        } else {
            (
                LANGUAGE_A_ENCODE
                    .replace("{DOMAIN}", scenario.domain)
                    .replace("{CONCEPTS}", concept_label)
                    .replace("{LEXICON}", &lex_str)
                    .replace("{MESSAGE}", message),
                LANGUAGE_B_DECODE
                    .replace("{DOMAIN}", scenario.domain)
                    .replace("{CONCEPTS}", concept_label)
                    .replace("{LEXICON}", &lex_str),
            )
        };

        agent_a.start_round(&a_sys);
        agent_b.start_round(&b_sys);

        let mut exchange_log: Vec<ExchangeEntry> = vec![];

        // ── Agent A goes first ──
        let a_opener = if is_bootstrap {
            format!(
                "Let's invent our symbol language for domain '{}'.\n\
                 Concepts this round: {concept_label}\n\
                 Message we need to encode: \"{message}\"",
                scenario.domain,
            )
        } else {
            format!("Encode this message using our lexicon: \"{message}\"")
        };

        let msg_a = agent_a.receive(&a_opener)?;
        print_msg('A', 'B', &msg_a, CYAN);
        exchange_log.push(ExchangeEntry { agent: 'A', text: msg_a.clone() });

        // ── Agent B responds ──
        let msg_b = agent_b.receive(&msg_a)?;
        print_msg('B', 'A', &msg_b, MAGENTA);
        exchange_log.push(ExchangeEntry { agent: 'B', text: msg_b.clone() });

        // ── Bootstrap: one more A→B to finalise & emit test encode ──
        if is_bootstrap {
            let finalise = "Good. Please emit the final agreed LEXICON block, \
                then encode the test message using only our new symbols.";
            let final_a = agent_a.receive(finalise)?;
            print_msg('A', 'B', &final_a, CYAN);
            exchange_log.push(ExchangeEntry { agent: 'A', text: final_a.clone() });

            let final_b = agent_b.receive(&final_a)?;
            print_msg('B', 'A', &final_b, MAGENTA);
            exchange_log.push(ExchangeEntry { agent: 'B', text: final_b.clone() });

            // Harvest lexicon from this round
            for entry in exchange_log.iter() {
                for new_e in extract_lexicon_lines(&entry.text) {
                    if !lexicon.contains(&new_e) {
                        lexicon.push(new_e);
                    }
                }
            }
        } else {
            // Harvest any NEW: declarations from A's message
            for new_e in extract_lexicon_lines(&msg_a) {
                if !lexicon.contains(&new_e) {
                    lexicon.push(new_e);
                }
            }
        }

        print_lexicon(&lexicon);

        // ── Measure compression ──
        let a_symbol_msg = exchange_log.iter()
            .filter(|e| e.agent == 'A')
            .last()
            .map(|e| e.text.as_str())
            .unwrap_or("");
        let a_tokens: usize = a_symbol_msg.split_whitespace().count();
        let natural_tokens: usize = message.split_whitespace().count();
        let ratio_pct = if natural_tokens > 0 {
            (a_tokens * 100) / natural_tokens
        } else { 100 };

        if !is_bootstrap {
            let ratio_col = if ratio_pct <= 50 { GREEN } else if ratio_pct <= 80 { YELLOW } else { RED };
            println!(
                "\n  {} {} tokens  (natural: {} tokens — {}% of original)",
                c("A's encoding:", &[DIM]),
                c(&a_tokens.to_string(), &[BOLD]),
                natural_tokens,
                c(&ratio_pct.to_string(), &[BOLD, ratio_col]),
            );
        }

        // ── Overseer ──
        let task_ctx = format!(
            "EMERGENT LANGUAGE EXPERIMENT\n\
             Domain: {}\n\
             Round {rnd} — concepts: {concept_label}\n\
             Original message to encode: \"{message}\"\n\
             Expected meaning: \"{expected_meaning}\"\n\
             Established lexicon:\n{lex_str}",
            scenario.domain,
        );

        let vqs: &[&str] = if is_bootstrap {
            &[
                "Did the agents agree on a clear, unambiguous lexicon?",
                "Are all required concepts covered by symbols?",
                "Is each symbol short (1-3 chars) and distinct?",
                "Did Agent B correctly decode the test message?",
            ]
        } else {
            &[
                "Did Agent B correctly decode the meaning?",
                "Did Agent A use ONLY symbols (no natural language sentences)?",
                "Were new concepts handled with new symbol declarations?",
                "Is the encoding compact relative to natural language?",
            ]
        };

        let b_last = exchange_log.iter()
            .rfind(|e| e.agent == 'B')
            .map(|e| e.text.as_str())
            .unwrap_or("");
        let fb = overseer.evaluate(&exchange_log, &task_ctx, vqs, b_last)?;
        print_overseer(&fb, &overseer.scores);

        agent_a.add_tip(format!("Round {rnd}: {}", fb.tips_a.join("; ")));
        agent_b.add_tip(format!("Round {rnd}: {}", fb.tips_b.join("; ")));

        log.push(json!({
            "round": rnd,
            "phase": phase,
            "scenario": scenario.id,
            "domain": scenario.domain,
            "concepts": concept_label,
            "message": message,
            "lexicon_size": lexicon.len(),
            "lexicon": lexicon,
            "compression_pct": ratio_pct,
            "exchange": exchange_log.iter().map(|e| json!({"agent": e.agent.to_string(), "text": e.text})).collect::<Vec<_>>(),
            "score": fb.score,
            "verdict": fb.verdict,
        }));
        println!();
    }

    // ── final lexicon printout ──
    println!("{}", banner("FINAL LEXICON"));
    print_lexicon(&lexicon);
    println!();

    Ok(())
}

// ── final summary ─────────────────────────────────────────────────────────────

fn print_final_summary(scores: &[u8]) {
    println!("{}", banner("FINAL SUMMARY"));
    if scores.is_empty() {
        return;
    }
    let avg = scores.iter().map(|s| *s as f64).sum::<f64>() / scores.len() as f64;
    let best = scores.iter().max().copied().unwrap_or(0);
    let trend = scores.last().copied().unwrap_or(0) as i32
        - scores.first().copied().unwrap_or(0) as i32;
    let trend_str = if trend > 0 {
        c(&format!("+{trend} improvement!"), &[BOLD, GREEN])
    } else if trend < 0 {
        c(&format!("{trend} (no gain)"), &[BOLD, RED])
    } else {
        c("→ steady", &[DIM])
    };

    println!();
    println!("  Rounds:      {}", scores.len());
    println!(
        "  Scores:      {}",
        scores.iter().map(|s| s.to_string()).collect::<Vec<_>>().join(" → ")
    );
    println!("  Avg score:   {avg:.1}/10");
    println!("  Best round:  {best}/10");
    println!("  Trend:       {trend_str}");
    println!();
    println!("  Score chart:");
    for (i, s) in scores.iter().enumerate() {
        let col = if *s >= 7 { GREEN } else if *s >= 4 { YELLOW } else { RED };
        let bar = format!("{}{}", "█".repeat(*s as usize), "░".repeat((10 - s) as usize));
        println!("    Round {:>2}  {}  {}/10", i + 1, c(&bar, &[col]), s);
    }
    println!();
}
