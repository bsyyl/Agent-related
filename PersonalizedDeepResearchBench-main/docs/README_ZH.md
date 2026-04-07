# PersonaDeepResearchBench 使用说明

[English README](README_EN.md)

本项目提供一套对“深度调研”类文章的基准评测流程，涵盖三大维度：
- 个性化对齐（Personalization）
- 文章质量（Quality）
- 事实可靠性（Reliability）

核心脚本为 `PersonaDeepResearchBench/run_eval.sh`，内部依次调用：
- `code/eval_personalization.py`
- `code/eval_quality.py`
- `code.utils.extract`、`code.utils.deduplicate`、`code.utils.scrape`、`code.utils.validate`、`code.utils.stat`

---

## 快速开始

1) 准备环境
- Python: 3.9+
- 安装依赖：`pip install -r PersonaDeepResearchBench/requirements.txt`
- 环境变量（必需）：
  - `OPENAI_API_KEY`: 兼容 OpenAI 接口的 API Key
  - `BASE_URL`: 兼容 OpenAI 的接口地址，例如 `https://api.openai.com/v1` 或你的自托管代理地址
- 环境变量（用于网页抓取的可靠性评测，推荐）：
  - `JINA_API_KEY`: 用于 `r.jina.ai` 抓取网页内容

2) 准备数据目录
- 原始文章（必须）：将模型输出的原始文章按 JSONL 存放到：
  - `data/test_data/raw_data/<MODEL>.jsonl`
  - 行格式示例：`{"id": 1, "article": "……模型生成的全文……"}`
- 清洗文章（自动生成）：
  - 由评测脚本自动写入 `data/test_data/cleaned_data/<MODEL>.jsonl`
- 任务与语言信息（已提供示例）：
  - `data/prompt_data/queries150.jsonl`（中英字段：`id`、`language`、`task` 等）
- 用户画像（已提供示例）：
  - 中文：`data/persona_data/extend_personas.jsonl`
  - 英文：`data/persona_data/extend_personas_en.jsonl`
- 评测标准（从以下中选择其一；需与任务 `id` 对齐）：
  - 目录：`data/criteria_data/`
  - 示例：`criteria_gpt5.jsonl`、`criteria_gpt5_revise.jsonl`、`criteria_gpt5_en.jsonl` 等
  - 注意：脚本默认使用 `data/criteria_data/criteria.jsonl`，仓库中无该文件，请将你选择的标准文件路径显式传参或在脚本中修改。

3) 运行评测（推荐通过 Bash）
- 编辑 `PersonaDeepResearchBench/run_eval.sh`：
  - 设置 `TARGET_MODEL="你的模型名"`（需与原始文章文件名一致）
  - 按需设置：`QUERY_DATA_PATH`、`PERSONA_DATA_PATH`、`CRITERIA_FILE_PATH`
  - 可选开关（取消注释即可）：`--limit`、`--skip_cleaning`、`--only_zh`、`--only_en`、`--force`
- 执行：
  - Linux/Mac: `bash PersonaDeepResearchBench/run_eval.sh`
  - Windows: 请在 Git Bash/WSL 中执行（脚本为 bash 格式）。

---

## 脚本与参数

- 个性化评测：`code/eval_personalization.py <target_model>`
  - 关键参数：
    - `--raw_data_dir` 默认 `data/test_data/raw_data`
    - `--cleaned_data_dir` 默认 `data/test_data/cleaned_data`
    - `--max_workers` 线程数，默认 `5`
    - `--query_file` 任务清单，默认 `data/prompt_data/queries.jsonl`（如用 150 条，请改为 `queries150.jsonl`）
    - `--output_dir` 输出目录，默认 `results`
    - `--persona_file` 画像文件，默认 `data/persona_data/extended_personas.jsonl`（仓库为 `extend_personas.jsonl`，请按需调整）
    - `--criteria_file` 评测标准文件，默认 `data/criteria_data/criteria.jsonl`（需改为真实存在的标准文件）
    - 可选：`--limit`、`--skip_cleaning`、`--only_zh`、`--only_en`、`--force`
- 质量评测：`code/eval_quality.py <target_model>`
  - 参数与上面基本一致（去除了 `--persona_file`）。
- 可靠性评测流水线（以 `run_eval.sh` 为准，逐步执行）：
  - 提取事实与引用：
    - `python -u -m code.utils.extract --raw_data_path data/test_data/raw_data/<MODEL>.jsonl --output_path results/reliability/<MODEL>/extracted.jsonl --query_data_path data/prompt_data/queries150.jsonl --n_total_process 50`
  - 去重：
    - `python -u -m code.utils.deduplicate --raw_data_path results/reliability/<MODEL>/extracted.jsonl --output_path results/reliability/<MODEL>/deduplicated.jsonl --query_data_path data/prompt_data/queries150.jsonl --n_total_process 50`
  - 抓取引用页面内容（需 `JINA_API_KEY`）：
    - `python -u -m code.utils.scrape --raw_data_path results/reliability/<MODEL>/deduplicated.jsonl --output_path results/reliability/<MODEL>/scraped.jsonl --n_total_process 50`
  - 验证事实：
    - `python -u -m code.utils.validate --raw_data_path results/reliability/<MODEL>/scraped.jsonl --output_path results/reliability/<MODEL>/validated.jsonl --query_data_path data/prompt_data/queries150.jsonl --n_total_process 50`
  - 统计得分：
    - `python -u -m code.utils.stat --input_path results/reliability/<MODEL>/validated.jsonl --output_path results/reliability/<MODEL>/reliability_result.txt`

---

## 输出结果

- 个性化：`results/personalization/<MODEL>/`
  - `personalization_results.jsonl`（逐条评分详情，含维度：`goal_alignment`、`content_alignment`、`presentation_fit`、`actionability_practicality`）
  - `personalization_result.txt`（汇总均值与 `P Overall Score`）
- 质量：`results/quality/<MODEL>/`
  - `quality_results.jsonl`（逐条评分详情，含维度：`depth_insight`、`logical_coherence`、`clarity_readability`）
  - `quality_result.txt`（汇总均值与 `Q Overall Score`）
- 可靠性：`results/reliability/<MODEL>/`
  - `extracted.jsonl` → `deduplicated.jsonl` → `scraped.jsonl` → `validated.jsonl`
  - `reliability_result.txt`（`Factual Accuracy`、`Citation Coverage`、`R Overall Score`）
- 日志：`results/output_logs/<MODEL>.log`

---

## 注意事项与排错

- 接口配置
  - `BASE_URL` 必须设置；使用官方 OpenAI 请设为 `https://api.openai.com/v1`，或根据你的代理/私有部署修改。
  - `OPENAI_API_KEY` 必须设置；若模型名称与默认不符，请在 `code/utils/api.py` 中修改 `Model`/`FACT_Model`，或给 `AIClient` 传入自定义 `model`。
- 数据对齐
  - `queries*.jsonl`、`criteria*.jsonl`、`raw_data/<MODEL>.jsonl` 三者的 `id` 必须一致，否则会出现“缺少标准/缺少文章”的告警并被跳过。
- Windows 运行
  - `run_eval.sh` 为 bash 脚本，建议在 Git Bash 或 WSL 中执行。
- 最小化测试
  - 可在 `run_eval.sh` 中启用 `--limit 2` 先跑通流程与目录写入。

---

## 示例命令（直接运行 Python）

- 个性化（仅中文，限制 2 条）：
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

- 质量（仅英文）：
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

- 可靠性（整条流水线见上文命令示例）。
