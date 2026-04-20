# Formwerk Engineering Design Domain for HyperAgents
#
# Each scenario presents an engineering part with current parameters,
# constraint violations, and performance metrics.
# The task agent must output a JSON object with improved parameters.
#
# Labels are the "ideal" parameter adjustments that would fix the violations.
# The meta-agent evolves the task agent's reasoning strategy to find
# better parameter suggestions across diverse engineering problems.

import json
import subprocess
import os
from pathlib import Path

NEWRON_ROOT = Path(__file__).resolve().parents[4]  # up to NewRon root
OPTIMIZER_BIN = NEWRON_ROOT / "Optimize" / "newron-opt" / "target" / "release" / "newron-opt"

# ── Static dataset: engineering scenarios with known-good solutions ────────

DATASET = [
    # ── PISTON (train) ─────────────────────────────────────────────────────
    {"id": "p01", "label": '{"ring_depth_mm": 3.0}',
     "domain": "formwerk", "part": "piston",
     "scenario": "Part: piston. Score: 0.944 (15/16 pass).\n"
                 "FAIL: ring_depth_clearance: value=0.086 limit=0.100 — Ring depth leaves >= 10% wall.\n"
                 "Current params: wall_thick_mm=3.5, ring_depth_mm=3.2, bore_mm=77.\n"
                 "Valid params: bore_mm(77 FIXED), wall_thick_mm(2.5-6), ring_depth_mm(2.5-4.0), "
                 "crown_thick_mm(4-8), pin_dia_mm(17-22), skirt_length_mm(65-85)."},

    {"id": "p02", "label": '{"wall_thick_mm": 3.0, "crown_thick_mm": 4.5}',
     "domain": "formwerk", "part": "piston",
     "scenario": "Part: piston. Score: 0.875 (14/16 pass).\n"
                 "FAIL: wall_max: value=6.5 limit=6.0 — Wall <= 6mm.\n"
                 "FAIL: crown_max: value=9.0 limit=8.0 — Crown <= 8mm.\n"
                 "Current params: wall_thick_mm=6.5, crown_thick_mm=9.0, bore_mm=77.\n"
                 "Valid params: wall_thick_mm(2.5-6), crown_thick_mm(4-8)."},

    {"id": "p03", "label": '{"pin_dia_mm": 18.0}',
     "domain": "formwerk", "part": "piston",
     "scenario": "Part: piston. Score: 0.938 (15/16 pass).\n"
                 "FAIL: pin_ratio_min: value=0.195 limit=0.220 — Pin/bore >= 0.22.\n"
                 "Current params: pin_dia_mm=15, bore_mm=77.\n"
                 "Valid params: pin_dia_mm(17-22)."},

    # ── TURBINE (train) ────────────────────────────────────────────────────
    {"id": "t01", "label": '{"num_blades": 18, "blade_thickness_mm": 1.8, "outer_dia_mm": 24}',
     "domain": "formwerk", "part": "turbinerotor",
     "scenario": "Part: turbinerotor. Score: 0.944 (17/18 pass).\n"
                 "FAIL: solidity_min: value=0.183 limit=0.800 — Solidity = nBlades*thickness / (2*pi*meanR). "
                 "Increase num_blades, blade_thickness, or decrease outer_dia_mm.\n"
                 "Current params: outer_dia_mm=36, hub_dia_mm=14, num_blades=12, blade_thickness_mm=1.2.\n"
                 "Valid params: outer_dia_mm(18-40), hub_dia_mm(6-16), num_blades(8-20), "
                 "blade_thickness_mm(0.8-2.0)."},

    {"id": "t02", "label": '{"blade_height_mm": 6.0}',
     "domain": "formwerk", "part": "turbinerotor",
     "scenario": "Part: turbinerotor. Score: 0.944 (17/18 pass).\n"
                 "FAIL: blade_ar_min: value=2.63 limit=3.00 — Blade AR >= 3 (aero).\n"
                 "Current params: blade_height_mm=5.0, blade_thickness_mm=1.9.\n"
                 "Valid params: blade_height_mm(3-10), blade_thickness_mm(0.8-2.0)."},

    # ── NOZZLE (train) ─────────────────────────────────────────────────────
    {"id": "n01", "label": '{"wall_thickness_mm": 3.0}',
     "domain": "formwerk", "part": "nozzle",
     "scenario": "Part: nozzle. Score: 0.875 (7/8 pass).\n"
                 "FAIL: wall_min: value=1.5 limit=2.0 — Wall >= 2mm.\n"
                 "Current params: wall_thickness_mm=1.5.\n"
                 "Valid params: wall_thickness_mm(2-6)."},

    {"id": "n02", "label": '{"exit_radius_mm": 16.0}',
     "domain": "formwerk", "part": "nozzle",
     "scenario": "Part: nozzle. Score: 0.875 (7/8 pass).\n"
                 "FAIL: expansion_min: value=1.5 limit=2.0 — Expansion ratio >= 2.\n"
                 "Current params: throat_radius_mm=8, exit_radius_mm=10.\n"
                 "Valid params: throat_radius_mm(3-15), exit_radius_mm(8-30)."},

    # ── BIKE (train) ──────────────────────────────────────────────────────
    {"id": "b01", "label": '{"head_angle_deg": 73.0}',
     "domain": "formwerk", "part": "bike",
     "scenario": "Part: bike. Score: 0.875 (7/8 pass).\n"
                 "FAIL: ha_min: value=68.0 limit=70.0 — Head angle >= 70 degrees.\n"
                 "Current params: head_angle_deg=68.\n"
                 "Valid params: head_angle_deg(70-76), seat_angle_deg(71-76)."},

    # ── VALIDATION (held-out) ──────────────────────────────────────────────
    {"id": "v01", "label": '{"ring_depth_mm": 2.8, "wall_thick_mm": 3.8}',
     "domain": "formwerk", "part": "piston",
     "scenario": "Part: piston. Score: 0.875 (14/16 pass).\n"
                 "FAIL: ring_clear: value=0.053 limit=0.100 — Ring depth leaves >= 10% wall.\n"
                 "FAIL: wall_min: value=2.4 limit=2.5 — Wall >= 2.5mm.\n"
                 "Current params: wall_thick_mm=2.4, ring_depth_mm=2.8, bore_mm=77.\n"
                 "Valid params: wall_thick_mm(2.5-6), ring_depth_mm(2.5-4.0)."},

    {"id": "v02", "label": '{"outer_dia_mm": 22, "blade_height_mm": 5.8}',
     "domain": "formwerk", "part": "turbinerotor",
     "scenario": "Part: turbinerotor. Score: 0.889 (16/18 pass).\n"
                 "FAIL: solidity_min: value=0.509 limit=0.800.\n"
                 "FAIL: blade_ar_min: value=2.63 limit=3.00.\n"
                 "Current params: outer_dia_mm=30, num_blades=20, blade_thickness_mm=2.0, blade_height_mm=5.0.\n"
                 "Valid params: outer_dia_mm(18-40), blade_height_mm(3-10)."},

    {"id": "v03", "label": '{"converge_length_mm": 25.0}',
     "domain": "formwerk", "part": "nozzle",
     "scenario": "Part: nozzle. Score: 0.875 (7/8 pass).\n"
                 "FAIL: converge_angle: value=12.5 limit=15.0 — Converge half-angle 15-45 deg.\n"
                 "Current params: chamber_radius_mm=25, throat_radius_mm=8, converge_length_mm=60.\n"
                 "Valid params: converge_length_mm(10-60)."},

    # ── HEAT EXCHANGER (train) ─────────────────────────────────────────────
    {"id": "h01", "label": '{"cell_size_mm": 8.0}',
     "domain": "formwerk", "part": "heatexchanger",
     "scenario": "Part: heatexchanger. Score: 0.833 (5/6 pass).\n"
                 "FAIL: cell_min: value=3.0 limit=5.0 — Cell >= 5mm.\n"
                 "Current params: cell_size_mm=3.0.\n"
                 "Valid params: cell_size_mm(5-20)."},

    # ── LATTICE (train) ────────────────────────────────────────────────────
    {"id": "l01", "label": '{"strut_rad_mm": 0.6}',
     "domain": "formwerk", "part": "lattice",
     "scenario": "Part: lattice. Score: 0.857 (6/7 pass).\n"
                 "FAIL: strut_min: value=0.3 limit=0.4 — Strut >= 0.4mm.\n"
                 "Current params: strut_rad_mm=0.3.\n"
                 "Valid params: strut_rad_mm(0.4-1.5)."},

    # ── STATOR (train) ─────────────────────────────────────────────────────
    {"id": "s01", "label": '{"back_iron_mm": 5.0}',
     "domain": "formwerk", "part": "stator",
     "scenario": "Part: stator. Score: 0.833 (5/6 pass).\n"
                 "FAIL: back_iron: value=3.0 limit=4.0 — Back iron >= 4mm.\n"
                 "Current params: back_iron_mm=3.0.\n"
                 "Valid params: back_iron_mm(4-10)."},

    # ── RATTE (train) ──────────────────────────────────────────────────────
    {"id": "r01", "label": '{"num_regen_channels": 12}',
     "domain": "formwerk", "part": "ratte",
     "scenario": "Part: ratte. Score: 0.875 (7/8 pass).\n"
                 "FAIL: regen_min: value=6 limit=8 — Regen channels >= 8.\n"
                 "Current params: num_regen_channels=6.\n"
                 "Valid params: num_regen_channels(8-24)."},

    # ── MULTI-CONSTRAINT (validation — harder) ────────────────────────────
    {"id": "v04", "label": '{"wall_thick_mm": 3.5, "ring_depth_mm": 2.8, "pin_dia_mm": 19}',
     "domain": "formwerk", "part": "piston",
     "scenario": "Part: piston. Score: 0.750 (12/16 pass).\n"
                 "FAIL: wall_min: value=2.3 limit=2.5 — Wall >= 2.5mm.\n"
                 "FAIL: ring_clear: value=0.01 limit=0.10 — Ring depth leaves >= 10% wall.\n"
                 "FAIL: pin_ratio_min: value=0.19 limit=0.22 — Pin/bore >= 0.22.\n"
                 "FAIL: skirt_ratio_min: value=0.82 limit=0.85 — Skirt/bore >= 0.85.\n"
                 "Current params: wall_thick_mm=2.3, ring_depth_mm=3.5, pin_dia_mm=15, "
                 "skirt_length_mm=63, bore_mm=77.\n"
                 "Valid params: wall_thick_mm(2.5-6), ring_depth_mm(2.5-4.0), "
                 "pin_dia_mm(17-22), skirt_length_mm(65-85)."},

    {"id": "v05", "label": '{"outer_dia_mm": 22, "num_blades": 18, "blade_thickness_mm": 1.8, "blade_height_mm": 6}',
     "domain": "formwerk", "part": "turbinerotor",
     "scenario": "Part: turbinerotor. Score: 0.833 (15/18 pass).\n"
                 "FAIL: solidity_min: value=0.18 limit=0.80 — Solidity = nBlades*thickness / (2*pi*meanR).\n"
                 "FAIL: blade_ar_min: value=2.5 limit=3.0 — Blade AR >= 3 (aero).\n"
                 "FAIL: tip_speed: value=132 limit=120 — Tip speed <= 120 m/s at 42000 RPM.\n"
                 "Current params: outer_dia_mm=38, hub_dia_mm=14, num_blades=10, "
                 "blade_thickness_mm=1.1, blade_height_mm=5.\n"
                 "Valid params: outer_dia_mm(18-40), hub_dia_mm(6-16), num_blades(8-20), "
                 "blade_thickness_mm(0.8-2.0), blade_height_mm(3-10)."},

    # ── TOPOLOGY OPTIMIZATION (train) ──────────────────────────────────
    {"id": "to01", "label": '{"volume_fraction": 0.30, "removal_threshold": 0.15}',
     "domain": "formwerk", "part": "topobracket",
     "scenario": "Part: topobracket. Score: 0.800 (4/5 pass).\n"
                 "FAIL: mass_max: value=180 limit=150 — Mass too high, need more material removal.\n"
                 "Current params: volume_fraction=0.45, removal_threshold=0.10.\n"
                 "Lower volume_fraction removes more material. Higher removal_threshold is more aggressive.\n"
                 "Valid params: volume_fraction(0.20-0.60), removal_threshold(0.05-0.30), "
                 "n_topo_iterations(3-10), min_feature_mm(0.5-2.0)."},

    {"id": "to02", "label": '{"min_feature_mm": 1.5, "n_topo_iterations": 8}',
     "domain": "formwerk", "part": "topobracket",
     "scenario": "Part: topobracket. Score: 0.800 (4/5 pass).\n"
                 "FAIL: am_overhang: overhang=12% limit=5% — Too many unsupported overhangs.\n"
                 "Current params: min_feature_mm=0.5, n_topo_iterations=3.\n"
                 "Increase min_feature_mm to prevent thin unsupported features. More iterations = smoother.\n"
                 "Valid params: min_feature_mm(0.5-2.0), n_topo_iterations(3-10)."},

    {"id": "gb01", "label": '{"cell_min_mm": 5, "thick_max": 0.45}',
     "domain": "formwerk", "part": "gradedbracket",
     "scenario": "Part: gradedbracket. Score: 0.857 (6/7 pass).\n"
                 "FAIL: mass_max: value=250 limit=220 — Too heavy.\n"
                 "Current params: cell_min_mm=4, thick_max=0.55.\n"
                 "Increase cell_min_mm (sparser dense zone) or decrease thick_max (thinner walls).\n"
                 "Valid params: cell_min_mm(3-8), cell_max_mm(10-20), thick_min(0.10-0.25), thick_max(0.30-0.60)."},
]

