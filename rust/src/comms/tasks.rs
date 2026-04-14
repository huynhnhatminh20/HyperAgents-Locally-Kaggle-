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

// ── Language (Emergent Symbol System) ────────────────────────────────────────

pub struct LanguageRound {
    /// Short label describing which new concepts must be expressible this round
    pub concept_label: &'static str,
    /// The concrete message Agent A must encode
    pub message: &'static str,
    /// Ground-truth meaning the overseer uses to verify Agent B's decode
    pub expected_meaning: &'static str,
}

pub struct LanguageScenario {
    pub id: &'static str,
    /// Thematic domain — sets the context for what symbols are needed
    pub domain: &'static str,
    pub rounds: &'static [LanguageRound],
}

pub const LANGUAGE_SCENARIOS: &[LanguageScenario] = &[
    LanguageScenario {
        id: "lang_001",
        domain: "mission ops",
        rounds: &[
            LanguageRound {
                concept_label: "BOOTSTRAP — agents, status, urgency",
                message: "Agent Alpha is blocked. Needs help urgently.",
                expected_meaning: "An entity called Alpha is in a stuck/blocked state and requires immediate assistance.",
            },
            LanguageRound {
                concept_label: "locations + movement",
                message: "Move Agent Beta to sector 7. Sector 3 is clear.",
                expected_meaning: "Agent Beta should relocate to sector 7. Sector 3 has no threats or obstacles.",
            },
            LanguageRound {
                concept_label: "quantities + time",
                message: "3 agents arrive at base in 2 hours. Supplies for 5 days.",
                expected_meaning: "Three agents will reach the base within two hours. There are supplies sufficient for five days.",
            },
            LanguageRound {
                concept_label: "conditions + logic (if/then/else)",
                message: "If sector 4 is blocked then reroute via sector 2, else proceed direct.",
                expected_meaning: "Conditional: if sector 4 is obstructed, use sector 2 as alternative; otherwise continue on the direct route.",
            },
            LanguageRound {
                concept_label: "FULL MESSAGE — use complete lexicon",
                message: "Alpha and Beta complete. Gamma blocked at sector 5. Reroute Gamma to sector 2 in 1 hour.",
                expected_meaning: "Agents Alpha and Beta finished their tasks. Gamma is stuck at sector 5. Gamma must be redirected to sector 2 within one hour.",
            },
        ],
    },
    LanguageScenario {
        id: "lang_002",
        domain: "environment / survival",
        rounds: &[
            LanguageRound {
                concept_label: "BOOTSTRAP — elements, states, intensity levels",
                message: "Heavy rain is coming. Wind is strong.",
                expected_meaning: "Intense rainfall is approaching. Wind speed is high.",
            },
            LanguageRound {
                concept_label: "directions + locations",
                message: "Storm moving north. Safe shelter is to the east.",
                expected_meaning: "The storm is travelling northward. A safe refuge exists in the eastern direction.",
            },
            LanguageRound {
                concept_label: "time + duration",
                message: "Sun appears in 3 hours. Rain lasts 2 days.",
                expected_meaning: "Clear skies will return in approximately three hours. The rainfall will continue for two days.",
            },
            LanguageRound {
                concept_label: "danger + safety alerts",
                message: "Flood risk high in valley. Move to high ground now.",
                expected_meaning: "There is a high flood danger in the valley. Immediate relocation to elevated terrain is required.",
            },
            LanguageRound {
                concept_label: "FULL REPORT — all concepts",
                message: "Storm from east, strong wind, heavy rain 2 days. Valley flooded. Move north to shelter in 1 hour.",
                expected_meaning: "An eastern storm brings strong winds and heavy rain lasting two days. The valley is already flooded. Evacuate northward to a shelter within one hour.",
            },
        ],
    },
    LanguageScenario {
        id: "lang_003",
        domain: "trade / economy",
        rounds: &[
            LanguageRound {
                concept_label: "BOOTSTRAP — goods, prices, quantities",
                message: "Grain costs 5 coins. We have 20 units.",
                expected_meaning: "The price of grain is 5 currency units. The current stock is 20 units of grain.",
            },
            LanguageRound {
                concept_label: "transactions + direction (buy/sell/trade)",
                message: "Sell 10 grain, buy 3 iron.",
                expected_meaning: "Execute a sale of 10 units of grain and purchase 3 units of iron.",
            },
            LanguageRound {
                concept_label: "time + trends (rising/falling/stable)",
                message: "Iron price rising fast. Sell iron tomorrow.",
                expected_meaning: "The price of iron is increasing rapidly. Sell iron holdings the next day.",
            },
            LanguageRound {
                concept_label: "conditionals + thresholds",
                message: "If grain price drops below 3 coins, buy 50 units.",
                expected_meaning: "When grain falls below 3 currency units per unit, acquire 50 units of grain.",
            },
            LanguageRound {
                concept_label: "FULL TRADE ORDER — all concepts",
                message: "Grain 4 coins stable. Iron 8 coins rising. Sell 5 iron now. If iron exceeds 10 coins, sell all. Buy 30 grain.",
                expected_meaning: "Grain is at 4 coins and stable. Iron is at 8 and rising. Sell 5 iron immediately. If iron exceeds 10, liquidate all iron. Purchase 30 units of grain.",
            },
        ],
    },
];

