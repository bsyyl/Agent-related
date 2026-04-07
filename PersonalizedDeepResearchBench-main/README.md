<h1 align="center"> Towards Personalized Deep Research: Benchmarks and Evaluations</h1>
<div align="center">
<a href="LICENSE"><img src="https://img.shields.io/badge/Code_License-Apache%202.0-blue" alt="license"></a>
<a href="https://arxiv.org/abs/2509.25106" target="_blank"><img src=https://img.shields.io/badge/arXiv-b5212f.svg?logo=arxiv></a>
<a href="https://huggingface.co/papers/2509.25106" target="_blank"><img src="https://img.shields.io/badge/%F0%9F%A4%97%20HF%20Paper-blue?color=8A2BE2" alt="Hugging Face Paper"></a>
<a href="https://huggingface.co/datasets/PersonalAILab/PersonalizedDeepResearchBench" target="_blank"><img src="https://img.shields.io/badge/%F0%9F%A4%97%20HF%20Dataset-blue?color=00A651" alt="Hugging Face Dataset"></a>

</div>

## 📖 Overview

**Personalized Deep Research Bench (PDR-Bench)** is the first benchmark to **systematically evaluate personalization in Deep Research Agents (DRAs)**.  
It pairs **50 real-world deep-research tasks** across **10 domains** with **25 authentic user profiles**, yielding **250 personalized task–user pairs**.

Evaluation is conducted via the **PQR Framework**, which jointly measures:
- 🎯 **Personalization Alignment (P)** — user–task fit  
- 🧠 **Content Quality (Q)** — report depth and reasoning  
- 🔍 **Factual Reliability (R)** — factual soundness and citation integrity  



## 🧩 Benchmark Composition

![Data Construction Pipeline](pics/construction.jpg)

| Component         | Description                                                                                                  |
| ----------------- | ------------------------------------------------------------------------------------------------------------ |
| **Tasks**         | 50 complex research tasks across 10 domains (Education, Career, Health, Finance, etc.)                       |
| **User Profiles** | 25 authentic, structured personas with dynamic contexts (age, occupation, lifestyle, financial traits, etc.) |
| **Queries**       | 250 paired task–user scenarios simulating realistic deep research interactions                               |
| **Languages**     | Chinese and English                                                                                           |



## 🧮 PQR Evaluation Framework
![Framework Overview](pics/evaluation.jpg)

The **PQR Evaluation Framework** provides a holistic, user-centered methodology for assessing **Personalized Deep Research (PDR)** reports along three complementary axes:

---

### 🎯 **P — Personalization Alignment**

Evaluates how well a report aligns with the **user persona** and **task** through:

- **Dynamic Weighting**: LLM meta-evaluator assigns relative importance to personalization dimensions  
- **Granular Criteria Generation**: Creates task and persona specific sub-criteria for detailed assessment  
- **Dimension Scoring**: Computes a weighted score across four key dimensions:
  - 🎯 **Goal Alignment** — Alignment with the user’s goals  
  - 📚 **Content Alignment** — Relevance and depth suited to the user’s background  
  - ✍️ **Presentation Fit** — Style and structure matching user preferences  
  - 🧩 **Actionability** — Practical value and usefulness of insights  

---

### 🧠 **Q — Content Quality**

Assesses the intrinsic quality of report writing and reasoning, independent of personalization:

- **Dynamic Criteria Generation**: Produces task-specific sub-criteria for quality assessment  
- **Weighted Scoring** across three key dimensions:
  - 💡 **Depth & Insight** — Analytical richness and originality  
  - 🔗 **Logical Coherence** — Rigor and flow of reasoning  
  - 📖 **Clarity & Readability** — Language fluency and presentation quality  

---

### 🔍 **R — Factual Reliability**

Evaluates factual correctness and evidence grounding through automated verification:

- **Claim Extraction & Deduplication**: Identifies unique verifiable statements and their citations  
- **Automated Verification**: Uses retrieval and LLM judgment to check factual support  
- **Citation Metrics**:
  - ✅ **Factual Accuracy (FA)** — Proportion of claims supported by sources  
  - 🔗 **Citation Coverage (CC)** — Proportion of total claims properly cited  

---

Together, **P, Q, and R** form a unified framework balancing **personalization**, **quality**, and **reliability** for robust DRA evaluation.


## 🧪 Experiments