# ── Live evaluation: actually build the part and check the score ──────────

def evaluate_live(prediction_json: str, scenario: dict) -> dict:
    """Run the actual Formwerk evaluator with the predicted params."""
    import tempfile
    try:
        params = json.loads(prediction_json)
    except json.JSONDecodeError:
        return {"correct": False, "score": 0.0, "reason": "Invalid JSON output"}

    part = scenario.get("part", "piston")

    # Write params to temp file and evaluate
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(params, f)
        params_file = f.name

    try:
        result = subprocess.run(
            ["dotnet", "run", "--project", str(NEWRON_ROOT),
             "--", "evaluate", part, params_file, "1.0"],
            capture_output=True, text=True, timeout=30)

        report_path = Path.home() / "NewRon" / "Output" / "report.json"
        if report_path.exists():
            report = json.loads(report_path.read_text())
            score = report.get("overall_score", 0)
            n_pass = sum(1 for c in report.get("constraints", []) if c.get("passed"))
            n_total = len(report.get("constraints", []))
            return {
                "correct": score >= 0.99,
                "score": score,
                "n_pass": n_pass,
                "n_total": n_total,
                "reason": f"Score {score:.3f} ({n_pass}/{n_total})"
            }
    except Exception as e:
        return {"correct": False, "score": 0.0, "reason": str(e)}
    finally:
        os.unlink(params_file)

    return {"correct": False, "score": 0.0, "reason": "No report generated"}
