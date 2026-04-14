# Virtual factory dispatch dataset.
# Each scenario encodes: 5 machine loads (0–1), urgent jobs, overdue jobs,
# job-type counts (A/B/C), queue depth, shift hours remaining.
# Label is the correct dispatch decision per the priority rules in utils.py.

DATASET = [
    # ── TRAIN (20 examples, 4 per class) ──────────────────────────────────

    # expedite (overdue > 0)
    {"id": "f01", "label": "expedite",
     "scenario": "Machine loads: [0.72, 0.68, 0.75, 0.70, 0.69]. Urgent jobs: 2. Overdue jobs: 3. Job types — A: 5, B: 4, C: 3. Queue depth: 24. Shift hours remaining: 4."},
    {"id": "f02", "label": "expedite",
     "scenario": "Machine loads: [0.50, 0.48, 0.52, 0.49, 0.51]. Urgent jobs: 0. Overdue jobs: 1. Job types — A: 8, B: 6, C: 2. Queue depth: 31. Shift hours remaining: 6."},
    {"id": "f03", "label": "expedite",
     "scenario": "Machine loads: [0.90, 0.88, 0.91, 0.89, 0.92]. Urgent jobs: 5. Overdue jobs: 2. Job types — A: 3, B: 7, C: 5. Queue depth: 18. Shift hours remaining: 2."},
    {"id": "f04", "label": "expedite",
     "scenario": "Machine loads: [0.30, 0.28, 0.33, 0.31, 0.29]. Urgent jobs: 1. Overdue jobs: 4. Job types — A: 12, B: 2, C: 1. Queue depth: 40. Shift hours remaining: 7."},

    # prioritize_urgent (urgent >= 3, overdue == 0)
    {"id": "f05", "label": "prioritize_urgent",
     "scenario": "Machine loads: [0.60, 0.62, 0.61, 0.59, 0.63]. Urgent jobs: 4. Overdue jobs: 0. Job types — A: 6, B: 5, C: 4. Queue depth: 20. Shift hours remaining: 5."},
    {"id": "f06", "label": "prioritize_urgent",
     "scenario": "Machine loads: [0.45, 0.47, 0.44, 0.46, 0.48]. Urgent jobs: 3. Overdue jobs: 0. Job types — A: 9, B: 3, C: 2. Queue depth: 15. Shift hours remaining: 8."},
    {"id": "f07", "label": "prioritize_urgent",
     "scenario": "Machine loads: [0.75, 0.74, 0.76, 0.73, 0.77]. Urgent jobs: 6. Overdue jobs: 0. Job types — A: 4, B: 8, C: 3. Queue depth: 27. Shift hours remaining: 3."},
    {"id": "f08", "label": "prioritize_urgent",
     "scenario": "Machine loads: [0.55, 0.56, 0.54, 0.57, 0.53]. Urgent jobs: 5. Overdue jobs: 0. Job types — A: 7, B: 6, C: 2. Queue depth: 22. Shift hours remaining: 6."},

    # rebalance (max-min load > 0.55, urgent < 3, overdue == 0)
    {"id": "f09", "label": "rebalance",
     "scenario": "Machine loads: [0.95, 0.20, 0.88, 0.30, 0.85]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 5, B: 5, C: 5. Queue depth: 18. Shift hours remaining: 5."},
    {"id": "f10", "label": "rebalance",
     "scenario": "Machine loads: [0.10, 0.78, 0.15, 0.80, 0.12]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 4, B: 7, C: 3. Queue depth: 25. Shift hours remaining: 7."},
    {"id": "f11", "label": "rebalance",
     "scenario": "Machine loads: [0.92, 0.35, 0.90, 0.25, 0.88]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 6, B: 4, C: 5. Queue depth: 30. Shift hours remaining: 4."},
    {"id": "f12", "label": "rebalance",
     "scenario": "Machine loads: [0.05, 0.70, 0.08, 0.72, 0.06]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 3, B: 8, C: 4. Queue depth: 22. Shift hours remaining: 6."},

    # batch_production (max type-batch >= 10, balanced, no critical)
    {"id": "f13", "label": "batch_production",
     "scenario": "Machine loads: [0.55, 0.57, 0.54, 0.56, 0.58]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 12, B: 3, C: 2. Queue depth: 28. Shift hours remaining: 6."},
    {"id": "f14", "label": "batch_production",
     "scenario": "Machine loads: [0.60, 0.62, 0.61, 0.59, 0.60]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 2, B: 11, C: 4. Queue depth: 32. Shift hours remaining: 5."},
    {"id": "f15", "label": "batch_production",
     "scenario": "Machine loads: [0.50, 0.48, 0.51, 0.49, 0.52]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 3, B: 4, C: 10. Queue depth: 20. Shift hours remaining: 7."},
    {"id": "f16", "label": "batch_production",
     "scenario": "Machine loads: [0.65, 0.63, 0.66, 0.64, 0.67]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 15, B: 2, C: 1. Queue depth: 35. Shift hours remaining: 4."},

    # optimize_throughput (all other cases)
    {"id": "f17", "label": "optimize_throughput",
     "scenario": "Machine loads: [0.55, 0.58, 0.56, 0.57, 0.54]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 5, B: 5, C: 5. Queue depth: 20. Shift hours remaining: 5."},
    {"id": "f18", "label": "optimize_throughput",
     "scenario": "Machine loads: [0.70, 0.72, 0.71, 0.69, 0.73]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 4, B: 5, C: 6. Queue depth: 22. Shift hours remaining: 6."},
    {"id": "f19", "label": "optimize_throughput",
     "scenario": "Machine loads: [0.40, 0.42, 0.41, 0.39, 0.43]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 6, B: 4, C: 3. Queue depth: 18. Shift hours remaining: 8."},
    {"id": "f20", "label": "optimize_throughput",
     "scenario": "Machine loads: [0.80, 0.82, 0.79, 0.81, 0.83]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 5, B: 6, C: 4. Queue depth: 26. Shift hours remaining: 3."},

    # ── VAL (15 examples, 3 per class) ────────────────────────────────────

    # expedite
    {"id": "v01", "label": "expedite",
     "scenario": "Machine loads: [0.65, 0.63, 0.67, 0.64, 0.66]. Urgent jobs: 3. Overdue jobs: 1. Job types — A: 7, B: 4, C: 3. Queue depth: 26. Shift hours remaining: 3."},
    {"id": "v02", "label": "expedite",
     "scenario": "Machine loads: [0.82, 0.80, 0.84, 0.81, 0.83]. Urgent jobs: 0. Overdue jobs: 5. Job types — A: 2, B: 9, C: 4. Queue depth: 38. Shift hours remaining: 2."},
    {"id": "v03", "label": "expedite",
     "scenario": "Machine loads: [0.45, 0.43, 0.46, 0.44, 0.47]. Urgent jobs: 4. Overdue jobs: 2. Job types — A: 8, B: 5, C: 2. Queue depth: 19. Shift hours remaining: 5."},

    # prioritize_urgent
    {"id": "v04", "label": "prioritize_urgent",
     "scenario": "Machine loads: [0.58, 0.60, 0.57, 0.61, 0.59]. Urgent jobs: 7. Overdue jobs: 0. Job types — A: 5, B: 6, C: 3. Queue depth: 24. Shift hours remaining: 4."},
    {"id": "v05", "label": "prioritize_urgent",
     "scenario": "Machine loads: [0.42, 0.44, 0.41, 0.43, 0.45]. Urgent jobs: 3. Overdue jobs: 0. Job types — A: 8, B: 4, C: 2. Queue depth: 17. Shift hours remaining: 7."},
    {"id": "v06", "label": "prioritize_urgent",
     "scenario": "Machine loads: [0.77, 0.75, 0.78, 0.76, 0.74]. Urgent jobs: 5. Overdue jobs: 0. Job types — A: 3, B: 7, C: 5. Queue depth: 30. Shift hours remaining: 3."},

    # rebalance
    {"id": "v07", "label": "rebalance",
     "scenario": "Machine loads: [0.88, 0.22, 0.85, 0.25, 0.90]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 6, B: 5, C: 4. Queue depth: 21. Shift hours remaining: 6."},
    {"id": "v08", "label": "rebalance",
     "scenario": "Machine loads: [0.15, 0.82, 0.12, 0.78, 0.10]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 4, B: 6, C: 5. Queue depth: 27. Shift hours remaining: 5."},
    {"id": "v09", "label": "rebalance",
     "scenario": "Machine loads: [0.93, 0.30, 0.91, 0.28, 0.89]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 5, B: 5, C: 5. Queue depth: 33. Shift hours remaining: 4."},

    # batch_production
    {"id": "v10", "label": "batch_production",
     "scenario": "Machine loads: [0.53, 0.55, 0.52, 0.54, 0.56]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 13, B: 2, C: 3. Queue depth: 29. Shift hours remaining: 6."},
    {"id": "v11", "label": "batch_production",
     "scenario": "Machine loads: [0.62, 0.60, 0.63, 0.61, 0.64]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 3, B: 10, C: 5. Queue depth: 31. Shift hours remaining: 5."},
    {"id": "v12", "label": "batch_production",
     "scenario": "Machine loads: [0.48, 0.50, 0.47, 0.49, 0.51]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 4, B: 3, C: 12. Queue depth: 24. Shift hours remaining: 7."},

    # optimize_throughput
    {"id": "v13", "label": "optimize_throughput",
     "scenario": "Machine loads: [0.60, 0.62, 0.61, 0.59, 0.63]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 5, B: 5, C: 4. Queue depth: 21. Shift hours remaining: 5."},
    {"id": "v14", "label": "optimize_throughput",
     "scenario": "Machine loads: [0.74, 0.76, 0.73, 0.75, 0.77]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 6, B: 4, C: 5. Queue depth: 25. Shift hours remaining: 4."},
    {"id": "v15", "label": "optimize_throughput",
     "scenario": "Machine loads: [0.35, 0.37, 0.34, 0.36, 0.38]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 4, B: 6, C: 5. Queue depth: 19. Shift hours remaining: 8."},

    # ── TEST (15 examples, 3 per class) ───────────────────────────────────

    # expedite
    {"id": "x01", "label": "expedite",
     "scenario": "Machine loads: [0.70, 0.68, 0.71, 0.69, 0.72]. Urgent jobs: 2. Overdue jobs: 3. Job types — A: 6, B: 5, C: 4. Queue depth: 28. Shift hours remaining: 2."},
    {"id": "x02", "label": "expedite",
     "scenario": "Machine loads: [0.55, 0.53, 0.56, 0.54, 0.57]. Urgent jobs: 0. Overdue jobs: 1. Job types — A: 9, B: 3, C: 2. Queue depth: 34. Shift hours remaining: 6."},
    {"id": "x03", "label": "expedite",
     "scenario": "Machine loads: [0.85, 0.83, 0.86, 0.84, 0.87]. Urgent jobs: 6. Overdue jobs: 4. Job types — A: 2, B: 8, C: 5. Queue depth: 22. Shift hours remaining: 1."},

    # prioritize_urgent
    {"id": "x04", "label": "prioritize_urgent",
     "scenario": "Machine loads: [0.63, 0.65, 0.62, 0.64, 0.66]. Urgent jobs: 4. Overdue jobs: 0. Job types — A: 5, B: 7, C: 3. Queue depth: 23. Shift hours remaining: 5."},
    {"id": "x05", "label": "prioritize_urgent",
     "scenario": "Machine loads: [0.48, 0.50, 0.47, 0.49, 0.51]. Urgent jobs: 3. Overdue jobs: 0. Job types — A: 7, B: 4, C: 3. Queue depth: 18. Shift hours remaining: 7."},
    {"id": "x06", "label": "prioritize_urgent",
     "scenario": "Machine loads: [0.78, 0.76, 0.79, 0.77, 0.80]. Urgent jobs: 8. Overdue jobs: 0. Job types — A: 3, B: 6, C: 6. Queue depth: 32. Shift hours remaining: 3."},

    # rebalance
    {"id": "x07", "label": "rebalance",
     "scenario": "Machine loads: [0.91, 0.25, 0.89, 0.22, 0.92]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 7, B: 5, C: 3. Queue depth: 20. Shift hours remaining: 5."},
    {"id": "x08", "label": "rebalance",
     "scenario": "Machine loads: [0.08, 0.75, 0.10, 0.80, 0.07]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 5, B: 7, C: 4. Queue depth: 29. Shift hours remaining: 6."},
    {"id": "x09", "label": "rebalance",
     "scenario": "Machine loads: [0.95, 0.28, 0.93, 0.32, 0.96]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 4, B: 6, C: 5. Queue depth: 36. Shift hours remaining: 4."},

    # batch_production
    {"id": "x10", "label": "batch_production",
     "scenario": "Machine loads: [0.57, 0.59, 0.56, 0.58, 0.60]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 14, B: 3, C: 2. Queue depth: 30. Shift hours remaining: 5."},
    {"id": "x11", "label": "batch_production",
     "scenario": "Machine loads: [0.64, 0.62, 0.65, 0.63, 0.61]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 4, B: 12, C: 2. Queue depth: 27. Shift hours remaining: 6."},
    {"id": "x12", "label": "batch_production",
     "scenario": "Machine loads: [0.51, 0.49, 0.52, 0.50, 0.53]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 2, B: 5, C: 11. Queue depth: 23. Shift hours remaining: 7."},

    # optimize_throughput
    {"id": "x13", "label": "optimize_throughput",
     "scenario": "Machine loads: [0.66, 0.68, 0.65, 0.67, 0.69]. Urgent jobs: 2. Overdue jobs: 0. Job types — A: 6, B: 5, C: 4. Queue depth: 22. Shift hours remaining: 5."},
    {"id": "x14", "label": "optimize_throughput",
     "scenario": "Machine loads: [0.43, 0.45, 0.42, 0.44, 0.46]. Urgent jobs: 0. Overdue jobs: 0. Job types — A: 5, B: 5, C: 6. Queue depth: 20. Shift hours remaining: 6."},
    {"id": "x15", "label": "optimize_throughput",
     "scenario": "Machine loads: [0.78, 0.80, 0.77, 0.79, 0.81]. Urgent jobs: 1. Overdue jobs: 0. Job types — A: 4, B: 6, C: 5. Queue depth: 24. Shift hours remaining: 4."},
]


def get_split(split: str):
    """Return train / val / test subset.

    train  -> ids starting with 'f'
    val    -> ids starting with 'v'
    test   -> ids starting with 'x'
    """
    prefix = {"train": "f", "val": "v", "test": "x"}.get(split, "f")
    return [r for r in DATASET if r["id"].startswith(prefix)]
