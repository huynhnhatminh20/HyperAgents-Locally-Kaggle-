use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Sample {
    pub id: String,
    pub scenario: String,
    pub label: String,
}

pub fn all_samples() -> Vec<Sample> {
    vec![
        // ── TRAIN (20 examples, 4 per class) ────────────────────────────────
        // expedite
        Sample { id: "f01".into(), label: "expedite".into(),
            scenario: "Machine loads: [0.72, 0.68, 0.75, 0.70, 0.69]. Urgent jobs: 2. Overdue jobs: 3. Job types — A: 5, B: 4, C: 3. Queue depth: 24. Shift hours remaining: 4.".into() },
        Sample { id: "f02".into(), label: "expedite".into(),
            scenario: "Machine loads: [0.50, 0.48, 0.52, 0.49, 0.51]. Urgent jobs: 0. Overdue jobs: 1. Job types — A: 8, B: 6, C: 2. Queue depth: 31. Shift hours remaining: 6.".into() },
        Sample { id: "f03".into(), label: "expedite".into(),
            scenario: "Machine loads: [0.90, 0.88, 0.91, 0.89, 0.92]. Urgent jobs: 5. Overdue jobs: 2. Job types — A: 3, B: 7, C: 5. Queue depth: 18. Shift hours remaining: 2.".into() },
        Sample { id: "f04".into(), label: "expedite".into(),
            scenario: "Machine loads: [0.30, 0.28, 0.33, 0.31, 0.29]. Urgent jobs: 1. Overdue jobs: 4. Job types — A: 12, B: 2, C: 1. Queue depth: 40. Shift hours remaining: 7.".into() },
        // prioritize_urgent
        Sample { id: "f05".into(), label: "prioritize_urgent".into(),
            scenario: "Machine loads: [0.60, 0.62, 0.61, 0.59, 0.63]. Urgent jobs: 4. Overdue jobs: 0. Job types — A: 6, B: 5, C: 4. Queue depth: 20. Shift hours remaining: 5.".into() },
        Sample { id: "f06".into(), label: "prioritize_urgent".into(),
            scenario: "Machine loads: [0.45, 0.47, 0.44, 0.46, 0.48]. Urgent jobs: 3. Overdue jobs: 0. Job types — A: 9, B: 3, C: 2. Queue depth: 15. Shift hours remaining: 8.".into() },
        Sample { id: "f07".into(), label: "prioritize_urgent".into(),
            scenario: "Machine loads: [0.75, 0.74, 0.76, 0.73, 0.77]. Urgent jobs: 6. Overdue jobs: 0. Job types — A: 4, B: 8, C: 3. Queue depth: 27. Shift hours remaining: 3.".into() },
        Sample { id: "f08".into(), label: "prioritize_urgent".into(),
            scenario: "Machine loads: [0.55, 0.56, 0.54, 0.57, 0.53]. Urgent jobs: 5. Overdue jobs: 0. Job types — A: 7, B: 6, C: 2. Queue depth: 22. Shift hours remaining: 6.".into() },
        // rebalance
        Sample { id: "f09".into(), label: "rebalance".into(),
            scenario: "Machine loads: [0.95, 0.20, 0.88, 0.30, 0.85]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 5, B: 5, C: 5. Queue depth: 18. Shift hours remaining: 5.".into() },
        Sample { id: "f10".into(), label: "rebalance".into(),
            scenario: "Machine loads: [0.10, 0.78, 0.15, 0.80, 0.12]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 4, B: 7, C: 3. Queue depth: 25. Shift hours remaining: 7.".into() },
        Sample { id: "f11".into(), label: "rebalance".into(),
            scenario: "Machine loads: [0.92, 0.35, 0.90, 0.25, 0.88]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 6, B: 4, C: 5. Queue depth: 30. Shift hours remaining: 4.".into() },
        Sample { id: "f12".into(), label: "rebalance".into(),
            scenario: "Machine loads: [0.05, 0.70, 0.08, 0.72, 0.06]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 3, B: 8, C: 4. Queue depth: 22. Shift hours remaining: 6.".into() },
        // batch_production
        Sample { id: "f13".into(), label: "batch_production".into(),
            scenario: "Machine loads: [0.55, 0.57, 0.54, 0.56, 0.58]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 12, B: 3, C: 2. Queue depth: 28. Shift hours remaining: 6.".into() },
        Sample { id: "f14".into(), label: "batch_production".into(),
            scenario: "Machine loads: [0.60, 0.62, 0.61, 0.59, 0.60]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 2, B: 11, C: 4. Queue depth: 32. Shift hours remaining: 5.".into() },
        Sample { id: "f15".into(), label: "batch_production".into(),
            scenario: "Machine loads: [0.50, 0.48, 0.51, 0.49, 0.52]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 3, B: 4, C: 10. Queue depth: 20. Shift hours remaining: 7.".into() },
        Sample { id: "f16".into(), label: "batch_production".into(),
            scenario: "Machine loads: [0.65, 0.63, 0.66, 0.64, 0.67]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 15, B: 2, C: 1. Queue depth: 35. Shift hours remaining: 4.".into() },
        // optimize_throughput
        Sample { id: "f17".into(), label: "optimize_throughput".into(),
            scenario: "Machine loads: [0.55, 0.58, 0.56, 0.57, 0.54]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 5, B: 5, C: 5. Queue depth: 20. Shift hours remaining: 5.".into() },
        Sample { id: "f18".into(), label: "optimize_throughput".into(),
            scenario: "Machine loads: [0.70, 0.72, 0.71, 0.69, 0.73]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 4, B: 5, C: 6. Queue depth: 22. Shift hours remaining: 6.".into() },
        Sample { id: "f19".into(), label: "optimize_throughput".into(),
            scenario: "Machine loads: [0.40, 0.42, 0.41, 0.39, 0.43]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 6, B: 4, C: 3. Queue depth: 18. Shift hours remaining: 8.".into() },
        Sample { id: "f20".into(), label: "optimize_throughput".into(),
            scenario: "Machine loads: [0.80, 0.82, 0.79, 0.81, 0.83]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 5, B: 6, C: 4. Queue depth: 26. Shift hours remaining: 3.".into() },

        // ── VAL (15 examples, 3 per class) ──────────────────────────────────
        // expedite
        Sample { id: "v01".into(), label: "expedite".into(),
            scenario: "Machine loads: [0.65, 0.63, 0.67, 0.64, 0.66]. Urgent jobs: 3. Overdue jobs: 1. Job types — A: 7, B: 4, C: 3. Queue depth: 26. Shift hours remaining: 3.".into() },
        Sample { id: "v02".into(), label: "expedite".into(),
            scenario: "Machine loads: [0.82, 0.80, 0.84, 0.81, 0.83]. Urgent jobs: 0. Overdue jobs: 5. Job types — A: 2, B: 9, C: 4. Queue depth: 38. Shift hours remaining: 2.".into() },
        Sample { id: "v03".into(), label: "expedite".into(),
            scenario: "Machine loads: [0.45, 0.43, 0.46, 0.44, 0.47]. Urgent jobs: 4. Overdue jobs: 2. Job types — A: 8, B: 5, C: 2. Queue depth: 19. Shift hours remaining: 5.".into() },
        // prioritize_urgent
        Sample { id: "v04".into(), label: "prioritize_urgent".into(),
            scenario: "Machine loads: [0.58, 0.60, 0.57, 0.61, 0.59]. Urgent jobs: 7. Overdue jobs: 0. Job types — A: 5, B: 6, C: 3. Queue depth: 24. Shift hours remaining: 4.".into() },
        Sample { id: "v05".into(), label: "prioritize_urgent".into(),
            scenario: "Machine loads: [0.42, 0.44, 0.41, 0.43, 0.45]. Urgent jobs: 3. Overdue jobs: 0. Job types — A: 8, B: 4, C: 2. Queue depth: 17. Shift hours remaining: 7.".into() },
        Sample { id: "v06".into(), label: "prioritize_urgent".into(),
            scenario: "Machine loads: [0.77, 0.75, 0.78, 0.76, 0.74]. Urgent jobs: 5. Overdue jobs: 0. Job types — A: 3, B: 7, C: 5. Queue depth: 30. Shift hours remaining: 3.".into() },
        // rebalance
        Sample { id: "v07".into(), label: "rebalance".into(),
            scenario: "Machine loads: [0.88, 0.22, 0.85, 0.25, 0.90]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 6, B: 5, C: 4. Queue depth: 21. Shift hours remaining: 6.".into() },
        Sample { id: "v08".into(), label: "rebalance".into(),
            scenario: "Machine loads: [0.15, 0.82, 0.12, 0.78, 0.10]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 4, B: 6, C: 5. Queue depth: 27. Shift hours remaining: 5.".into() },
        Sample { id: "v09".into(), label: "rebalance".into(),
            scenario: "Machine loads: [0.93, 0.30, 0.91, 0.28, 0.89]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 5, B: 5, C: 5. Queue depth: 33. Shift hours remaining: 4.".into() },
        // batch_production
        Sample { id: "v10".into(), label: "batch_production".into(),
            scenario: "Machine loads: [0.53, 0.55, 0.52, 0.54, 0.56]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 13, B: 2, C: 3. Queue depth: 29. Shift hours remaining: 6.".into() },
        Sample { id: "v11".into(), label: "batch_production".into(),
            scenario: "Machine loads: [0.62, 0.60, 0.63, 0.61, 0.64]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 3, B: 10, C: 5. Queue depth: 31. Shift hours remaining: 5.".into() },
        Sample { id: "v12".into(), label: "batch_production".into(),
            scenario: "Machine loads: [0.48, 0.50, 0.47, 0.49, 0.51]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 4, B: 3, C: 12. Queue depth: 24. Shift hours remaining: 7.".into() },
        // optimize_throughput
        Sample { id: "v13".into(), label: "optimize_throughput".into(),
            scenario: "Machine loads: [0.60, 0.62, 0.61, 0.59, 0.63]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 5, B: 5, C: 4. Queue depth: 21. Shift hours remaining: 5.".into() },
        Sample { id: "v14".into(), label: "optimize_throughput".into(),
            scenario: "Machine loads: [0.74, 0.76, 0.73, 0.75, 0.77]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 6, B: 4, C: 5. Queue depth: 25. Shift hours remaining: 4.".into() },
        Sample { id: "v15".into(), label: "optimize_throughput".into(),
            scenario: "Machine loads: [0.35, 0.37, 0.34, 0.36, 0.38]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 4, B: 6, C: 5. Queue depth: 19. Shift hours remaining: 8.".into() },

        // ── TEST (15 examples, 3 per class) ─────────────────────────────────
        // expedite
        Sample { id: "x01".into(), label: "expedite".into(),
            scenario: "Machine loads: [0.70, 0.68, 0.71, 0.69, 0.72]. Urgent jobs: 2. Overdue jobs: 3. Job types — A: 6, B: 5, C: 4. Queue depth: 28. Shift hours remaining: 2.".into() },
        Sample { id: "x02".into(), label: "expedite".into(),
            scenario: "Machine loads: [0.55, 0.53, 0.56, 0.54, 0.57]. Urgent jobs: 0. Overdue jobs: 1. Job types — A: 9, B: 3, C: 2. Queue depth: 34. Shift hours remaining: 6.".into() },
        Sample { id: "x03".into(), label: "expedite".into(),
            scenario: "Machine loads: [0.85, 0.83, 0.86, 0.84, 0.87]. Urgent jobs: 6. Overdue jobs: 4. Job types — A: 2, B: 8, C: 5. Queue depth: 22. Shift hours remaining: 1.".into() },
        // prioritize_urgent
        Sample { id: "x04".into(), label: "prioritize_urgent".into(),
            scenario: "Machine loads: [0.63, 0.65, 0.62, 0.64, 0.66]. Urgent jobs: 4. Overdue jobs: 0. Job types — A: 5, B: 7, C: 3. Queue depth: 23. Shift hours remaining: 5.".into() },
        Sample { id: "x05".into(), label: "prioritize_urgent".into(),
            scenario: "Machine loads: [0.48, 0.50, 0.47, 0.49, 0.51]. Urgent jobs: 3. Overdue jobs: 0. Job types — A: 7, B: 4, C: 3. Queue depth: 18. Shift hours remaining: 7.".into() },
        Sample { id: "x06".into(), label: "prioritize_urgent".into(),
            scenario: "Machine loads: [0.78, 0.76, 0.79, 0.77, 0.80]. Urgent jobs: 8. Overdue jobs: 0. Job types — A: 3, B: 6, C: 6. Queue depth: 32. Shift hours remaining: 3.".into() },
        // rebalance
        Sample { id: "x07".into(), label: "rebalance".into(),
            scenario: "Machine loads: [0.91, 0.25, 0.89, 0.22, 0.92]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 7, B: 5, C: 3. Queue depth: 20. Shift hours remaining: 5.".into() },
        Sample { id: "x08".into(), label: "rebalance".into(),
            scenario: "Machine loads: [0.08, 0.75, 0.10, 0.80, 0.07]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 5, B: 7, C: 4. Queue depth: 29. Shift hours remaining: 6.".into() },
        Sample { id: "x09".into(), label: "rebalance".into(),
            scenario: "Machine loads: [0.95, 0.28, 0.93, 0.32, 0.96]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 4, B: 6, C: 5. Queue depth: 36. Shift hours remaining: 4.".into() },
        // batch_production
        Sample { id: "x10".into(), label: "batch_production".into(),
            scenario: "Machine loads: [0.57, 0.59, 0.56, 0.58, 0.60]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 14, B: 3, C: 2. Queue depth: 30. Shift hours remaining: 5.".into() },
        Sample { id: "x11".into(), label: "batch_production".into(),
            scenario: "Machine loads: [0.64, 0.62, 0.65, 0.63, 0.61]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 4, B: 12, C: 2. Queue depth: 27. Shift hours remaining: 6.".into() },
        Sample { id: "x12".into(), label: "batch_production".into(),
            scenario: "Machine loads: [0.51, 0.49, 0.52, 0.50, 0.53]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 2, B: 5, C: 11. Queue depth: 23. Shift hours remaining: 7.".into() },
        // optimize_throughput
        Sample { id: "x13".into(), label: "optimize_throughput".into(),
            scenario: "Machine loads: [0.66, 0.68, 0.65, 0.67, 0.69]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 6, B: 5, C: 4. Queue depth: 22. Shift hours remaining: 5.".into() },
        Sample { id: "x14".into(), label: "optimize_throughput".into(),
            scenario: "Machine loads: [0.43, 0.45, 0.42, 0.44, 0.46]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 5, B: 5, C: 6. Queue depth: 20. Shift hours remaining: 6.".into() },
        Sample { id: "x15".into(), label: "optimize_throughput".into(),
            scenario: "Machine loads: [0.78, 0.80, 0.77, 0.79, 0.81]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 4, B: 6, C: 5. Queue depth: 24. Shift hours remaining: 4.".into() },
    ]
}

pub fn get_split(split: &str) -> Vec<Sample> {
    let prefix = match split {
        "train" => "f",
        "val"   => "v",
        "test"  => "x",
        _       => "f",
    };
    all_samples().into_iter().filter(|s| s.id.starts_with(prefix)).collect()
}

pub fn format_input(sample: &Sample) -> serde_json::Value {
    serde_json::json!({
        "domain": "factory",
        "id": sample.id,
        "scenario": sample.scenario,
        "instruction": concat!(
            "You are a factory floor controller. Analyse the production scenario and output ",
            "exactly one dispatch decision from: ",
            "expedite, prioritize_urgent, rebalance, batch_production, optimize_throughput.\n",
            "Decision rules (apply top-to-bottom, first match wins):\n",
            "  expedite            — any overdue jobs > 0\n",
            "  prioritize_urgent   — urgent jobs >= 3 AND overdue == 0\n",
            "  rebalance           — max_machine_load - min_machine_load > 0.55 AND urgent < 3 AND overdue == 0\n",
            "  batch_production    — largest job-type batch >= 10 AND machines balanced AND no critical pressure\n",
            "  optimize_throughput — none of the above apply\n",
            "Respond with ONLY the decision label in lowercase, nothing else."
        ),
    })
}