### Evaluated Systems
We benchmarked a broad range of systems, including:

| Category                            | Representative Models                                                    |
| ----------------------------------- | ------------------------------------------------------------------------ |
| **Commercial Deep Research Agents** | Gemini 2.5-Pro Deep Research, O3 Deep Research, Perplexity Deep Research |
| **Open-Source DRAs**                | OAgents, DeerFlow, MiroFlow                                              |
| **LLMs + Search Tools**             | GPT-4.1-Search, Claude 3.7-Sonnet-Search, Perplexity Sonar Reasoning Pro |
| **Memory Systems**                  | Mem0, Memory OS, O-Mem                                                   |

### Main Results


| Model                                   | Overall | GOAL | CONT | PRES | ACTI | DEIN | LOGC | CLAR |  FA  |  CC  |
|-----------------------------------------|:------:|:----:|:----:|:----:|:----:|:----:|:----:|:----:|:----:|:----:|
| **Commercial Deep Research Agents**     |   —    |  —   |  —   |  —   |  —   |  —   |  —   |  —   |  —   |  —   |
| Gemini-2.5-Pro Deep Research            |  **6.58**  | <u>5.27<u> | <u>5.78<u> | **5.83** | <u>4.56<u> | <u>5.32<u> | 6.13 | **6.16** | **8.40** | **9.26** |
| O3 Deep Research                        |  <u>6.11<u>  | **5.67** | **5.95** | <u>5.57<u> | **5.10** | **5.68** | **6.40** | <u>5.58<u> | 6.84 | 7.14 |
| Perplexity Deep Research                |  5.99  | 4.69 | 4.93 | 4.72 | 4.33 | 4.93 | 5.43 | 4.68 | <u>7.68<u> | <u>9.02<u> |
| **Open-Source Deep Research Agents**    |   —    |  —   |  —   |  —   |  —   |  —   |  —   |  —   |  —   |  —   |
| OAgents                                 |  **6.64**  | **6.68** | <u>6.44<u> | **7.13** | **6.92** | **6.99** | **7.44** | **6.85** | 3.77 | **8.32** |
| DeerFlow                                |  5.30  | 5.20 | 4.97 | 6.71 | 5.41 | 5.43 | 6.25 | 6.44 | <u>6.85<u> | <u>2.32<u> |
| MiroFlow                                |  <u>5.78<u>  | <u>6.65<u> | **6.45** | <u>7.03<u> | <u>6.65<u> | <u>6.53<u> | <u>7.31<u> | <u>6.68<u> | **7.29** | 0.44 |
| **LLM with Search Tools**               |   —    |  —   |  —   |  —   |  —   |  —   |  —   |  —   |  —   |  —   |
| Gemini-2.5-Pro w/Search                 |  **5.53**  | **4.85** | **5.20** | <u>5.61<u> | <u>4.19<u> | **4.54** | **5.57** | <u>5.41<u> | 6.99 | **6.62** |
| Claude-3.7-Sonnet w/Search              |  4.83  | 4.27 | 4.24 | 5.43 | **4.28** | <u>4.26<u> | 5.09 | 5.34 | <u>8.27<u> | 2.37 |
| Perplexity-Sonar-Reasoning-Pro          |  <u>5.02<u>  | 4.27 | 4.37 | 5.27 | 4.15 | 4.22 | 5.03 | 5.23 | **8.44** | <u>3.67<u> |
| GPT-4.1 w/Search                        |  4.28  | <u>4.59<u> | <u>4.86<u> | **5.74** | 4.07 | 4.21 | <u>5.27<u> | **5.54** | 6.75 | 0.10 |


**Key Findings**