pub const LANGUAGE_A_BOOTSTRAP: &str = "\
You are Agent A in an EMERGENT LANGUAGE experiment (domain: {DOMAIN}).

YOUR GOAL this round: invent a compact symbol vocabulary with Agent B.
New concepts to cover: {CONCEPTS}

RULES:
• Symbols can be anything short: emoji, 1-3 letter codes, numbers, punctuation combinations
• Each symbol must be unambiguous and as short as possible
• Propose, negotiate, refine — natural language is allowed ONLY for negotiation
• When you both agree, end your final message with a LEXICON block:

LEXICON:
<symbol> = <meaning>
<symbol> = <meaning>
...

Try to encode the test message at the end using only your new symbols, \
so B can verify understanding:
TEST: {MESSAGE}";

pub const LANGUAGE_B_BOOTSTRAP: &str = "\
You are Agent B in an EMERGENT LANGUAGE experiment (domain: {DOMAIN}).

YOUR GOAL this round: agree on a compact symbol vocabulary with Agent A.
New concepts to cover: {CONCEPTS}

RULES:
• Accept, reject, or modify A's symbol proposals — keep them short (1-3 chars)
• Add your own proposals for anything A misses
• Natural language is allowed ONLY for negotiation
• After agreeing, end with the full LEXICON block:

LEXICON:
<symbol> = <meaning>
<symbol> = <meaning>
...

Then decode A's TEST message to confirm understanding:
DECODE: <natural language meaning of the test encoding>";

pub const LANGUAGE_A_ENCODE: &str = "\
You are Agent A in an EMERGENT LANGUAGE experiment (domain: {DOMAIN}).

This round you must ENCODE a message using ONLY your invented symbols.
New concepts this round: {CONCEPTS}

CURRENT LEXICON:
{LEXICON}

STEPS:
1. If the message requires new concepts not in the lexicon, declare new symbols first:
   NEW: <sym> = <meaning>
2. Then encode the message — PURE SYMBOLS ONLY, no natural language sentences.
   You may use spaces between symbols for readability.

Message to encode: \"{MESSAGE}\"";

pub const LANGUAGE_B_DECODE: &str = "\
You are Agent B in an EMERGENT LANGUAGE experiment (domain: {DOMAIN}).

Decode Agent A's symbol message into full natural language.
New concepts this round: {CONCEPTS}

CURRENT LEXICON:
{LEXICON}

If A declared new symbols (lines starting with NEW:), add them to your understanding.

Reply format:
NEW SYMBOLS ADDED: <list any new symbols A introduced, or \"none\">
DECODE: <your full natural-language decoding of A's message>";

// ── Free topics ───────────────────────────────────────────────────────────────

pub const FREE_TOPICS: &[&str] = &[
    "The trade-offs between consistency and availability in distributed systems.",
    "Why do large language models sometimes confidently produce wrong answers?",
    "How should autonomous AI agents decide when to ask for human help?",
    "What makes a good abstraction in software engineering?",
];
