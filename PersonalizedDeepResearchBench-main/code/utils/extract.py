import multiprocessing
import json
import os
import argparse
import re
from functools import partial
from .io_utils import load_jsonl
from .api import call_model

prompt_template = """你会看到一篇研究报告，你的任务是仅提取文中的所有可被验证的事实性陈述（factual claims）。

## 事实性陈述的定义
事实性陈述是关于外部世界客观状态的、可被验证的陈述。它描述的是已经发生的事实、可量化的数据、公认的分类或科学规律，而不是作者的主观看法、意图、计划或对未来的预测，也不是对报告本身计划或结构的描述。

## 事实性陈述识别指南

### 应提取的类型 (示例)
* **具体数据和统计**: "2023年，全球电动汽车销量达到1410万辆。"
* **已发生的历史事件**: "该公司于2010年在中国上海成立。"
* **公认的分类或定义**: "李强基于收入、教育和职业构造了一个社会经济地位指数（SES），将社会划分为7个等级[15]。"
* **引用的研究发现**: "研究表明，超过8小时的睡眠对记忆力巩固至关重要[8]。"

### 应排除的类型 (示例)
* **目标与意图**: 任何描述本文档或项目“目的”、“目标”、“旨在”做什么的陈述。
    * 例如： "本报告的目标是将个人创作活动系统化。" 或 "本项目旨在验证小额营收模式。"
* **计划与方案**: 对未来行动、策略或内容的规划。
    * 例如： "内容支柱包括：旅行手绘日记、过程拆解、工具测评..." 或 "我们将分三个阶段执行该计划。"
* **对文档自身的描述**: 介绍报告结构或内容的陈述。
    * 例如： "本报告为...的3个月品牌与运营执行手册。" 或 "第三章将详细讨论市场分析。"
* **预测与推测**: 对未来可能发生的事情的预估或猜想。
    * 例如： "预计该策略将提升20%的用户粘性。" 或 "这可能会带来新的商业机会。"
* **观点与建议**: 作者的主观判断、看法或提出的建议。
    * 例如： "我们认为这是一个关键的突破口。" 或 "因此，我们建议采用A方案。"
* **研究方法**: 描述研究或工作将如何开展的过程。
    * 例如： "本研究将采用定性与定量相结合的方法。"

---

## 提取规则与输出格式
对于你找到的每一个事实性陈述，请判断它是否附带了参考文献引用，并提取 (fact, ref_idx, url) 三元组。
正文中的引用可能以如下形式出现：
1. 一段文字+空格+数字，例如："李强基于收入、教育和职业构造了一个社会经济地位指数（SES），将社会划分为7个等级 15"
2. 一段文字+[（一个或多个)数字]，例如："李强基于收入、教育和职业构造了一个社会经济地位指数（SES），将社会划分为7个等级[15]"
3. 一段文字+[（一个或多个)数字†(一些行号等内容)]，例如："李强基于收入、教育和职业构造了一个社会经济地位指数（SES），将社会划分为7个等级[15†L10][5L23][7†summary][9summary]"
4. [引用来源](引用链接)，例如："根据[ChinaFile: A Guide to Social Class in Modern China](https://www.chinafile.com/reporting-opinion/media/guide-social-class-modern-china)'s分类，中国社会可分为九个阶层"

提取的时候，注意以下事项：
1. 提取的fact应当是完整可理解的，而不是简单的词组或短语
2. 如果一个fact引用了多个文献，那么它应该对应多个三元组，例如如果引用了2个文献，则应该是(fact, ref_idx_1, url_1)和(fact, ref_idx_2, url_2)
3. 对于第三种形式的引用，ref_idx仅考虑第一个数字部分，不考虑其他指示具体位置的内容；对于第四种形式的引用（即引用来源和链接直接出现在正文中）的情况，ref_idx统一设置为0
4. 如果一个事实性陈述没有引用，则ref_idx和url均设为空字符串""

**输出要求**:
你应该返回一个 JSON 列表，列表中的每一项是一个三元组。对于不确定是否为事实性陈述的内容，请务必谨慎判断，宁可漏掉也不要误标。如果文章中没有事实性陈述，则返回空列表 `[]`。

**JSON 示例**:
```json
[
    {{
        "fact": "原文中的文本片段，注意中文引号要用全角, 英文引号前加单个反斜杠转义",
        "ref_idx": "该段文字引用的参考文献在参考文献列表中的索引，如果没有引用则为空字符串",
        "url": "该段文字引用的参考文献链接（从研究报告结尾的参考文献列表或引用处的括号中提取），如果没有引用则为空字符串"
    }},
    {{
        "fact": "2023年，全球电动汽车销量达到1410万辆。",
        "ref_idx": 12,
        "url": "https://iea.org/reports/global-ev-outlook-2024"
    }},
    {{
        "fact": "特斯拉于2010年在美国纳斯达克上市。",
        "ref_idx": "",
        "url": ""
    }},
    {{
        "fact": "研究表明，超过8小时的睡眠显著提升了记忆力巩固效果。",
        "ref_idx": 5,
        "url": "https://doi.org/10.1016/j.neurobiol.2020.101945"
    }},
    {{
        "fact": "根据[联合国环境规划署](https://www.unep.org/resources/emissions-gap-report-2023)的报告，2023年全球温室气体排放量达到历史最高水平。",
        "ref_idx": 0,
        "url": "[https://www.unep.org/resources/emissions-gap-report-2023](https://www.unep.org/resources/emissions-gap-report-2023)"
    }}
]

下面是研究报告的正文：
{report_text}

下面开始提取，直接输出json列表，不要输出任何闲聊或解释。"""