* **Open-source Agents**: Achieve the strongest personalization, with OAgents scoring 6.64 and leading in GOAL, PRES, and LOGC. MiroFlow performs well in CONT and FA, but overall reliability is a weakness (e.g., OAgents' low FA of 3.77, and poor citation coverage in MiroFlow/DeerFlow).
* **Commercial Agents**: Provide more balanced quality and reliability, with Gemini-2.5-Pro Deep Research leading in FA and CC while maintaining strong quality scores. O3 Deep Research excels in personalization within this category but slightly lags in overall performance compared to open-source agents.
* **LLMs with Search Tools**: Underperform compared to specialized agents. While some models like Perplexity-Sonar-Reasoning-Pro achieve high FA (8.44), they fall short in CC and personalization. For example, GPT-4.1 w/Search almost fails in CC (0.10), indicating that adding search alone is insufficient to match the personalization and quality of dedicated deep research agents.
## 📁 Repository Structure

```
PersonaDeepResearchBench/
├── code/
│   ├── prompt/                   # Prompt templates
│   ├── utils/                    # Reliability scoring and tool functions  
│   ├── eval_personalization.py   # P: personalization scoring
│   ├── eval_quality.py           # Q: quality scoring
│   └── generate_criteria.py      # Dimension weights and criteria generating
├── data/
│   ├── criteria_data/            # Criteria data for Evaluation
│   ├── persona_data/             # 25 Personas
│   │   ├── personas_en.jsonl
│   │   └── personas_zh.jsonl
│   ├── prompt_data/              # user-task pairs(queries)
│   │   ├── queries150_en.jsonl   # 150 English queries
│   │   ├── queries150_zh.jsonl   # 150 Chinese queries
│   │   ├── queries250_en.jsonl   # 250 English queries
│   │   └── queries250_zh.jsonl   # 250 Chinese queries
│   ├── task_data/             
│   │   ├── tasks_en.jsonl        # 50 English deep research tasks
│   │   └── tasks_zh.jsonl        # 50 Chinese deep research tasks
│   ├── test_data/                 
│   │   ├── cleaned_data/         # Cleaned article data
│   │   └── raw_data/             # ← Put your TARGET_MODEL outputs here (model_name.jsonl)
│   ├── results/ 
│   │   ├── output_logs/          # Output logs during evaluation
│   │   ├── overall/              # P,Q,R overall scores and final overall score
│   │   ├── personalization/      # Personalization scoring results
│   │   ├── quality/              # Quality scoring results
│   │   └── reliability/          # Reliability scoring results
│── README.md                     # This file
│── requirements.txt              # Dependencies
└── run_eval.sh                   # Evaluation pipeline, set TARGET_MODEL then run
```

## 🚀 Quick Start

### Prerequisites
- Python: 3.9+
- OPENAI API key
- Jina API key

### Environment Setup

```bash
conda create -n pdrbench python=3.10
conda activate pdrbench
pip install -r requirements.txt
```
### API Configuration
```bash
# Set up OPENAI API key
export OPENAI_API_KEY=<your_api_key>

# Set up BASE_URL (optional)
export BASE_URL=<base_url>

# Set up Jina API key
export JINA_API_KEY=<your_api_key>
```

### Prepare Your Data
Run your DRA on the benchmark queries and save outputs in the required format:

**Input**: Use queries from `data/prompt_data/queries150_zh.jsonl`.
Each line contains a JSON object with a `"query"` field — this is the **input text** you should feed into your DRA.


**Output**: Save results to `data/test_data/raw_data/<model_name>.jsonl`

**Target format** (each line should contain):
```json
{
    "id": "query id", 
    "language": "task and user profile language",
    "taskid": "task id",
    "userid": "user id",
    "article": "generated deep research article"
}
```

### Run Evaluation

For detailed technical instructions and parameters, see [README_EN.md](docs/README_EN.md).

```bash
bash run_eval.sh
```

Evaluation results will be saved to:

```bash
data/results/
├── output_logs/
├── overall/
├── personalization/
├── quality/
└── reliability/
```

## 🌻 Acknowledgement

Our implementation builds upon the [DeepResearch Bench](https://github.com/Ayanami0730/deep_research_bench) and includes significant modifications and extensions to adapt it for the **Personalized Deep Research Bench (PDR-Bench)** project.
We sincerely thank the original authors for their excellent work.


## 📚 Citation

If you find this work useful, please ⭐ the repo and cite our paper.  

```bibtex
@misc{liang2025personalizeddeepresearchbenchmarks,
      title={Towards Personalized Deep Research: Benchmarks and Evaluations}, 
      author={Yuan Liang and Jiaxian Li and Yuqing Wang and Piaohong Wang and Motong Tian and Pai Liu and Shuofei Qiao and Runnan Fang and He Zhu and Ge Zhang and Minghao Liu and Yuchen Eleanor Jiang and Ningyu Zhang and Wangchunshu Zhou},
      year={2025},
      eprint={2509.25106},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2509.25106}, 
}
```
