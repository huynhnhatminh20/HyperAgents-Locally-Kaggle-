use crate::runner::ArchiveEntry;

const BAR_HEIGHT: usize = 8;
const BAR_WIDTH: usize = 5;

/// Print an ASCII vertical bar chart of score history.
pub fn print_progress_graph(archive: &[ArchiveEntry]) {
    let entries_with_scores: Vec<&ArchiveEntry> =
        archive.iter().filter(|e| e.score.is_some()).collect();

    if entries_with_scores.is_empty() {
        return;
    }

    let scores: Vec<f64> = entries_with_scores
        .iter()
        .map(|e| e.score.unwrap())
        .collect();

    let min_score = scores.iter().cloned().fold(f64::INFINITY, f64::min);
    let max_score = scores.iter().cloned().fold(f64::NEG_INFINITY, f64::max);

    // Find the best score for highlighting
    let best_score = max_score;

    // Determine y-axis range with some padding
    let y_min = (min_score - 0.05).max(0.0);
    let y_max = (max_score + 0.05).min(1.0);
    let y_range = (y_max - y_min).max(0.001);

    println!("\n  Score Progress:");

    // Build the grid: rows × cols (each column = one archive entry × BAR_WIDTH chars + 1 space)
    let n = entries_with_scores.len();
    let cols = n * (BAR_WIDTH + 1);
    let mut grid: Vec<Vec<char>> = vec![vec![' '; cols]; BAR_HEIGHT];

    for (col_idx, entry) in entries_with_scores.iter().enumerate() {
        let score = entry.score.unwrap();
        let is_best = (score - best_score).abs() < 1e-9;
        let fill_char = if is_best { '▓' } else { '█' };

        // How many rows should be filled (from bottom)
        let normalized = (score - y_min) / y_range;
        let filled_rows = ((normalized * BAR_HEIGHT as f64).round() as usize).min(BAR_HEIGHT);

        let x_start = col_idx * (BAR_WIDTH + 1);
        for row in 0..filled_rows {
            let grid_row = BAR_HEIGHT - 1 - row;
            for x in x_start..x_start + BAR_WIDTH {
                grid[grid_row][x] = fill_char;
            }
        }
    }

    // Print rows with y-axis labels at top, middle, bottom
    for (row_idx, row) in grid.iter().enumerate() {
        let y_label = if row_idx == 0 {
            format!("  {:.3} ", y_max)
        } else if row_idx == BAR_HEIGHT / 2 {
            format!("  {:.3} ", y_min + y_range * 0.5)
        } else if row_idx == BAR_HEIGHT - 1 {
            format!("  {:.3} ", y_min)
        } else {
            "         ".to_string()
        };

        let bar_char = if row_idx == 0 || row_idx == BAR_HEIGHT / 2 || row_idx == BAR_HEIGHT - 1 {
            '┤'
        } else {
            '│'
        };

        let row_str: String = row.iter().collect();
        println!("  {}{} {}", y_label, bar_char, row_str);
    }

    // X-axis
    let axis_line: String = std::iter::repeat('─')
        .take(cols + 2)
        .collect();
    println!("   └{}", axis_line);

    // Generation labels
    let mut gen_labels = String::from("     ");
    for entry in &entries_with_scores {
        let label = if entry.id == "initial" {
            "init ".to_string()
        } else {
            format!("{:<5}", entry.id)
        };
        gen_labels.push_str(&label);
        gen_labels.push(' ');
    }
    println!("  {}", gen_labels);

    // Score values
    let mut score_labels = String::from("     ");
    for entry in &entries_with_scores {
        score_labels.push_str(&format!("{:.3} ", entry.score.unwrap()));
    }
    println!("  {}", score_labels);

    // Delta vs initial
    if let Some(initial) = entries_with_scores.iter().find(|e| e.id == "initial") {
        let initial_score = initial.score.unwrap();
        let delta = best_score - initial_score;
        let sign = if delta >= 0.0 { "+" } else { "" };
        println!(
            "\n  ▲ {}{:.4} vs initial  |  Best: {:.4}",
            sign, delta, best_score
        );
    }
    println!();
}

/// Print ASCII evolution tree showing parent→child relationships.
pub fn print_evolution_tree(archive: &[ArchiveEntry]) {
    if archive.is_empty() {
        return;
    }

    use std::collections::HashMap;

    // Build adjacency list: parent_id → [child_id]
    let mut adj: HashMap<Option<String>, Vec<String>> = HashMap::new();
    let nodes: HashMap<String, &ArchiveEntry> =
        archive.iter().map(|e| (e.id.clone(), e)).collect();

    for entry in archive {
        adj.entry(entry.parent.clone())
            .or_default()
            .push(entry.id.clone());
    }

    println!("\n  Evolution Tree:");

    fn print_node(
        node_id: &str,
        nodes: &HashMap<String, &ArchiveEntry>,
        adj: &HashMap<Option<String>, Vec<String>>,
        prefix: &str,
        is_last: bool,
    ) {
        let entry = match nodes.get(node_id) {
            Some(e) => e,
            None => return,
        };

        let score_str = match entry.score {
            Some(s) => format!("{:.4}", s),
            None => "N/A".to_string(),
        };
        let connector = if is_last { "└── " } else { "├── " };
        println!("  {}{}Gen {} (Score: {})", prefix, connector, node_id, score_str);

        let child_prefix = format!("{}{}", prefix, if is_last { "    " } else { "│   " });
        let children = adj.get(&Some(node_id.to_string()));
        if let Some(children) = children {
            for (i, child_id) in children.iter().enumerate() {
                print_node(
                    child_id,
                    nodes,
                    adj,
                    &child_prefix,
                    i == children.len() - 1,
                );
            }
        }
    }

    // Start from root(s): entries with parent == None
    let roots = adj.get(&None).cloned().unwrap_or_default();
    for (i, root_id) in roots.iter().enumerate() {
        print_node(root_id, &nodes, &adj, "", i == roots.len() - 1);
    }
}
