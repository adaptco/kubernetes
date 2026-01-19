
import json
import argparse
import math

def calculate_diff(receipt_golden: dict, receipt_latest: dict, tolerance: float) -> dict:
    """
    Compares two receipts and returns a diff report.
    """
    golden_anchors = receipt_golden.get("anchors", {})
    latest_anchors = receipt_latest.get("anchors", {})
    
    regressions = {}
    
    all_anchor_names = set(golden_anchors.keys()) | set(latest_anchors.keys())
    
    for name in all_anchor_names:
        golden_pos = golden_anchors.get(name)
        latest_pos = latest_anchors.get(name)
        
        if not golden_pos:
            regressions[name] = {"change_type": "added", "position": latest_pos}
            continue
        
        if not latest_pos:
            regressions[name] = {"change_type": "removed", "position": golden_pos}
            continue
            
        distance = math.sqrt(
            (golden_pos['x'] - latest_pos['x'])**2 +
            (golden_pos['y'] - latest_pos['y'])**2 +
            (golden_pos['z'] - latest_pos['z'])**2
        )
        
        if distance > tolerance:
            regressions[name] = {
                "change_type": "moved",
                "distance_mm": round(distance, 4),
                "from": golden_pos,
                "to": latest_pos,
            }
            
    return {
        "metadata": {
            "golden_source": receipt_golden.get("metadata", {}).get("source_file"),
            "latest_source": receipt_latest.get("metadata", {}).get("source_file"),
            "tolerance_mm": tolerance,
        },
        "causal_summary": regressions
    }

def main():
    """Main function to run the diff tool."""
    parser = argparse.ArgumentParser(description="Diff two CAM receipts.")
    parser.add_argument("golden_receipt", help="Path to the golden master receipt.")
    parser.add_argument("latest_receipt", help="Path to the latest generated receipt.")
    parser.add_argument("--tol_mm", type=float, default=0.25, help="Tolerance in millimeters for anchor drift.")
    args = parser.parse_args()

    with open(args.golden_receipt, 'r') as f:
        golden = json.load(f)
        
    with open(args.latest_receipt, 'r') as f:
        latest = json.load(f)
        
    diff_report = calculate_diff(golden, latest, args.tol_mm)
    
    # Output the diff report as JSON to stdout
    print(json.dumps(diff_report, indent=2))

if __name__ == "__main__":
    main()
