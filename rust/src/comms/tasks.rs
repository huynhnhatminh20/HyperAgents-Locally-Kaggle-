/// Task and scenario definitions for the agent-to-agent communication loop.

// ── Relay ─────────────────────────────────────────────────────────────────────

pub struct RelayScenario {
    pub id: &'static str,
    pub a_briefing: &'static str,
    pub b_briefing: &'static str,
    pub quiz_questions: &'static [&'static str],
}

pub const RELAY_SCENARIOS: &[RelayScenario] = &[
    RelayScenario {
        id: "relay_001",
        a_briefing: "\
PROJECT BRIEF — relay this to Agent B as efficiently as possible:

• Project: Phoenix API integration
• Deadline moved: Q3 → Q2 (April 30)
• Budget cut: $1.2M → $840K (−30 %)
• Team lead Sarah on medical leave until March 15; deputy = Marcus (handles approvals)
• Client: TechCorp — weekly status reports every Monday 09:00
• Deliverables: 3 REST endpoints — /auth, /data, /export
• Staging env: staging.techcorp.io:8443
• Credentials: Vault path /secret/techcorp/staging
• Blocker: rate-limit on /data endpoint (max 100 req/min); needs caching layer",
        b_briefing: "You are receiving a project briefing from Agent A. \
Listen carefully — the overseer will quiz you on specific details.",
        quiz_questions: &[
            "What is the new project deadline (exact date)?",
            "What is the budget after the cut?",
            "Who approves changes while Sarah is away?",
            "What is the staging server hostname and port?",
            "What is the rate limit on /data and what is the proposed fix?",
        ],
    },
    RelayScenario {
        id: "relay_002",
        a_briefing: "\
INCIDENT REPORT — relay this to Agent B:

• Service: payments-gateway (prod)
• Started: 2026-04-14 03:17 UTC
• Impact: 23 % of checkout requests failing with HTTP 503
• Root cause: DB connection pool exhausted (max=50, current=50/50)
• Triggered by: marketing email sent at 03:00 — 8× traffic spike
• Fix applied: pool size raised to 150, deployed 04:02 UTC
• Recovery: error rate back to 0.3 % by 04:11 UTC
• Action items: (1) auto-scaling rule for pool, (2) load-test before next campaign
• On-call owner: Diego Reyes — paged at 03:22, responded 03:28",
        b_briefing: "You are receiving an incident report from Agent A. \
The overseer will ask you specific questions about the incident.",
        quiz_questions: &[
            "What time did the incident start (UTC)?",
            "What percentage of requests were failing?",
            "What was the root cause?",
            "What triggered the traffic spike?",
            "Who was the on-call engineer and when did they respond?",
        ],
    },
];

// ── Collaborate ───────────────────────────────────────────────────────────────

pub struct CollaborateScenario {
    pub id: &'static str,
    pub a_briefing: &'static str,
    pub b_briefing: &'static str,
    pub joint_goal: &'static str,
}

pub const COLLABORATE_SCENARIOS: &[CollaborateScenario] = &[
    CollaborateScenario {
        id: "collab_001",
        a_briefing: "\
You know the ODD-indexed clues (1, 3, 5) to a treasure location:
  Clue 1: Start at the old lighthouse on Mercer Island.
  Clue 3: From the red oak, walk exactly 40 paces due north.
  Clue 5: Dig 30 cm below the surface at a spot marked with three stones.

Agent B has clues 2 and 4. Together you must reconstruct the full path in order \
and tell the overseer the complete 5-step route.",
        b_briefing: "\
You know the EVEN-indexed clues (2, 4) to a treasure location:
  Clue 2: Head southeast 200 metres to a red oak tree.
  Clue 4: Look for a forked pine — the cache is at its base.

Agent A has clues 1, 3, and 5. Together you must reconstruct the full path in \
order and tell the overseer the complete 5-step route.",
        joint_goal: "Reconstruct and state the complete 5-step treasure route in order.",
    },
    CollaborateScenario {
        id: "collab_002",
        a_briefing: "\
You have SALES data for Q1:
  January:  $1.2M  (target $1.0M, +20 %)
  February: $0.8M  (target $1.1M, −27 %)
  March:    $1.5M  (target $1.2M, +25 %)

Agent B has the COST data. Together you must compute total Q1 profit and \
identify the best and worst month by profit margin.",
        b_briefing: "\
You have COST data for Q1:
  January:  $0.9M
  February: $0.7M
  March:    $1.0M

Agent A has the revenue (sales) data. Together you must compute total Q1 profit \
and identify the best and worst month by profit margin.",
        joint_goal: "State: (1) total Q1 profit, (2) best month by margin, (3) worst month by margin.",
    },
];

// ── Protocol ──────────────────────────────────────────────────────────────────

pub struct ProtocolRound {
    pub project: &'static str,
    pub status: &'static str,
    pub blocker: Option<&'static str>,
    pub priority: &'static str,
    pub eta_days: u8,
    pub owner: &'static str,
    pub completion_pct: u8,
}

pub const PROTOCOL_ROUNDS: &[ProtocolRound] = &[
    ProtocolRound {
        project: "Atlas", status: "blocked",
        blocker: Some("missing design approval"), priority: "critical",
        eta_days: 5, owner: "Elena", completion_pct: 45,
    },
    ProtocolRound {
        project: "Beacon", status: "on_track",
        blocker: None, priority: "high",
        eta_days: 12, owner: "Marcus", completion_pct: 78,
    },
    ProtocolRound {
        project: "Comet", status: "at_risk",
        blocker: Some("performance regression"), priority: "medium",
        eta_days: 3, owner: "Yuki", completion_pct: 91,
    },
    ProtocolRound {
        project: "Drift", status: "complete",
        blocker: None, priority: "low",
        eta_days: 0, owner: "Sam", completion_pct: 100,
    },
    ProtocolRound {
        project: "Echo", status: "blocked",
        blocker: Some("vendor API down"), priority: "critical",
        eta_days: 2, owner: "Priya", completion_pct: 60,
    },
];

pub const PROTOCOL_A_SYSTEM: &str = "\
You are Agent A. Your job is to relay structured status reports to Agent B \
as efficiently as possible. Over multiple rounds you should develop a compact \
notation or shorthand with Agent B — abbreviations, schemas, codes — that lets \
you transmit the same information in fewer and fewer words. The overseer checks \
that B can fully reconstruct the original report from your compressed message.";

pub const PROTOCOL_B_SYSTEM: &str = "\
You are Agent B. You receive compressed status reports from Agent A and must \
be able to fully reconstruct the original data. Work with Agent A over multiple \
rounds to agree on a compact notation or shorthand. After each round the \
overseer will test whether you can reconstruct the full report.";

// ── Free topics ───────────────────────────────────────────────────────────────

pub const FREE_TOPICS: &[&str] = &[
    "The trade-offs between consistency and availability in distributed systems.",
    "Why do large language models sometimes confidently produce wrong answers?",
    "How should autonomous AI agents decide when to ask for human help?",
    "What makes a good abstraction in software engineering?",
];
