# PersonaDeepResearchBench

[中文说明 (Chinese README)](README_ZH.md)

PersonaDeepResearchBench provides a benchmark pipeline to evaluate deep-research style articles along three aspects:
- Personalization alignment
- Article quality
- Factual reliability

The main entry is `PersonaDeepResearchBench/run_eval.sh`, which sequentially invokes:
- `code/eval_personalization.py`
- `code/eval_quality.py`
- `code.utils.extract`, `code.utils.deduplicate`, `code.utils.scrape`, `code.utils.validate`, `code.utils.stat`

## Quick Start

- Python: 3.9+
- Install dependencies:
  - `pip install -r PersonaDeepResearchBench/requirements.txt`
- Required environment variables:
  - `OPENAI_API_KEY`: API key for an OpenAI-compatible endpoint
  - `BASE_URL`: Base URL of the OpenAI-compatible API (e.g., `https://api.openai.com/v1` or your proxy/self-hosted endpoint)
- Optional (recommended for reliability scraping):
  - `JINA_API_KEY`: Used by `r.jina.ai` to fetch webpage content

## Data Layout

Prepare the following folders/files (relative to `PersonaDeepResearchBench/`):
- Raw articles (required):
  - `data/test_data/raw_data/<MODEL>.jsonl`
  - Each line example: `{ "id": 1, "article": "...full article text from your model..." }`
- Cleaned articles (auto-generated):
  - `data/test_data/cleaned_data/<MODEL>.jsonl`
- Tasks with language info (examples provided):
  - `data/prompt_data/queries150.jsonl` (fields include `id`, `language`, `task`, etc.)
- User personas (examples provided):
  - Chinese: `data/persona_data/extend_personas.jsonl`
  - English: `data/persona_data/extend_personas_en.jsonl`
- Evaluation criteria (choose one; must align by `id` with tasks):
  - Directory: `data/criteria_data/`
  - Examples: `criteria_gpt5.jsonl`, `criteria_gpt5_revise.jsonl`, `criteria_gpt5_en.jsonl`, etc.
  - Note: The code defaults to `data/criteria_data/criteria.jsonl`, which is not present in this repo. Pass your chosen file via CLI or change the default in code.

## Run with the Bash Script

- Edit `PersonaDeepResearchBench/run_eval.sh`:
  - Set `TARGET_MODEL="YourModelName"` (must match the raw articles filename)
  - Adjust `QUERY_DATA_PATH`, `PERSONA_DATA_PATH`, `CRITERIA_FILE_PATH` as needed
  - Optional flags (uncomment in the script): `--limit`, `--skip_cleaning`, `--only_zh`, `--only_en`, `--force`
- Execute:
  - Linux/macOS: `bash PersonaDeepResearchBench/run_eval.sh`
  - Windows: run in Git Bash or WSL (the script is a bash script)

## Python Entry Points and Key Flags

- Personalization: `code/eval_personalization.py <target_model>`
  - `--raw_data_dir` default `data/test_data/raw_data`
  - `--cleaned_data_dir` default `data/test_data/cleaned_data`
  - `--max_workers` default `5`
  - `--query_file` default `data/prompt_data/queries.jsonl` (switch to `queries150.jsonl` if needed)
  - `--output_dir` default `results`
  - `--persona_file` default `data/persona_data/extended_personas.jsonl` (repo file is `extend_personas.jsonl`; adjust accordingly)
  - `--criteria_file` default `data/criteria_data/criteria.jsonl` (replace with an existing file under `criteria_data/`)
  - Optional: `--limit`, `--skip_cleaning`, `--only_zh`, `--only_en`, `--force`
- Quality: `code/eval_quality.py <target_model>`
  - Parameters are similar (no `--persona_file`).