prompt_template_en = """You will see a research report, and your task is to extract **only** all verifiable factual statements (factual claims) from the text.

## Definition of Factual Statement
A factual statement is a verifiable claim about the objective state of the external world. It describes facts that have already occurred, quantifiable data, recognized classifications, or scientific laws — not the author’s subjective opinions, intentions, plans, or predictions about the future, nor descriptions about the report’s own plans or structure.

## Guidelines for Identifying Factual Statements

### Types to Extract (Examples)
* **Specific data and statistics**: "In 2023, global electric vehicle sales reached 14.1 million units."
* **Past historical events**: "The company was founded in Shanghai, China, in 2010."
* **Recognized classifications or definitions**: "Li Qiang constructed a socioeconomic status index (SES) based on income, education, and occupation, dividing society into seven classes [15]."
* **Cited research findings**: "Studies show that more than eight hours of sleep are critical for memory consolidation [8]."

### Types to Exclude (Examples)
* **Goals and intentions**: Any statement describing the “purpose,” “goal,” or “aim” of this document or project.
    * Example: "The goal of this report is to systematize personal creative activities." or "This project aims to verify the small-revenue model."
* **Plans and proposals**: Plans about future actions, strategies, or content.
    * Example: "The content pillars include: travel sketch diaries, process breakdowns, tool reviews..." or "We will execute this plan in three phases."
* **Self-referential statements about the document**: Statements introducing the report’s structure or content.
    * Example: "This report is a three-month brand and operations execution manual for..." or "Chapter 3 will discuss market analysis in detail."
* **Predictions and speculations**: Estimations or guesses about what might happen in the future.
    * Example: "This strategy is expected to increase user stickiness by 20%." or "This could create new business opportunities."
* **Opinions and recommendations**: The author’s subjective judgments, opinions, or suggestions.
    * Example: "We believe this is a key breakthrough." or "Therefore, we recommend adopting Plan A."
* **Research methods**: Descriptions of how the research or work will be conducted.
    * Example: "This study will adopt a mixed-method approach combining qualitative and quantitative analysis."

---

## Extraction Rules and Output Format
For each factual statement you find, determine whether it includes a reference citation, and extract it as a (fact, ref_idx, url) triple.
Citations in the text may appear in the following forms:
1. A piece of text + space + number, for example: "Li Qiang constructed a socioeconomic status index (SES) based on income, education, and occupation, dividing society into seven classes 15"
2. A piece of text + [number(s)], for example: "Li Qiang constructed a socioeconomic status index (SES) based on income, education, and occupation, dividing society into seven classes [15]"
3. A piece of text + [number(s)†(some line numbers etc.)], for example: "Li Qiang constructed a socioeconomic status index (SES) based on income, education, and occupation, dividing society into seven classes [15†L10][5L23][7†summary][9summary]"
4. [Cited source](citation link), for example: "According to [ChinaFile: A Guide to Social Class in Modern China](https://www.chinafile.com/reporting-opinion/media/guide-social-class-modern-china), Chinese society can be divided into nine classes"

When extracting, pay attention to the following:
1. The extracted fact should be a complete, understandable statement — not just a phrase or fragment.
2. If a fact cites multiple references, output multiple triples. For example, if it cites two references, output (fact, ref_idx_1, url_1) and (fact, ref_idx_2, url_2).
3. For the third form of citation, only take the first numeric part as ref_idx, ignoring indicators of specific locations. For the fourth form (where the source and link appear directly in the text), set ref_idx uniformly to 0.
4. If a factual statement has no citation, set both ref_idx and url to empty strings "".

**Output Requirements**:
You should return a JSON list, where each item is one triple. For content you are unsure about, err on the side of caution — it’s better to miss something than to mislabel it. If there are no factual statements in the article, return an empty list `[]`.

**JSON Example**:
```json
[
    {{
        "fact": "Text from the original article, use full-width Chinese quotation marks, escape English quotes with a single backslash",
        "ref_idx": "The index of the cited reference in the reference list for this statement; leave empty if none",
        "url": "The link of the cited reference (extracted from the report’s reference list or from the inline citation), leave empty if none"
    }},
    {{
        "fact": "In 2023, global electric vehicle sales reached 14.1 million units.",
        "ref_idx": 12,
        "url": "https://iea.org/reports/global-ev-outlook-2024"
    }},
    {{
        "fact": "Tesla went public on NASDAQ in 2010.",
        "ref_idx": "",
        "url": ""
    }},
    {{
        "fact": "Studies show that more than eight hours of sleep significantly enhances memory consolidation.",
        "ref_idx": 5,
        "url": "https://doi.org/10.1016/j.neurobiol.2020.101945"
    }},
    {{
        "fact": "According to [the United Nations Environment Programme](https://www.unep.org/resources/emissions-gap-report-2023), global greenhouse gas emissions reached a record high in 2023.",
        "ref_idx": 0,
        "url": "[https://www.unep.org/resources/emissions-gap-report-2023](https://www.unep.org/resources/emissions-gap-report-2023)"
    }}
]

Below is the main text of the research report:
{report_text}

Now start extracting, and directly output the JSON list — do not output any small talk or explanation."""


