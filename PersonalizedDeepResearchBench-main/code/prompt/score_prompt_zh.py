personalization_generate_merged_score_prompt = """
<system_role>你是一名严格、细致、客观的个性化调研文章评估专家。你擅长根据具体的个性化评估标准，对调研文章进行深入评估，并给出精确的评分和清晰的理由。</system_role>

<user_prompt>
**任务背景**
有一个深度调研任务，你需要评估针对该任务撰写的一篇调研文章对于提问用户在“个性化对齐程度”方面的表现。我们会从以下四个维度进行评估：
1. 目标需求理解与匹配度（Goal Alignment）
2. 内容偏好（Content Alignment）
3. 表达方式匹配（Presentation Fit）
4. 可操作性与实用价值（Actionability & Practicality）

<task>
"{task_prompt}"
</task>

**用户画像**
<persona>
"{persona_prompt}"
</persona>

**待评估文章**
<target_article>
"{article}"
</target_article>

**评估标准**
现在，你需要根据以下**评判标准列表**，逐条评估这篇文章在个性化对齐方面的具体表现，输出分析，然后给出0-10的分数。每个标准都附有其解释，请仔细理解。

<criteria_list>
{criteria_list}
</criteria_list>

<Instruction>
**你的任务**
请严格按照 `<criteria_list>` 中的**每一条标准**，评估 `<target_article>` 在该标准上的具体表现。你需要：
1. **逐条分析**：针对列表中的每一条标准，思考文章是如何满足该标准要求的。
2. **分析评估**：结合文章内容、任务和用户画像，分析文章在该条标准上的表现，指出其优点和不足。
3. **打分**：基于你的分析，为文章在该条标准上的表现打分（0-10分）。

**打分规则**
对每一条标准，为文章打分，打分范围为 0-10 分（整数）。分数高低应体现文章在该标准上表现的好坏：
* 0-2分：表现很差。几乎完全不符合标准要求。
* 2-4分：表现较差。少量符合标准要求，但有明显不足。
* 4-6分：表现中等。基本符合标准要求，不好不坏。
* 6-8分：表现较好。大部分符合标准要求，有可取之处。
* 8-10分：表现出色/极好。完全或超预期符合标准要求。

**输出格式要求**
请**严格**按照下列`<output_format>`格式输出每一条标准的评估结果，**不要包含任何其他无关内容、引言或总结**。从第一个维度开始，按顺序输出所有维度及其标准的评估：
</Instruction>

<output_format>
{{
    "goal_alignment": [
        {{
            "criterion": [需求理解与匹配度的第一条评判标准文本内容],
            "analysis": [分析],
            "target_score": [0-10的整数]
        }},
        {{
            "criterion": [需求理解与匹配度的第二条评判标准文本内容],
            "analysis": [分析],
            "target_score": [0-10的整数]
        }},
        ...
    ],
    "content_alignment": [
        {{
            "criterion": [内容偏好的第一条评判标准文本内容],
            "analysis": [分析],
            "target_score": [0-10的整数]
        }},
        ...
    ],
    "presentation_fit": [
        {{
            "criterion": [表达方式匹配的第一条评判标准文本内容],
            "analysis": [分析],
            "target_score": [0-10的整数]
        }},
        ...
    ],
    "actionability_practicality": [
        {{
            "criterion": [可操作性与实用价值的第一条评判标准文本内容],
            "analysis": [分析],
            "target_score": [0-10的整数]
        }},
        ...
    ]
}}
</output_format>

现在，请根据调研任务、用户画像和标准，对文章在个性化对齐程度上的表现进行评估，并按照上述要求给出详细的分析和评分，请确保输出格式遵守上述`<output_format>`，而且保证其中的json格式可以解析，注意避免所有可能导致json解析错误的要转义的符号。
</user_prompt>
"""


quality_generate_merged_score_prompt = """
<system_role>你是一名严格、细致、客观的调研文章质量评估专家。你擅长根据具体的评估标准，对调研文章进行深入评估，并给出精确的评分和清晰的理由。</system_role>

<user_prompt>
**任务背景**
有一个深度调研任务，你需要评估针对该任务撰写的一篇调研文章。我们会从以下三个维度评估文章：内容深度与洞察力Depth & Insight、逻辑连贯性Logical Coherence、清晰度与可读性Clarity & Readability。内容如下：
<task>
"{task_prompt}"
</task>

**待评估文章**
<target_article>
"{article}"
</target_article>

**评估标准**
现在，你需要根据以下**评判标准列表**，逐条评估这篇文章的表现，输出分析，然后给出0-10的分数。每个标准都附有其解释，请仔细理解。

<criteria_list>
{criteria_list}
</criteria_list>

<Instruction>
**你的任务**
请严格按照 `<criteria_list>` 中的**每一条标准**，评估 `<target_article>` 在该标准上的具体表现。你需要：
1.  **逐条分析**：针对列表中的每一条标准，思考文章是如何满足该标准要求的。
2.  **分析评估**：结合文章内容与标准解释，分析文章在每一条标准上的表现，指出其优点和不足。
3.  **打分**：基于你的分析，为文章在该条标准上的表现打分（0-10分）。

**打分规则**
对每一条标准，为文章打分，打分范围为 0-10 分（整数）。分数高低应体现文章在该标准上表现的好坏：
*   0-2分：表现很差。几乎完全不符合标准要求。
*   2-4分：表现较差。少量符合标准要求，但有明显不足。
*   4-6分：表现中等。基本符合标准要求，不好不坏。
*   6-8分：表现较好。大部分符合标准要求，有可取之处。
*   8-10分：表现出色/极好。完全或超预期符合标准要求。

**输出格式要求**
请**严格**按照下列`<output_format>`格式输出每一条标准的评估结果，**不要包含任何其他无关内容、引言或总结**。从"标准1"开始，按顺序输出所有标准的评估：
</Instruction>

<output_format>
{{
  "depth_insight": [
      {{
          "criterion": [内容深度与洞察力维度的第一条评判标准文本内容],
          "analysis": [分析],
          "target_score": [0-10的整数]
      }},
      {{
          "criterion": [内容深度与洞察力维度的第二条评判标准文本内容],
          "analysis": [分析],
          "target_score": [0-10的整数]
      }},
      ...
  ],
  "logical_coherence": [
      {{
          "criterion": [逻辑连贯性的第一条评判标准文本内容],
          "analysis": [分析],
          "target_score": [0-10的整数]
      }},
      {{
          "criterion": [逻辑连贯性的第二条评判标准文本内容],
          "analysis": [分析],
          "target_score": [0-10的整数]
      }},
      ...
  ],
    "clarity_readability": [
        {{
            "criterion": [清晰度与可读性维度的第一条评判标准文本内容],
            "analysis": [分析],
            "target_score": [0-10的整数]
        }},
        {{
            "criterion": [清晰度与可读性维度的第二条评判标准文本内容],
            "analysis": [分析],
            "target_score": [0-10的整数]
        }},
        ...
    ]
}}
</output_format>

现在，请根据调研任务和标准，对文章进行评估，并按照上述要求给出详细的分析和评分，请确保输出格式遵守上述`<output_format>`，而且保证其中的json格式可以解析，注意所有可能导致json解析错误的要转义的符号。
</user_prompt>
"""