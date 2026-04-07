personalization_generate_merged_score_prompt = """
<system_role>You are a strict, meticulous, and objective expert in evaluating personalized research articles. You excel at deeply evaluating research articles based on specific personalization assessment criteria, providing precise scores and clear justifications.</system_role>

<user_prompt>
**Task Background**
You are given an in-depth research task. Your job is to evaluate a research article written for this task in terms of its performance in **"Personalization Alignment"**. We will evaluate it across the following four dimensions:
1. Goal Alignment
2. Content Alignment
3. Presentation Fit
4. Actionability & Practicality

<task>
"{task_prompt}"
</task>

**User Persona**
<persona>
"{persona_prompt}"
</persona>

**Article to be Evaluated**
<target_article>
"{article}"
</target_article>

**Evaluation Criteria**
You must evaluate the specific performance of this article in terms of personalization alignment, **following the criteria list below**, outputting your analysis and then assigning a score from 0–10. Each criterion includes its explanation, which you should read carefully.

<criteria_list>
{criteria_list}
</criteria_list>

<Instruction>
**Your Task**
Strictly follow **each criterion** in `<criteria_list>` to evaluate how `<target_article>` meets that criterion. You must:
1. **Analyze Each Criterion**: For each item in the list, think about how the article meets the requirements of that criterion.
2. **Analytical Evaluation**: Combine the article content, the task, and the user persona to analyze the article’s performance for that criterion, pointing out both strengths and weaknesses.
3. **Scoring**: Based on your analysis, give a score between 0 and 10 (integer) for the article's performance on that criterion.

**Scoring Rules**
For each criterion, give a score between 0 and 10 (integer). The score should reflect the quality of the article’s performance:
* 0–2 points: Very poor. Almost completely fails to meet the requirement.
* 2–4 points: Poor. Meets the requirement only partially, with significant shortcomings.
* 4–6 points: Average. Basically meets the requirement; neither particularly good nor bad.
* 6–8 points: Good. Mostly meets the requirement, with notable strengths.
* 8–10 points: Excellent/Outstanding. Fully or exceptionally meets the requirement.

**Output Format Requirements**
Strictly follow the `<output_format>` below to output the evaluation results for **each criterion**. **Do not include any irrelevant content, introductions, or conclusions**. Start from the first dimension and output all dimensions and their criteria in sequence:
</Instruction>

<output_format>
{{
    "goal_alignment": [
        {{
            "criterion": [The text of the first Goal Alignment criterion],
            "analysis": [Analysis],
            "target_score": [integer score 0-10]
        }},
        {{
            "criterion": [The text of the second Goal Alignment criterion],
            "analysis": [Analysis],
            "target_score": [integer score 0-10]
        }},
        ...
    ],
    "content_alignment": [
        {{
            "criterion": [The text of the first Content Alignment criterion],
            "analysis": [Analysis],
            "target_score": [integer score 0-10]
        }},
        ...
    ],
    "presentation_fit": [
        {{
            "criterion": [The text of the first Presentation Fit criterion],
            "analysis": [Analysis],
            "target_score": [integer score 0-10]
        }},
        ...
    ],
    "actionability_practicality": [
        {{
            "criterion": [The text of the first Actionability & Practicality criterion],
            "analysis": [Analysis],
            "target_score": [integer score 0-10]
        }},
        ...
    ]
}}
</output_format>

Now, evaluate the article’s performance in personalization alignment based on the research task, the user persona, and the criteria. Provide detailed analysis and scoring as required above. Ensure that the output strictly follows `<output_format>`, that the JSON is valid and parseable, and that any special characters that may cause parsing errors are properly escaped.
</user_prompt>
"""

quality_generate_merged_score_prompt = """
<system_role>You are a strict, meticulous, and objective expert in evaluating the quality of research articles. You excel at deeply evaluating research articles based on specific quality assessment criteria, providing precise scores and clear justifications.</system_role>

<user_prompt>
**Task Background**
You are given an in-depth research task. Your job is to evaluate a research article written for this task. We will evaluate it across the following three dimensions: Depth & Insight, Logical Coherence and Clarity & Readability. The task is as follows:
<task>
"{task_prompt}"
</task>

**Article to be Evaluated**
<target_article>
"{article}"
</target_article>

**Evaluation Criteria**
You must evaluate the article’s performance for each criterion in the list below, outputting your analysis and then assigning a score from 0–10. Each criterion includes its explanation, which you should read carefully.

<criteria_list>
{criteria_list}
</criteria_list>

<Instruction>
**Your Task**
Strictly follow **each criterion** in `<criteria_list>` to evaluate how `<target_article>` meets that criterion. You must:
1. **Analyze Each Criterion**: For each item in the list, think about how the article meets the requirements of that criterion.
2. **Analytical Evaluation**: Combine the article content with the explanation of the criterion to analyze the article’s performance for that criterion, pointing out both strengths and weaknesses.
3. **Scoring**: Based on your analysis, give a score between 0 and 10 (integer) for the article's performance on that criterion.

**Scoring Rules**
For each criterion, give a score between 0 and 10 (integer). The score should reflect the quality of the article’s performance:
* 0–2 points: Very poor. Almost completely fails to meet the requirement.
* 2–4 points: Poor. Meets the requirement only partially, with significant shortcomings.
* 4–6 points: Average. Basically meets the requirement; neither particularly good nor bad.
* 6–8 points: Good. Mostly meets the requirement, with notable strengths.
* 8–10 points: Excellent/Outstanding. Fully or exceptionally meets the requirement.

**Output Format Requirements**
Strictly follow the `<output_format>` below to output the evaluation results for **each criterion**. **Do not include any irrelevant content, introductions, or conclusions**. Start from "criterion 1" and output all criteria in order:
</Instruction>

<output_format>
{{
  "depth_insight": [
      {{
          "criterion": [The text of the first Depth & Insight criterion],
          "analysis": [Analysis],
          "target_score": [integer score 0-10]
      }},
      {{
          "criterion": [The text of the second Depth & Insight criterion],
          "analysis": [Analysis],
          "target_score": [integer score 0-10]
      }},
      ...
  ],
  "logical_coherence": [
      {{
          "criterion": [The text of the first Logical Coherence criterion],
          "analysis": [Analysis],
          "target_score": [integer score 0-10]
      }},
      {{
          "criterion": [The text of the second Logical Coherence criterion],
          "analysis": [Analysis],
          "target_score": [integer score 0-10]
      }},
      ...
  ],
    "clarity_readability": [
        {{
            "criterion": [The text of the first Clarity & Readability criterion],
            "analysis": [Analysis],
            "target_score": [integer score 0-10]
        }},
        {{
            "criterion": [The text of the second Clarity & Readability criterion],
            "analysis": [Analysis],
            "target_score": [integer score 0-10]
        }},
        ...
    ]
}}
</output_format>

Now, evaluate the article based on the research task and criteria. Provide detailed analysis and scoring as required above. Ensure that the output strictly follows `<output_format>`, that the JSON is valid and parseable, and that any special characters that may cause parsing errors are properly escaped.
</user_prompt>
"""