def clean_urls(input_text):
    # match [title](url) format
    pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

    def repl(match):
        title = match.group(1)
        url = match.group(2)
        # truncate #:~:text= and its content
        cut_idx = url.find('#:~:text=')
        if cut_idx != -1:
            url = url[:cut_idx]
        return f'[{title}]({url})'

    return pattern.sub(repl, input_text)


def remove_urls(input_text):
    # match [title](url) format, only remove the content in the parentheses, keep [title]
    pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    # replace [title](url) with [title]
    return pattern.sub(r'[\1]', input_text)


def clean_escape(input_text):
    # replace illegal escape characters
    input_text = input_text.replace("\\>", ">")
    input_text = input_text.replace("\\<", "<")
    input_text = input_text.replace("\\+", "+")
    input_text = input_text.replace("\\~", "~")
    return input_text


def run(data, output_path, id_to_lang_map):
    for i, d in enumerate(data):
        # Determine the language based on the id in the query data
        article_id = d.get('id')

        if not article_id:
            print(f"Article has no ID field, skipping extraction")
            continue

        if article_id not in id_to_lang_map:
            print(f"Language not found for article ID: {article_id}")
            continue

        lang = id_to_lang_map[article_id]
        if lang not in ["zh", "en"]:
            print(f"Unsupported language: {lang} for article ID: {article_id}")
            continue

        # Select the prompt based on the language
        if lang == "zh":
            user_prompt = prompt_template.format(report_text=d['article'])
        elif lang == 'en':
            user_prompt = prompt_template_en.format(report_text=d['article'])

        success = False
        retries = 0
        while retries < 3:
            retries += 1
            try:
                response = call_model(user_prompt)

                if response != "":
                    response = response.replace("```json", "").replace("```", "")
                    response = clean_escape(response)

                    d['factual_claims'] = json.loads(response)

                    for c in d['factual_claims']:
                        c['fact'] = remove_urls(c['fact'])

                    success = True
                    break
            except Exception as e:
                print(f"[{d['id']}-th instance: Retry {retries}] Failed: {repr(e)}")
                continue

        if not success:
            d['factual_claims'] = "extraction failed"
            print(f">>>>>>>>>> All attempts failed, article ID: {article_id}, cannot extract factual claims")
        else:
            print(f">>>>>>>>>> generating {d['id']}-th instance...")

        with open(output_path, "a+", encoding='utf-8') as f:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")



if __name__ == '__main__':
    import sys
    if sys.platform == 'win32':
        multiprocessing.set_start_method('spawn', force=True)
    else:
        multiprocessing.set_start_method('fork', force=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--output_path", type=str, required=True)
    parser.add_argument("--raw_data_path", type=str, required=True)
    parser.add_argument("--query_data_path", type=str, required=True, help="Path to query data with language information")
    parser.add_argument("--n_total_process", type=int, default=1)
    args = parser.parse_args()

    output_path = args.output_path

    # Load the query data to get language information
    query_data = load_jsonl(args.query_data_path)

    # Create a mapping from ID to language
    id_to_lang_map = {item['id']: item.get('language') for item in query_data if 'id' in item and 'language' in item}

    if not id_to_lang_map:
        raise ValueError("No valid language information found in query data")

    # Load the raw data
    raw_data = load_jsonl(args.raw_data_path)

    # If the output file exists, load the processed ids and filter out the processed instances
    if os.path.exists(output_path):
        processed = [d['id'] for d in load_jsonl(output_path)]
        data_to_process = [d for d in raw_data if d['id'] not in processed]
    else:
        data_to_process = raw_data

    # OpenAI deep research will add webpage snippets to the citations.
    # For fair comparison, we remove these snippets
    if 'openai' in args.raw_data_path:
        for d in data_to_process:
            d['article'] = clean_urls(d['article'])

    print(f"Processing {len(data_to_process)} instances...")

    n_total_process = args.n_total_process
    if n_total_process == 1:
        run(data_to_process, output_path, id_to_lang_map)
    elif n_total_process > 1:
        part_size = (len(data_to_process) + n_total_process - 1) // n_total_process
        data_splits = [data_to_process[i * part_size : (i + 1) * part_size] for i in range(n_total_process)]
        run_partial = partial(run, output_path=output_path, id_to_lang_map=id_to_lang_map)
        with multiprocessing.Pool(processes=n_total_process) as pool:
            results = pool.map(run_partial, data_splits)