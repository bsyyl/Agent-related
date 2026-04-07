import os
import argparse
from .io_utils import load_jsonl
from tqdm import tqdm

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    args = parser.parse_args()

    total_factual_claims = 0
    total_cicted_factual_claims = 0
    total_valid_factual_claims = 0

    data = load_jsonl(args.input_path)

    for d in tqdm(data):
        if not d['factual_claims']:
            continue
        for k,v in d['factual_claims_deduped'].items():
            total_factual_claims += len(v['facts'])
            if k == 'no_url' or k == '':
                continue
            else:
                total_cicted_factual_claims += len(v['facts'])
                if v['validate_error'] is not None:
                    continue
                for _c in v['validate_res']:
                    if _c['result'] == 'supported':
                        total_valid_factual_claims += 1
    
    factual_accuracy_score = (total_valid_factual_claims / total_cicted_factual_claims) * 10
    citation_coverage_score = (total_cicted_factual_claims / total_factual_claims) * 10
    r_overall_score = (factual_accuracy_score + citation_coverage_score) / 2

    with open(args.output_path, 'w') as f:
        f.write(f'Factual Accuracy: {factual_accuracy_score:.4f}\n')
        f.write(f'Citation Coverage: {citation_coverage_score:.4f}\n')
        f.write(f'R Overall Score: {r_overall_score:.4f}\n')