- Reliability pipeline (same order as in `run_eval.sh`):
  - Extract: `python -u -m code.utils.extract --raw_data_path data/test_data/raw_data/<MODEL>.jsonl --output_path results/reliability/<MODEL>/extracted.jsonl --query_data_path data/prompt_data/queries150.jsonl --n_total_process 50`
  - Deduplicate: `python -u -m code.utils.deduplicate --raw_data_path results/reliability/<MODEL>/extracted.jsonl --output_path results/reliability/<MODEL>/deduplicated.jsonl --query_data_path data/prompt_data/queries150.jsonl --n_total_process 50`
  - Scrape (needs `JINA_API_KEY`): `python -u -m code.utils.scrape --raw_data_path results/reliability/<MODEL>/deduplicated.jsonl --output_path results/reliability/<MODEL>/scraped.jsonl --n_total_process 50`
  - Validate: `python -u -m code.utils.validate --raw_data_path results/reliability/<MODEL>/scraped.jsonl --output_path results/reliability/<MODEL>/validated.jsonl --query_data_path data/prompt_data/queries150.jsonl --n_total_process 50`
  - Stats: `python -u -m code.utils.stat --input_path results/reliability/<MODEL>/validated.jsonl --output_path results/reliability/<MODEL>/reliability_result.txt`

## Outputs

- Personalization: `results/personalization/<MODEL>/`
  - `personalization_results.jsonl`: per-item scores (`goal_alignment`, `content_alignment`, `presentation_fit`, `actionability_practicality`)
  - `personalization_result.txt`: averages and `P Overall Score`
- Quality: `results/quality/<MODEL>/`
  - `quality_results.jsonl`: per-item scores (`depth_insight`, `logical_coherence`, `clarity_readability`)
  - `quality_result.txt`: averages and `Q Overall Score`
- Reliability: `results/reliability/<MODEL>/`
  - `extracted.jsonl` → `deduplicated.jsonl` → `scraped.jsonl` → `validated.jsonl`
  - `reliability_result.txt`: `Factual Accuracy`, `Citation Coverage`, `R Overall Score`
- Logs: `results/output_logs/<MODEL>.log`

## Tips & Troubleshooting

- API configuration
  - You must set `BASE_URL`. For the official OpenAI API, use `https://api.openai.com/v1`; otherwise set your proxy/self-hosted endpoint.
  - You must set `OPENAI_API_KEY`.
  - If your model names differ from defaults in `code/utils/api.py` (`Model` and `FACT_Model`), change them there or pass custom model names when constructing `AIClient`.
- Data alignment
  - `queries*.jsonl`, `criteria*.jsonl`, and `raw_data/<MODEL>.jsonl` must align on `id`. Missing pairs will be skipped.
- Criteria file
  - Since `data/criteria_data/criteria.jsonl` is not included, point `--criteria_file` to an existing one (e.g., `criteria_gpt5.jsonl`, `criteria_gpt5_en.jsonl`).
- Windows
  - Use Git Bash or WSL to run `run_eval.sh`.
- Sanity check
  - Use `--limit 2` to validate the pipeline and directory writes quickly.

## Example Commands

- Personalization (Chinese only, limit 2):
```
python -u PersonaDeepResearchBench/code/eval_personalization.py \
  "MyModel" \
  --raw_data_dir PersonaDeepResearchBench/data/test_data/raw_data \
  --cleaned_data_dir PersonaDeepResearchBench/data/test_data/cleaned_data \
  --query_file PersonaDeepResearchBench/data/prompt_data/queries150.jsonl \
  --persona_file PersonaDeepResearchBench/data/persona_data/extend_personas.jsonl \
  --criteria_file PersonaDeepResearchBench/data/criteria_data/criteria_gpt5.jsonl \
  --output_dir PersonaDeepResearchBench/results/personalization/MyModel \
  --only_zh --limit 2
```

- Quality (English only):
```
python -u PersonaDeepResearchBench/code/eval_quality.py \
  "MyModel" \
  --raw_data_dir PersonaDeepResearchBench/data/test_data/raw_data \
  --cleaned_data_dir PersonaDeepResearchBench/data/test_data/cleaned_data \
  --query_file PersonaDeepResearchBench/data/prompt_data/queries150_en.jsonl \
  --criteria_file PersonaDeepResearchBench/data/criteria_data/criteria_gpt5_en.jsonl \
  --output_dir PersonaDeepResearchBench/results/quality/MyModel \
  --only_en
```

- Reliability (is as described in the command example above).

