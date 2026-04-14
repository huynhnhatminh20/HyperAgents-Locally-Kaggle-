use anyhow::Result;
use chrono::Utc;
use serde_json::{json, Value};
use std::fs;
use std::path::PathBuf;

use crate::comms::agents::{CommunicatingAgent, ExchangeEntry, OverseerAgent, OverseerFeedback};
use crate::comms::tasks::{
    COLLABORATE_SCENARIOS, FREE_TOPICS, PROTOCOL_A_SYSTEM, PROTOCOL_B_SYSTEM,
    PROTOCOL_ROUNDS, RELAY_SCENARIOS,
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
