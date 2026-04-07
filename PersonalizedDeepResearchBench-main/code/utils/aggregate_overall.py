import os
import argparse
import re
from pathlib import Path


def extract_overall_score(file_path):
    """Extract the 'Overall Score' value from the given result file."""
    if not os.path.exists(file_path):
        print(f"[Warning] File not found: {file_path}")
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Match pattern like "P Overall Score: 3.9998" or "Q Overall Score: 4.0282"
    match = re.search(r'Overall Score:\s*([0-9.]+)', content)
    if match:
        return float(match.group(1))
    else:
        print(f"[Warning] No 'Overall Score' found in {file_path}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Aggregate P, Q, R results into an overall score.")
    parser.add_argument("--base_dir", type=str, required=True, help="Base result directory (e.g., results_judged_by_gpt5_revisecriteria_intscore)")
    parser.add_argument("--target_model", type=str, required=True, help="Model name (e.g., claude_3.7_latest)")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory for aggregated results.")
    args = parser.parse_args()

    # Define paths
    p_file = os.path.join(args.base_dir, "personalization", args.target_model, "personalization_result.txt")
    q_file = os.path.join(args.base_dir, "quality", args.target_model, "quality_result.txt")
    r_file = os.path.join(args.base_dir, "reliability", args.target_model, "reliability_result.txt")

    print("Reading from:")
    print(f"  P: {p_file}")
    print(f"  Q: {q_file}")
    print(f"  R: {r_file}")

    # Extract scores
    p_score = extract_overall_score(p_file)
    q_score = extract_overall_score(q_file)
    r_score = extract_overall_score(r_file)

    # Compute average (ignore missing)
    valid_scores = [s for s in [p_score, q_score, r_score] if s is not None]
    if not valid_scores:
        print("[Error] No valid scores found.")
        return

    overall_avg = sum(valid_scores) / len(valid_scores)

    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    output_file = os.path.join(args.output_dir, "overall_result.txt")

    # Write results
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("==== Aggregated Evaluation Results ====\n")
        f.write(f"P Overall Score: {p_score if p_score is not None else 'N/A'}\n")
        f.write(f"Q Overall Score: {q_score if q_score is not None else 'N/A'}\n")
        f.write(f"R Overall Score: {r_score if r_score is not None else 'N/A'}\n")
        f.write("---------------------------------------\n")
        f.write(f"Final Overall Score: {overall_avg:.4f}\n")

    print(f"[Success] Aggregated overall score: {overall_avg:.4f}")
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    main()
