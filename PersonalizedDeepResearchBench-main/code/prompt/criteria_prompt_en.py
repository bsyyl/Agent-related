# P - Personalization: Degree of Personalization Alignment
# 1. Goal Alignment: Whether the report accurately understands and responds to the user’s task goals and requirements
# 2. Content Alignment: Whether the research customizes the content selection according to the user’s interests, knowledge background, etc.
# 3. Presentation Fit: Whether the presentation style suits the user’s comprehension style (e.g., language style, depth of technical terminology, etc.)
# 4. Actionability & Practicality: Whether the report is feasible, practical, and helpful for decision-making for the user

# Personalization criteria generation pipeline
# Step 1: Based on the given task and user persona, have the model provide the percentage weight each of the four dimensions—
# Goal Alignment, Content Alignment, Presentation Fit, Actionability & Practicality—should account for in the overall evaluation criteria, output as JSON
# Step 2: For each dimension, have the model generate specific evaluation criteria based on the task and persona, and provide the weight for each criterion, output as JSON

personalization_eval_dimension_weight_prompt = """
<system_role>
You are an experienced evaluation expert for research articles. You excel at deeply understanding the goals, challenges, and key value points of a specific research task and the task initiator’s persona, and then setting **dynamic, reasonable, and well-justified** weights for evaluation dimensions in subsequent personalized article assessments.
</system_role>

<user_prompt>
Here is a deep research task, as follows:
<task>
"{task_prompt}"
</task>

The user persona is as follows:
<persona>
"{persona_prompt}"
</persona>

<instruction>
**Background**: The research team will conduct in-depth and comprehensive research based on the above `<task>` and `<persona>` and ultimately produce a high-quality, personalized research article.
**Your task**: As the evaluation expert, you need to set the weights of the personalized evaluation criteria for this specific `<task>`. The evaluation will revolve around the following four dimensions:
1. **Goal Alignment:** Whether the research sufficiently and accurately understands the relationship between the task and the user persona, extracts deep and implicit needs, and generates a personalized report based on them.
2. **Content Alignment:** Whether the research selects and customizes content according to the user’s interests, knowledge background, and preferences.
3. **Actionability & Practicality:** Whether the report is feasible, practical, and helpful for the user’s decision-making.
4. **Presentation Fit:** Whether the report’s language style, information structure, and presentation format match the user’s cognitive habits and medium preferences.

**Evaluation formula**:  
Total score = Goal Alignment * Goal Alignment weight + Content Alignment * Content Alignment weight + Actionability & Practicality * Actionability & Practicality weight + Presentation Fit * Presentation Fit weight. (**Note: The sum of all weights must be exactly 1.0**)

**Core requirements**:
1. **Deeply analyze the task and user persona**: Carefully study the specific content of `<task>`, its explicit goals, potential challenges, and hidden objectives. Combine this with `<persona>` to analyze the user’s needs, background, and preferences, and understand the core value of the task’s outcome.
2. **Dynamically assign weights**: Based on your analysis, assign weights to the four dimensions (use decimals between 0 and 1, e.g., 0.30). **The key is to recognize that different tasks and personas emphasize different aspects, so weights must be flexibly adjusted according to task characteristics and persona, not fixed.**
3. **Explain your reasoning**: Your analysis (`<analysis>`) **must clearly and specifically explain why each dimension is assigned a given weight**, and **directly link your reasoning to the requirements of `<task>` and the characteristics of `<persona>`**. This is critical for evaluating the quality of your work.
4. **Output in the standard format**: Strictly follow the example format below: first output `<analysis>` with detailed reasoning, then immediately provide `<json_output>` with the weight assignment results.

</instruction>

<examples_rationale>
Below are two examples that demonstrate **how to adjust the evaluation dimension weights and explain the reasoning based on changes in task nature and user persona**. Focus on learning the **thinking process and analytical method** in these examples, not simply copying their content or weight values.
</examples_rationale>

<example_1>
<task>
"I want to update my skincare products over the next month to choose ones suitable for my skin type and needs. My skin is combination type — my T-zone is oily, especially in the afternoon, while my cheeks are dry and feel tight after washing. Recently, I’ve been troubled by dull skin and some fine lines. My main skincare goals are anti-aging and brightening. My total budget is under 2000, and I want to first build a healthy skin barrier, then further improve my skin problems. I already have a morning and evening skincare routine using cleanser, toner, and cream. Please provide me with a skincare plan, including basic steps and product recommendations, compare ingredients, effects, and prices across different brands, and help me find the most suitable choice."
</task>
<persona>
"28-year-old female working in the internet industry, stays in air-conditioned rooms all year, wears makeup for 12 hours daily for video meetings, sensitive to ethanol, values oil control and long-lasting makeup during the day, prefers fragrance-free Japanese cosmeceutical brands. Needs to address T-zone shine and caking on cheeks. Has sufficient time at night for skincare and is willing to spend 3+ minutes for massage absorption."
</persona>
<output>
<analysis>
The core of this task is to provide a personalized skincare solution for a woman working in the internet industry, with the key value being whether the recommendations solve her actual problems. Therefore, the evaluation emphasizes the practicality of the suggestions, their accurate response to the user’s needs, and the clarity of expression.
* **Goal Alignment (0.40):** Evaluate whether the system goes beyond a literal understanding of the user’s task goals and performs deep analysis of the persona to uncover unstated or implicit needs. For example, “tightness after washing” + “oily T-zone, dry cheeks” indicate skin barrier damage and water-oil imbalance, so the core strategy should include “repair the barrier first, then treat each area separately.” This dimension measures the transformation from “data” to “insight,” which directly determines the value of the report, hence the highest weight.
* **Content Alignment (0.20):** This evaluates whether the proposed solutions (products, brands, services, and information) match the user’s consumption preferences, knowledge background, decision-making style, and values. For example, recommending Japanese cosmeceuticals, fragrance-free, and ethanol-free products. This dimension ensures the report content is acceptable and appealing to the user, thus a moderate weight.
* **Actionability & Practicality (0.30):** Focuses on whether the report’s recommendations are usable and effective for the user, e.g., within budget, feasible steps, ease of purchase. Hence a relatively high weight.
* **Presentation Fit (0.10):** Evaluates whether the presentation matches the user’s behavioral preferences. For a professional working woman, the language should be professional, concise, and logically clear, avoiding exaggerated marketing language. Since this is a secondary requirement, the weight is lower.
</analysis>
<json_output>
{{
    "goal_alignment": 0.40,
    "content_alignment": 0.20,
    "actionability_practicality": 0.30,
    "presentation_fit": 0.10
}}
</json_output>
</output>
</example_1>

<example_2>
<task>
"I am a beginner marathon runner planning to prepare for a full marathon over the next three months. My goal is to complete the race safely without injury. I can train about five days a week, about one hour each time, mainly in a nearby park or neighborhood roads. I do not have professional running equipment, only basic running shoes. I currently have no running experience and no specific pace target, but I want to gradually increase mileage, and the plan needs to fit into my daily life and work schedule, easy to stick to and flexible. Please create a personalized training plan for me based on this information."
</task>
<persona>
"Returning expat couple who value bilingual education. Live in a rainy area and need 50% indoor training alternatives. Have a pet dog that can join activities, and a children’s action camera. They care about calorie-tracking visualization and want to build a health-focused international family community."
</persona>
<output>
<analysis>
The primary goal of this task is “finish safely without injury,” with strong constraints on training time, venue, and equipment, plus the additional requirement of “50% indoor training due to rain.” The persona also includes preferences like family/pet participation, bilingual exposure, calorie tracking, and community building, which affect plan design and presentation.
* **Goal Alignment (0.30):** Evaluate whether the system performs deep analysis of the persona to uncover unstated needs, e.g., creatively solving the core pain points (rainy weather, indoor training) while meeting personalized preferences (family participation, data tracking, community building). High weight due to its importance.
* **Content Alignment (0.20):** Evaluate whether the report provides concrete solutions matching user preferences, e.g., recommending apps or devices for calorie tracking, suggesting how to use the pet dog for recovery runs. Moderate weight.
* **Actionability & Practicality (0.45):** This is the foundation of task success. The user clearly stated “rainy area, need 50% indoor alternatives,” which is a hard constraint. The primary goal is “complete safely without injury,” which requires a gradual, realistic, and safe training plan. Therefore, the highest weight.
* **Presentation Fit (0.05):** Serves as a baseline check to ensure the report mentions key persona information, thus lower weight.
</analysis>
<json_output>
{{
    "goal_alignment": 0.30,
    "content_alignment": 0.20,
    "actionability_practicality": 0.45,
    "presentation_fit": 0.05
}}
</json_output>
</output>
</example_2>

Now strictly follow the above instructions and methodology, and start your work for the following task:
<task>
"{task_prompt}"
</task>
<persona>
"{persona_prompt}"
</persona>
Please output your `<analysis>` and `<json_output>`.
</user_prompt>
"""

# Step 2 prompt
personalization_eval_criteria_prompt_goal_alignment = """
<system_role>
You are an experienced research article evaluation expert. You excel at breaking down abstract evaluation dimensions (such as "Goal Understanding and Personalization Insight") into actionable, clear evaluation criteria tailored to the specific research task and user persona, and assigning reasonable weights with explanations for each criterion.
</system_role>

<user_prompt>
**Background**: We are evaluating a research article written for the following research task under the dimension of Goal Alignment.
**Goal Alignment:** Whether the research fully and accurately understands the relationship between the task and the user persona, extracts deep and implicit needs,
and generates a personalized report based on that understanding, with a focus on performing user-centered, deeply personalized matching between the user persona and task requirements.

<task>
"{task_prompt}"
</task>

The user persona is as follows:
<persona>
"{persona_prompt}"
</persona>

<instruction>
Your goal:
For the Goal Alignment dimension of this research article, formulate a set of detailed, specific, and highly targeted evaluation criteria that are tightly aligned with the above <task> and <persona>. You need to:
1. Deeply analyze the user persona and task scenario: Thoroughly examine the background characteristics, knowledge structure, cognitive habits, and latent expectations of <persona>. Combine this with the specific application scenario of <task> to identify the user’s core explicit needs and deeper implicit needs.
2. Formulate personalized evaluation criteria: Based on the above analysis, propose specific evaluation criteria that reflect a deep understanding of <persona> and a close fit to the <task> scenario. These criteria should assess whether the content is well adapted to the user persona in style, depth, perspective, and practicality.
3. Explain the personalization rationale: Provide a brief explanation (explanation) for each criterion, clarifying how it addresses the specific attributes of <persona> or special requirements of <task>, and why such targeting is critical to achieving a good match.
4. Assign rational weights: Assign a weight (weight) to each criterion, ensuring that the total sum is 1.0. The distribution of weights should directly reflect the relative importance of each criterion in measuring how well the content matches "this particular user" in "this particular task." The closer a criterion is tied to persona characteristics and task scenario, the higher its weight should be.

Core requirements:
1. Deep personalization orientation: The analysis, criteria, explanations, and weights must be deeply rooted in the uniqueness of <persona> (e.g., their professional background, cognitive level, decision-making preferences, emotional needs) and the specific context of <task>. Avoid generic or templated evaluation.
2. Focus on contextual responsiveness and resonance: The criteria should evaluate whether the content not only responds to the task at the informational level but also resonates with the context and expectations implied by the user persona in terms of expression style, reasoning logic, case selection, and level of detail.
3. Rationale must reflect targeting: The <analysis> section must clearly explain how key features were extracted from the given <persona> and <task> to form these personalized criteria. Each criterion’s explanation must directly show how it serves this specific user and task.
4. Weights must reflect personalization priorities: The weight distribution must logically demonstrate which aspects of alignment are the most critical success factors for "this user" completing "this task."
5. Standard output format: Strictly follow the example format below. First output the <analysis> text, then immediately provide the <json_output>.
</instruction>

<example_rational>
The example below demonstrates **how to develop Goal Alignment evaluation criteria based on the task requirements**. Focus on understanding the **thinking process and analytical approach** used in the example, rather than simply copying its content or numerical weights.
</example_rational>

<example>
<task> 
"I want to update my skincare products in the next month to choose products suitable for my skin type and needs. My skin type is combination, with an oily T-zone that gets shiny in the afternoon, while my cheeks are quite dry and feel tight after washing. Recently, I have been troubled by dullness and some fine lines, and I hope to improve these through skincare. My main skincare goals are anti-aging and brightening, and my total budget is under 2000. I want to first establish a healthy skin state, then continue to improve skin problems. I do morning and evening skincare with cleanser, toner, and cream. Please provide me with a skincare plan including basic skincare steps and product recommendations, while comparing ingredients, effects, and prices of different brands to help me find the best choice."
</task> 
<persona> 
"A 28-year-old female working in the internet industry, staying in air-conditioned rooms for long hours and wearing makeup for 12 hours daily for video meetings. She is sensitive to ethanol, values daytime oil-control and long-lasting makeup, and prefers unscented Japanese cosmeceutical brands. She needs to address both T-zone makeup breakdown and cheek cakiness issues. At night, she has enough time for skincare and can accept over 3 minutes for massage and absorption."
</persona> 

<output> 
<analysis> 
Based on this specific user persona and task scenario, the core of the evaluation is to assess whether the report deeply understands the unique working environment, makeup needs, and ingredient preferences of this internet industry professional, and whether it provides highly personalized solutions. The user stays long hours in air-conditioned rooms and wears makeup for 12 hours, which means the plan must pay special attention to skin barrier repair, long-lasting hydration, and makeup adherence. The clear ethanol sensitivity and Japanese brand preference mean that the recommended products must strictly avoid irritating ingredients and match the brand preference.
Therefore, the evaluation criteria should focus on: 
1. **Addressing work environment impact:** Whether the plan specifically addresses the dual challenge of "dry air-conditioned environment" and "long-hour makeup wearing," providing specialized hydration and makeup-setting strategies. 
2. **Precise ingredient preference matching:** Whether recommended products strictly avoid ethanol and prioritize her preferred unscented Japanese brands, reflecting respect for her stated preferences. 
3. **Zonal care and barrier repair:** Whether the plan recognizes that "oily T-zone and dry cheeks" is fundamentally caused by barrier damage leading to imbalance, and proposes a strategy of "repairing barrier first, then zonal treatment." 
4. **Day/night differentiation design:** Whether the plan differentiates between "daytime oil-control/makeup needs" and "nighttime nourishing care," leveraging the fact that she has time for longer massage and absorption at night. 
The weight distribution reflects the importance of each criterion for this user completing the task. Addressing work environment challenges and matching ingredient preferences are most critical, as they directly determine usability and acceptance, so they receive the highest weights. Zonal care and day/night differentiation are also important but are more basic requirements, so they have slightly lower weights.
</analysis> 

<json_output> 
[ 
    {{ "criterion": "Targeted solutions for work environment challenges", "explanation": "Evaluate whether the plan specifically addresses the unique challenges of 'dry air-conditioned environment' and 'wearing makeup for 12 hours,' providing effective hydration, makeup-setting, and post-makeup repair strategies rather than generic combination-skin care advice.", "weight": 0.35 }}, 
    {{ "criterion": "Strict adherence to ingredient and brand preferences", "explanation": "Check whether all recommended products strictly avoid ethanol, are fragrance-free, and prioritize Japanese cosmeceutical brands, fully aligning with the user’s declared ingredient sensitivity and brand preferences.", "weight": 0.30 }}, 
    {{ "criterion": "Inclusion of barrier repair and zonal care strategies", "explanation": "Assess whether the plan identifies barrier damage as the root cause of imbalance and prioritizes 'repair and stabilize first, then functional care,' as well as provides specific methods for treating the T-zone and cheeks differently.", "weight": 0.20 }}, 
    {{ "criterion": "Scenario-specific differentiation of day and night skincare plans", "explanation": "Check whether the plan designs distinct product combinations and routines for 'quick daytime oil control/makeup setting' and 'nighttime nourishing repair,' especially taking advantage of the user’s sufficient nighttime skincare time.", "weight": 0.15 }} 
] 
</json_output> 
</output> 
</example>

Please strictly follow the above instructions and methodology. Now, for the following specific task, start your work:
<task>
"{task_prompt}"
</task>
<persona>
"{persona_prompt}"
</persona>
Please output your `<analysis>` and `<json_output>`.
</user_prompt>
"""

personalization_eval_criteria_prompt_content_alignment = """
<system_role>
You are an experienced research article evaluation expert. You are skilled at breaking down abstract evaluation dimensions (such as "Content Alignment") into actionable, clear, and specific evaluation criteria tailored to the given research task and user persona, and assigning reasonable weights and explanations for each criterion.
</system_role>


<user_prompt>
**Background**: We are providing a personalized scoring rubric for a specific task and user persona from the dimension of **Content Alignment**.
**Content Alignment**: Whether the research content is customized based on the user's interests, knowledge background, and other preferences.




<task>
"{task_prompt}"
</task>


The user persona is as follows:
<persona>
"{persona_prompt}"
</persona>


<instruction>
**Your Goal**: For the **Content Alignment** dimension of this research article, create a set of detailed, concrete, and highly tailored evaluation criteria for the above `<task>` and `<persona>`. You need to:
1. **Analyze the Task and Persona**: Deeply analyze `<task>` and `<persona>` to infer the user's potential interests, knowledge background, and the depth and breadth of content they may prefer.
2. **Formulate Criteria**: Based on your analysis, propose specific evaluation criteria that focus on whether the report's content matches the user's interest points and knowledge level.
3. **Provide Explanations**: For each criterion, provide a brief explanation (`explanation`) explaining why it is important for evaluating the content alignment for this `<task>`.
4. **Assign Weights**: Assign a reasonable weight to each criterion (weight), ensuring that the sum of all weights equals exactly 1.0.
The weight allocation should logically reflect the personalization-first principle: criteria directly tied to unique personal traits, exclusive preferences, or specific contextual needs in the user persona should receive higher weights, as they are key to achieving true personalized content alignment.
5. **Avoid Overlap**: Make sure the evaluation criteria focus solely on the **Content Alignment** dimension, avoiding overlap with other dimensions such as Goal Alignment, Expression Style Alignment, and Practicality/Actionability.


**Core Requirements**:
1. **Strongly Linked to the Persona**: The analysis, criteria, explanations, and weights must be directly connected to the user's interests, knowledge background, or content preferences.
2. **Focus on Content Selection and Depth**: The criteria should assess whether the choice of content is precise and whether the depth is appropriate, rather than merely evaluating whether information is presented.
3. **Provide Sufficient Rationale**: The `<analysis>` section must clearly articulate the overall reasoning behind formulating these criteria and weights, linking them to `<task>` and `<persona>`. Each `explanation` must clarify why the individual criterion is relevant.
4. **Reasonable Weighting**: The weight distribution should be logical, reflecting the relative importance of each criterion in measuring content alignment, with particular emphasis on giving higher priority to personalized aspects.
5. **Standardized Output Format**: Strictly follow the format below — output the `<analysis>` text first, immediately followed by `<json_output>`.
</instruction>


<example_rational>
The following example demonstrates **how to formulate content alignment evaluation criteria based on the task requirements and user persona**. Pay close attention to the **thinking process and analytical approach** in this example, rather than simply copying the content or weight values.
</example_rational>


<example>
<task> 
"I am an independent musician who specializes in synth-pop and chillwave. Recently, I have been working on a new song. The main melody and chord progression have been completed on my Minilogue synthesizer, but the arrangement still feels 'empty,' lacking layering and a sense of 'surprise.' I would like to receive some inspiration for arrangement and sound design. Please avoid recommending common pop music arrangement routines. I want to explore unconventional creative techniques that evoke a retro-futuristic atmosphere. You may suggest effect processing tricks, unique synthesizer modulation techniques, or even everyday sounds worth sampling." 
</task> 
<persona> 
"A male bedroom producer born in the 90s, deeply influenced by 80s synthesizer music and vaporwave aesthetics. Prefers KORG and Arturia hardware synthesizers and enjoys manually tweaking sounds rather than relying on preset packs. Identifies as a 'sound hunter' who enjoys discovering unique sounds. Has a solid music theory foundation and can understand advanced chord extensions (e.g., add9, #11th) and modal concepts. Strongly dislikes commercialized, cookie-cutter production advice." 
</persona> 
<output> 
<analysis> 
To evaluate the content alignment for this arrangement inspiration report, we must focus on the user persona's **highly specialized, almost "picky" personal taste and identity**. Their identity as a "bedroom producer" and "sound hunter" means they seek **unique, exploratory, and personally expressive techniques** rather than generic beginner tips. Their explicit hardware preferences (KORG, Arturia) and stylistic inclinations (retro-futurism, chillwave, vaporwave) act as a highly selective "content filter." Their solid understanding of music theory means the content can and should dive deep into **specific modulation parameters, advanced chord applications, and effect chain design**. Most importantly, their "strong dislike for commercialization" demands that content avoid mainstream approaches entirely, instead drawing inspiration from **experimental music, underground scenes, or vintage hardware manuals**. Weighting should be highly skewed: **uniqueness and anti-mainstream nature of the methods** receive the highest weight, as they are directly tied to the user's core identity ("uniqueness") and emotional stance ("anti-commercialization"), making them foundational for gaining the user's trust. **Relevance to specific devices and styles** is secondary but still crucial, as the content must work within their familiar workflow and aesthetic system. **Depth and exploratory nature of techniques** are natural extensions to satisfy their "sound hunter" persona and hands-on preferences.
</analysis> 
<json_output> 
[ 
    {{ "criterion": "Uniqueness and Anti-Mainstream Nature of Recommendations", "explanation": "Evaluate whether the content completely avoids common pop arrangement clichés, instead drawing from experimental music, lo-fi techniques, or obscure hardware/software features (e.g., downsampling tape samples to create a vaporwave feel, or using wavetable scanning for non-standard timbres), to meet the user's extreme desire for 'uniqueness' and 'anti-commercialization.'", "weight": 0.50 }}, 
    {{ "criterion": "Strong Association with User's Preferred Devices and Styles", "explanation": "Evaluate whether the suggestions specifically reference the user's equipment brands (e.g., KORG Minilogue modulation matrix settings, Arturia Pigments granular synth function) or point to their favorite styles (e.g., referencing John Carpenter's 80s film scores or modern chillwave techniques), ensuring the content works within their familiar technical and aesthetic context.", "weight": 0.30 }}, 
    {{ "criterion": "Depth, Modulatability, and Explorability of Techniques", "explanation": "Evaluate whether the sound design techniques are presented as a 'starting point' rather than a 'final answer' (e.g., offering a base effect chain with detailed explanation of how each parameter affects the sound), encouraging the user to iterate and experiment further, thereby satisfying their 'sound hunter' curiosity and hands-on approach.", "weight": 0.20 }} 
] 
</json_output> 
</output> 
</example>




Please strictly follow the above instructions and methodology. Now, for the following specific task, start your work:
<task>
"{task_prompt}"
</task>
<persona>
"{persona_prompt}"
</persona>
Please output your `<analysis>` and `<json_output>`.
</user_prompt>
"""

personalization_eval_criteria_prompt_presentation_fit = """
<system_role>
You are an experienced research article evaluation expert. You are skilled at breaking down abstract evaluation dimensions (such as "Presentation Fit") into actionable, clear, and task- and persona-specific evaluation criteria, and assigning reasonable weights and explanations for each criterion.
</system_role>

<user_prompt>
**Background**: We are evaluating a deep research report written for the following research task based on four dimensions: Goal Alignment, Content Alignment, Presentation Fit, and Actionability & Practicality.
1. **Goal Alignment:** Whether the research fully and accurately understands the relationship between the task and the user persona, extracts deep and implicit needs, and generates a personalized report based on that.
2. **Content Alignment:** Whether the research selects customized content based on the user's interests, knowledge background, etc.
3. **Actionability & Practicality:** Whether the report is feasible and practical for the user and can help decision-making.
4. **Presentation Fit:** Whether the language style, information structure, and presentation format of the report match the user's cognitive habits and media preferences.

<task>
"{task_prompt}"
</task>

The user persona is as follows:
<persona>
"{persona_prompt}"
</persona>

<instruction>
**Your goal**: For the **Presentation Fit** dimension of this research report, create a detailed, specific, and highly task- and persona-tailored set of evaluation criteria. You need to:
1.  **Analyze the task and user persona**: Carefully analyze `<task>` and `<persona>` to infer the user's likely comprehension level and preferred communication style, such as degree of professionalism, language habits, and information presentation preferences.
2.  **Develop criteria**: Based on the analysis, propose specific evaluation criteria focusing on whether the report's language style, terminology usage, information organization, and visualization match the user's habits.
3.  **Explain the reasoning**: Provide a brief explanation (`explanation`) for each criterion, clarifying why it is important for assessing the **Presentation Fit** of this `<task>`.
4.  **Assign weights**: Assign a reasonable weight (`weight`) to each criterion, ensuring that the sum of all weights is exactly **1.0**. The weights should reflect the relative importance of each criterion in achieving the goal of presentation fit for this task.
5.  **Avoid overlap**: Ensure the evaluation criteria are strictly related to the **Presentation Fit** dimension and avoid including aspects from other dimensions (Goal Alignment, Content Alignment, Actionability & Practicality).

**Core requirements**:
1.  **Reader-centered**: The analysis, criteria, explanations, and weights must directly relate to the user's comprehension ability and communication preferences.
2.  **Focus on presentation**: The criteria should evaluate formal elements such as language, structure, and charts, rather than just the content itself.
3.  **Provide sufficient reasoning**: The `<analysis>` section must clearly articulate the overall reasoning behind the criteria and weight assignment, linking them to `<task>` and `<persona>`. Each `explanation` must justify the relevance of the individual criterion.
4.  **Ensure reasonable weighting**: The weight assignment must be logical, reflecting the relative importance of each criterion in the context of presentation fit.
5.  **Standardized output format**: Strictly follow the example format below: first output `<analysis>` text, then provide `<json_output>` immediately after.
</instruction>

<example_rational>
The following example is provided to illustrate **how to develop Presentation Fit evaluation criteria based on task requirements and user persona**. Focus on learning the **thinking process and analysis method** demonstrated in this example, rather than simply copying its content or weight values.
</example_rationale>

<example>
<task>
"I hope to update my skincare products in the coming month so that I can choose products suitable for my skin type and needs. My skin type is combination, with an oily T-zone—especially shiny by the afternoon—and rather dry cheeks that feel tight after washing. Recently I’ve been troubled by dullness and some fine lines, and I hope to improve my skin condition through skincare. My skincare goals are mainly anti-aging and brightening, and my total budget is under 2000. I hope to first establish a healthy skin condition, then further improve my problems. My skincare routine includes morning and evening steps with cleanser, toner, and cream. Please provide me with a skincare plan, including basic steps and product recommendations, and compare ingredients, effects, and prices of different brands to help me find the most suitable choice."
</task>
<persona>
"28-year-old female working in the internet industry, spending long hours in air-conditioned rooms and wearing makeup for 12 hours daily due to video meetings. Sensitive to ethanol ingredients, values oil-control and long-lasting makeup performance during the day, prefers fragrance-free Japanese cosmeceutical brands. Needs to solve T-zone shine and foundation caking on the cheeks. Has enough time for a night routine and can accept more than 3 minutes of massage/absorption."
</persona>
<output>
<analysis>
When evaluating the presentation fit of a report for the “skincare product update” task, the core focus is whether the expression style, language tone, and wording are understandable and appealing to the user.

Therefore, the evaluation criteria must focus on:
1.  **Language style fit**: For an internet industry professional, the language should be professional, concise, and logically clear. Avoid overly exaggerated marketing language, and provide simple explanations of ingredients and mechanisms when appropriate, making it more evidence-based.
2.  **Terminology fit**: The user is not an expert in cosmetic science, so terminology should be simple and professional, with brief clarifications for technical terms to reduce reading effort.
3.  **Information presentation match**: For an internet industry worker used to structured content, check whether the report uses lists and bullet points to make it easy to read.

As for weight distribution, language style and terminology fit are the most critical, as they directly affect the user's comprehension. Information presentation further enhances reading efficiency and experience, so it has slightly lower weight.
</analysis>
<json_output>
[
  {{
    "criterion": "Whether the language style matches the characteristics of an internet industry professional",
    "explanation": "Evaluate whether the language is professional, concise, and logically clear, avoiding overly exaggerated marketing language.",
    "weight": 0.45
  }},
  {{
    "criterion": "Whether the terminology style matches the user's profile",
    "explanation": "Evaluate whether the article uses simple and professional terminology, and whether technical terms are briefly explained to reduce reading effort.",
    "weight": 0.35
  }},
  {{
    "criterion": "Whether the information presentation style matches the user's preferences",
    "explanation": "Evaluate whether the article makes extensive use of lists and bullet points to make it easier to read.",
    "weight": 0.20
  }}
]
</json_output>
</output>
</example>

Please strictly follow the above instructions and method. Now, for the following specific task, begin your work:
<task>
"{task_prompt}"
</task>
<persona>
"{persona_prompt}"
</persona>
Please output your `<analysis>` and `<json_output>`.
</user_prompt>
"""

personalization_eval_criteria_prompt_actionability = """
<system_role>
You are an experienced research article evaluation expert. You are skilled at breaking down abstract evaluation dimensions (such as "Actionability & Practicality") into actionable, clear, task- and persona-specific evaluation criteria, and assigning reasonable weights and explanations for each criterion.
</system_role>

<user_prompt>
**Background**: We are evaluating a deep research report written for the following research task based on four dimensions: Goal Alignment, Content Alignment, Presentation Fit, and Actionability & Practicality.
1. **Goal Alignment:** Whether the research fully and accurately understands the relationship between the task and the user persona, extracts deep and implicit needs, and generates a personalized report based on that.
2. **Content Alignment:** Whether the research selects customized content based on the user's interests, knowledge background, etc.
3. **Actionability & Practicality:** Whether the report is feasible and practical for the user and can help decision-making.
4. **Presentation Fit:** Whether the language style, information structure, and presentation format of the report match the user's cognitive habits and media preferences.

<task>
"{task_prompt}"
</task>

The user persona is as follows:
<persona>
"{persona_prompt}"
</persona>

<instruction>
**Your goal**: For the **Actionability & Practicality** dimension of this research report, create a detailed, specific, and highly task- and persona-tailored set of evaluation criteria. You need to:
1.  **Analyze the task and user persona**: Carefully analyze the ultimate purpose of `<task>`—what the user hopes to do with the report—and combine it with `<persona>` to infer what information or recommendations will truly help the user take action or make decisions.
2.  **Develop criteria**: Based on the analysis, propose specific evaluation criteria focusing on whether the report's conclusions, recommendations, and analytical framework are feasible, targeted, and practical.
3.  **Explain the reasoning**: Provide a brief explanation (`explanation`) for each criterion, clarifying why it is important for assessing the actionability of this `<task>`.
4.  **Assign weights**: Assign a reasonable weight (`weight`) to each criterion, ensuring that the sum of all weights is exactly **1.0**. The weights should reflect the relative importance of each criterion in achieving the goal of actionability.
5.  **Avoid overlap**: Ensure the evaluation criteria are strictly related to the **Actionability & Practicality** dimension and avoid including aspects from other dimensions (Goal Alignment, Content Alignment, Presentation Fit).

**Core requirements**:
1.  **Focus on action purpose**: The analysis, criteria, explanations, and weights must be directly related to the user's ability to obtain guidance from the report and take action.
2.  **Focus on practical aspects**: The criteria should evaluate whether the report provides specific, actionable recommendations rather than only high-level theory.
3.  **Provide sufficient reasoning**: The `<analysis>` section must clearly articulate the overall reasoning behind the criteria and weight assignment, linking them to `<task>` and `<persona>`. Each `explanation` must justify the relevance of the individual criterion.
4.  **Ensure reasonable weighting**: The weight assignment must be logical, reflecting the relative importance of each criterion in the context of actionability & practicality.
5.  **Standardized output format**: Strictly follow the example format below: first output `<analysis>` text, then provide `<json_output>` immediately after.
</instruction>

<example_rational>
The following example is provided to illustrate **how to develop Actionability & Practicality evaluation criteria based on task requirements and user persona**. Focus on learning the **thinking process and analysis method** demonstrated in this example, rather than simply copying its content or weight values.
</example_rationale>

<example>
<task>
"I hope to update my skincare products in the coming month so that I can choose products suitable for my skin type and needs. My skin type is combination, with an oily T-zone—especially shiny by the afternoon—and rather dry cheeks that feel tight after washing. Recently I’ve been troubled by dullness and some fine lines, and I hope to improve my skin condition through skincare. My skincare goals are mainly anti-aging and brightening, and my total budget is under 2000. I hope to first establish a healthy skin condition, then further improve my problems. My skincare routine includes morning and evening steps with cleanser, toner, and cream. Please provide me with a skincare plan, including basic steps and product recommendations, and compare ingredients, effects, and prices of different brands to help me find the most suitable choice."
</task>
<persona>
"28-year-old female working in the internet industry, spending long hours in air-conditioned rooms and wearing makeup for 12 hours daily due to video meetings. Sensitive to ethanol ingredients, values oil-control and long-lasting makeup performance during the day, prefers fragrance-free Japanese cosmeceutical brands. Needs to solve T-zone shine and foundation caking on the cheeks. Has enough time for a night routine and can accept more than 3 minutes of massage/absorption."
</persona>
<output>
<analysis>
When evaluating the actionability & practicality of a report for the “skincare product update” task, the key is to determine whether the report's conclusions and recommendations can directly guide the user to take real action. What the user needs is a clear and executable decision-making guide, not just data and analysis. For this user, these recommendations must be simple, understandable, and concrete.

The evaluation criteria should focus on:
1.  **Budget feasibility**: The total price of all recommended products (including cleansers, toners, creams, etc.) must fall within the user’s budget, with a clear total cost calculation that allows the user to quickly understand the expense.
2.  **Skincare routine feasibility**: Since the user is an office worker with limited time during the day, the daytime routine should not have too many steps. The nighttime routine can be more complete to meet user needs.
3.  **Purchase convenience**: The recommended Japanese cosmeceutical brands should be mainstream and easily available through domestic e-commerce platforms or offline channels, avoiding niche or hard-to-obtain products.
4.  **Ingredient safety**: Recommended products should contain safe ingredients and avoid those that may trigger the user's sensitivities.

For weight assignment, budget feasibility and ingredient safety are the most critical, as they directly determine the practical value of the report, so they receive the highest weights. Purchase convenience and routine feasibility increase persuasiveness and relevance, so they receive moderately high weights.
</analysis>
<json_output>
[
  {{
    "criterion": "Budget feasibility of the overall plan",
    "explanation": "Whether the report clearly states the total cost of the recommended skincare products, ensures it is within the user’s budget, and avoids exceeding the budget.",
    "weight": 0.30
  }},
  {{
    "criterion": "Feasibility of the skincare routine recommendations",
    "explanation": "Whether the report considers the user's busy daytime schedule, keeps the daytime routine concise, and provides a more complete nighttime routine.",
    "weight": 0.20
  }},
  {{
    "criterion": "Convenience of purchasing the recommended products",
    "explanation": "Whether the report recommends mainstream products that are easy to purchase from domestic e-commerce platforms or offline stores, avoiding niche or hard-to-find items.",
    "weight": 0.20
  }},
  {{
    "criterion": "Safety of the recommended product ingredients",
    "explanation": "Whether the report avoids recommending products containing ingredients that may cause irritation or sensitivity for the user.",
    "weight": 0.30
  }}
]
</json_output>
</output>
</example>

Please strictly follow the above instructions and method. Now, for the following specific task, begin your work:
<task>
"{task_prompt}"
</task>
<persona>
"{persona_prompt}"
</persona>
Please output your `<analysis>` and `<json_output>`.
</user_prompt>
"""







# Q - Quality: Content Quality Dimensions  
# 1. Depth & Insight: Does the report offer sufficient depth and unique insights?  
# 2. Logical Coherence: Is the argumentation framework rigorous and logically consistent?  
# 3. Clarity & Readability: Is the language, presentation, and formatting clear and easy to understand for readers?  

# Quality Criteria Generation Pipeline  
# Step 1: For a given task, ask the model to assign percentage weights to each dimension — Depth & Insight, Logical Coherence, Clarity & Readability — as part of the total evaluation criteria. Output as JSON.  
# Step 2: For each dimension, ask the model to generate specific evaluation criteria tailored to the task, along with the weight of each criterion. Output as JSON.

#step 1 prompt
quality_eval_dimension_weight_prompt = """
<system_role>
You are an experienced expert in evaluating research reports. You excel at deeply understanding the goals, challenges, and core value points of a given research task, and setting **dynamic, reasonable, and well-justified** dimension weights for subsequent report quality evaluations.
</system_role>

<user_prompt>
Here is a deep research task as follows:
<task>
"{task_prompt}"
</task>

<instruction>
**Background**: The research team will conduct an in-depth and comprehensive investigation based on the above `<task>` and eventually produce a high-quality research report.
**Your Task**: As an evaluation expert, you need to set the evaluation dimension weights specifically for this `<task>`. The evaluation will be carried out around the following **three dimensions**:
1. **Depth & Insight:** Whether the report provides sufficient depth and unique insights.
2. **Logical Coherence:** Whether the report’s reasoning framework is rigorous and its logical derivation coherent.
3. **Clarity & Readability:** Whether the report’s language, information presentation, and formatting are clear and easy to understand, allowing readers to absorb the content smoothly.

**Evaluation Formula**: Total Score = (Depth & Insight * weight₁) + (Logical Coherence * weight₂) + (Clarity & Readability * weight₃). (**Note: The sum of all weights must equal exactly 1.0**)

**Core Requirements**:
1. **Analyze the Task in Depth**: Carefully study the `<task>` content, implicit objectives, potential challenges, and the core value of the deliverable.
2. **Dynamically Allocate Weights**: Based on your analysis, assign weights to the three dimensions (use decimals between 0 and 1, e.g., 0.4). **The key is to understand that different tasks emphasize different aspects — weights must be adjusted flexibly based on task characteristics, rather than being fixed.**
3. **Explain the Allocation Rationale**: Your analysis (`<analysis>`) **must clearly and specifically explain why each dimension is given its corresponding weight** and **directly link your reasoning to the requirements and characteristics of `<task>`**. This is the key criterion for evaluating your work quality.
4. **Standardized Output Format**: Strictly follow the example format below — first output the detailed rationale in `<analysis>`, then provide the weight allocation result in `<json_output>`.

</instruction>

<examples_rationale>
Below are two examples, which demonstrate **how to adjust dimension weights according to the nature of the task and explain the reasoning**. Please focus on learning the **thinking process and analytical approach** shown in the examples, rather than simply copying their content or numerical values.
</examples_rationale>

<example_1>
<task>
"Predict the housing price trend in Foshan — is it better to sell or rent out a second-hand property?"
</task>
<output>
<analysis>
The core of this task is to perform complex market analysis and provide a clear, credible recommendation for a major financial decision. Therefore, the depth of content, logical rigor, and clarity of expression are all critical.
* **Depth & Insight (0.50):** The task requires forecasting the future and making a decision. Deep analysis, unique insights, and valuable conclusions are the foundation of report quality, so this dimension gets the highest weight.
* **Logical Coherence (0.30):** The prediction and decision-making advice must be built on a rigorous logical chain (from data to analysis, from analysis to prediction, from prediction to recommendation). Logical soundness directly affects credibility, thus it receives a high weight.
* **Clarity & Readability (0.20):** Since the report’s audience may include non-experts, whether the report can present complex analysis in a clear and understandable manner (with charts, plain language) directly affects its practical value, hence it also holds significant weight.
</analysis>
<json_output>
{{
    "depth_insight": 0.50,
    "logical_coherence": 0.30,
    "clarity_readability": 0.20
}}
</json_output>
</output>
</example_1>

<example_2>
<task>
"Research the historical returns of various major asset classes over the past 100 years."
</task>
<output>
<analysis>
The main goal of this task is to provide a comprehensive and accurate overview of macro-level historical data spanning a century. The emphasis is on clear presentation of information, structured organization, and accurate interpretation.
* **Clarity & Readability (0.45):** The biggest challenge lies in presenting a massive amount of multi-dimensional historical data through intuitive charts, clear language, and well-organized layout — hence the highest weight is assigned here.
* **Logical Coherence (0.30):** The report must use a clear structure to organize data by asset class and time period, ensuring systematization and comparability. Therefore, this dimension carries a high weight.
* **Depth & Insight (0.25):** Summarizing and analyzing data (e.g., revealing cyclical patterns, comparing risk-adjusted returns) adds value to the report, but is slightly less important than presenting massive information clearly and systematically, so it has a lower weight.
</analysis>
<json_output>
{{
    "depth_insight": 0.25,
    "logical_coherence": 0.30,
    "clarity_readability": 0.45
}}
</json_output>
</output>
</example_2>

Please strictly follow the above instructions and methodology. Now, for the following specific task, begin your work:
<task>
"{task_prompt}"
</task>
Please output your `<analysis>` and `<json_output>`.
</user_prompt>
"""
# step 2 prompt
quality_eval_criteria_prompt_depth_insight = """
<system_role>
You are an experienced expert in evaluating research reports. You excel at breaking down abstract evaluation dimensions (such as "Depth & Insight") into actionable, task-specific, and clear criteria, assigning reasonable weights and explanations for each.
</system_role>

<user_prompt>
**Background**: We are evaluating a research report based on three dimensions: Depth & Insight, Logical Coherence, and Clarity & Readability.
1. **Depth & Insight:** Whether the report provides sufficient depth and unique insights.
2. **Logical Coherence:** Whether the report’s reasoning framework is rigorous and its logical derivation coherent.
3. **Clarity & Readability:** Whether the report’s language, information presentation, and formatting are clear and easy to understand.

<task>
"{task_prompt}"
</task>

<instruction>
**Your Goal**: For the **Depth & Insight** dimension of this report, develop a detailed, specific, and highly task-targeted set of evaluation criteria. You need to:
1. **Analyze the Task**: Examine `<task>` in depth and identify where deep analysis, logical reasoning, insight extraction, or value judgment are required to demonstrate insight.
2. **Formulate Criteria**: Based on the analysis, propose concrete evaluation criteria focusing on analytical depth, logical rigor, originality, and value of conclusions.
3. **Explain Each Criterion**: Provide a brief explanation (`explanation`) for why this criterion is important for evaluating Depth & Insight for `<task>`.
4. **Assign Weights**: Assign a reasonable weight (`weight`) to each criterion, ensuring the weights sum exactly to **1.0**. The weights should reflect the relative importance of each criterion within the Depth & Insight dimension.
5. **Avoid Overlap**: Clearly focus only on criteria relevant to **Depth & Insight**, avoiding aspects of **Logical Coherence** (structure) or **Clarity & Readability** (language, formatting).

**Core Requirements**:
1. **Stay Task-Specific**: The analysis, criteria, explanations, and weights must directly relate to the task’s core requirements and characteristics.
2. **Go Beyond the Surface**: The criteria should assess analytical depth, reasoning rigor, originality of insights, and value of conclusions — not just listing information.
3. **Provide Strong Rationale**: The `<analysis>` section must clearly explain the overall approach to designing the criteria and weights, linking it to `<task>`. Each `explanation` must justify the criterion.
4. **Ensure Reasonable Weighting**: Weight distribution must be logical, reflecting the relative importance of each criterion in showing insight.
5. **Standardized Output Format**: Strictly follow the format below: output `<analysis>` first, then `<json_output>`.

</instruction>

<example_rational>
Below is an example demonstrating **how to design Depth & Insight criteria**. Focus on the **thinking logic and analytical approach** rather than copying its contents or weight numbers.
</example_rational>

<example>
<task>
"Predict the housing price trend in Foshan — is it better to sell or rent out a second-hand property?"
</task>
<output>
<analysis>
To evaluate the Depth & Insight dimension for this task, we must examine the depth of analysis, logical rigor, and value of conclusions — going beyond mere data presentation. The task’s core lies in analyzing complex factors to make forecasts and provide decision support. Insight is shown by identifying key drivers, building rigorous causal reasoning, conducting multi-dimensional risk-return tradeoffs, and offering forward-looking recommendations.

Evaluation criteria should emphasize:
1. **Identification and Analysis of Key Drivers** — not just listing them but explaining mechanisms and relative importance.
2. **Rigor of Predictive Logic** — assessing whether predictions are based on data and reasonable assumptions, forming a clear and credible chain of reasoning.
3. **Understanding of Factor Interactions** — revealing how macro, local, and policy factors interact to affect prices.
4. **Depth of Sell-vs-Rent Comparison Framework** — whether the comparison goes beyond surface-level yield to consider risk, time value, liquidity, etc.
5. **Scenario and Critical Thinking** — considering alternative homeowner situations or market scenarios, challenging mainstream views.
6. **Originality and Value of Insights** — providing forward-looking, actionable insights beyond common knowledge.

Weights prioritize key driver analysis and predictive logic because they form the foundation of insight. Sell-vs-rent comparison depth and scenario thinking also hold significant weight, as they demonstrate analytical sophistication. Original insights, while lower in weight, differentiate outstanding reports.
</analysis>
<json_output>
[
  {{
    "criterion": "Identification and In-depth Analysis of Key Drivers",
    "explanation": "Evaluates whether the report not only identifies key drivers of Foshan housing prices (e.g., policy, supply-demand, demographics) but also analyzes their mechanisms and relative importance rather than simply listing them.",
    "weight": 0.25
  }},
  {{
    "criterion": "Rigor and Soundness of Price Trend Prediction Logic",
    "explanation": "Evaluates whether the report builds a clear, logically rigorous predictive framework, based on data and reasonable assumptions rather than intuition or naive extrapolation.",
    "weight": 0.20
  }},
  {{
    "criterion": "Revealing Multi-factor Interaction Mechanisms",
    "explanation": "Evaluates whether the report explores how macroeconomy, local market, and policy interact and jointly affect prices, showing systemic thinking.",
    "weight": 0.15
  }},
  {{
    "criterion": "Depth and Multidimensionality of Sell-vs-Rent Framework",
    "explanation": "Evaluates whether the report builds a comprehensive sell vs rent comparison framework, going beyond yield calculation to consider risk, liquidity, time value, taxes, and holding costs.",
    "weight": 0.15
  }},
  {{
    "criterion": "Scenario-based and Critical Thinking",
    "explanation": "Evaluates whether the report considers different homeowner contexts (e.g., liquidity needs, risk preference) or property-specific factors and challenges mainstream views.",
    "weight": 0.15
  }},
  {{
    "criterion": "Originality and Forward-looking Value of Insights",
    "explanation": "Evaluates whether the report provides unique, enlightening, or actionable insights beyond common knowledge, offering new perspectives to decision-makers.",
    "weight": 0.10
  }}
]
</json_output>
</output>
</example>

Please strictly follow the above instructions and methodology. Now, for the following specific task, begin your work:
<task>
"{task_prompt}"
</task>
Please output your `<analysis>` and `<json_output>`.
</user_prompt>
"""

quality_eval_criteria_prompt_logical_coherence = """
<system_role>
You are an experienced expert in evaluating research reports. You excel at breaking down abstract evaluation dimensions (such as "Logical Coherence") into actionable, task-specific, and clear criteria, assigning reasonable weights and explanations for each.
</system_role>

<user_prompt>
**Background**: We are evaluating a research report based on three dimensions: Depth & Insight, Logical Coherence, and Clarity & Readability.
1. **Depth & Insight:** Whether the report provides sufficient depth and unique insights.
2. **Logical Coherence:** Whether the report’s reasoning framework is rigorous and its logical derivation coherent.
3. **Clarity & Readability:** Whether the report’s language, information presentation, and formatting are clear and easy to understand.

<task>
"{task_prompt}"
</task>

<instruction>
**Your Goal**: For the **Logical Coherence** dimension of this report, develop a detailed, specific, and highly task-targeted set of evaluation criteria. You need to:
1. **Analyze Logical Elements**: Consider the key components that make a research report logically sound, such as overall structure, section transitions, consistency of argumentation.
2. **Formulate Criteria**: Propose evaluation criteria covering:
    * The overall framework of the report
    * The relationship between arguments and supporting evidence
    * Smoothness of transitions between sections
    * The reasoning process from premises to conclusions
3. **Explain Each Criterion**: Provide a brief explanation (`explanation`) for why this criterion is important for logical rigor.
4. **Assign Weights**: Assign reasonable weights (`weight`) so that their sum equals **1.0**.
5. **Avoid Overlap**: Focus solely on criteria related to **Logical Coherence**, excluding those about **Depth & Insight** (depth of thought) or **Clarity & Readability** (language and layout).

**Core Requirements**:
1. **Focus on Structure**: The criteria should evaluate the organization of ideas and reasoning flow, not language elegance or depth of insight.
2. **Be Specific and Actionable**: Each criterion should be concrete and easy to assess.
3. **Provide Strong Rationale**: The `<analysis>` must explain the approach and weighting logic. Each `explanation` must justify the criterion.
4. **Standardized Output Format**: Output `<analysis>` first, then `<json_output>`.

</instruction>

<example_rational>
Below is an example demonstrating **how to design Logical Coherence criteria**. Focus on the **thinking logic and analytical approach**.
</example_rational>

<example>
<task>
"Predict the housing price trend in Foshan — is it better to sell or rent out a second-hand property?"
</task>
<output>
<analysis>
Evaluating logical coherence for this task focuses on whether the entire reasoning chain — from market analysis to final decision — is robust and connected. A logically sound report convinces readers that its prediction and recommendations are based on rational deduction, not subjective guesswork. Therefore, criteria must examine the overall structure, progressive layering of analysis, and reasoning process supporting core arguments.
Weights should prioritize the overall framework and reasoning chain, as they form the skeleton of the report. Supporting evidence and transitions are the flesh that keep the skeleton coherent and strong.
</analysis>
<json_output>
[
  {{
    "criterion": "Systematic and Reasonable Overall Report Framework",
    "explanation": "Evaluates whether the report constructs a clear analytical framework (e.g., from macro to micro, from current status analysis to prediction to decision advice), ensuring an orderly and comprehensive argumentation process.",
    "weight": 0.35
  }},
  {{
    "criterion": "Rigor of Reasoning from Analysis to Conclusion",
    "explanation": "Evaluates whether the core reasoning process is rigorous — whether market analysis logically leads to price trend forecasts and, subsequently, to sell-vs-rent recommendations.",
    "weight": 0.30
  }},
  {{
    "criterion": "Strength and Relevance of Evidence Supporting Arguments",
    "explanation": "Evaluates whether each argument (e.g., 'policy is a key factor') is backed by sufficient and relevant data or facts, avoiding unsubstantiated claims.",
    "weight": 0.20
  }},
  {{
    "criterion": "Smoothness of Transitions between Sections and Paragraphs",
    "explanation": "Evaluates whether transitions between sections are natural, contextually connected, and guide the reader smoothly through the author’s reasoning rather than creating logical jumps.",
    "weight": 0.15
  }}
]
</json_output>
</output>
</example>

Please strictly follow the above instructions and methodology. Now, for the following specific task, begin your work:
<task>
"{task_prompt}"
</task>
Please output your `<analysis>` and `<json_output>`.
</user_prompt>
"""

quality_eval_criteria_prompt_clarity_readability = """
<system_role>
You are an experienced research article evaluation expert. You are skilled at breaking down abstract evaluation dimensions (such as "Clarity & Readability") into concrete, actionable, and clear evaluation criteria tailored to specific research tasks, and assigning reasonable weights and explanations for each criterion.
</system_role>

<user_prompt>
**Background**: We are evaluating a deep research article written for the following research task across three dimensions: Content Depth & Insight, Logical Coherence, and Clarity & Readability.
1. **Content Depth & Insight:** Whether the report provides sufficient depth and unique insights.
2. **Logical Coherence:** Whether the report’s reasoning framework is rigorous and logically consistent.
3. **Clarity & Readability:** Whether the report’s language expression, information presentation, and layout make it easy to understand and absorb.

<task>
"{task_prompt}"
</task>

<instruction>
**Your Goal**: For the **Clarity & Readability** dimension of this research article, develop a set of detailed, concrete, and highly task-relevant evaluation criteria. You need to:
1. **Analyze Readability Elements**: Consider the key elements that constitute the readability of a high-quality research report, such as layout/formatting, language expression, and information presentation.
2. **Define Criteria**: Based on your analysis, propose concrete evaluation criteria covering:
   * Readability and aesthetics of formatting/layout
   * Fluency and accuracy of language expression
   * Use and explanation of technical terms
   * Effectiveness of data, charts, and other visualizations
3. **Explain Reasons**: Provide a brief explanation (`explanation`) for each criterion, describing why it is important for improving readability and the reader experience.
4. **Assign Weights**: Assign reasonable weights (`weight`) to each criterion, ensuring the sum of all weights is exactly **1.0**.
5. **Avoid Overlap**: Make sure the criteria are specifically focused on **Clarity & Readability** and do not evaluate **Content Depth** (the profundity of ideas) or **Logical Coherence** (the structure of argumentation).

**Core Requirements**:
1. **Focus on Presentation**: The criteria should evaluate the expression and presentation of the report, not the depth of its ideas.
2. **Clear and Actionable**: Each criterion must be specific, easy to understand, and easy to judge.
3. **Well-Justified**: The `<analysis>` section should explain your overall reasoning for designing these criteria and weights. Each `explanation` should clarify why the individual criterion is important.
4. **Standardized Output Format**: Output should strictly follow the example format below, with `<analysis>` text first, followed by `<json_output>`.

</instruction>

<example_rational>
The following example demonstrates **how to define evaluation criteria for Clarity & Readability**. Focus on learning the **thinking process and analytical approach** shown in the example.
</example_rational>

<example>
<task>
"Predict the housing price trend in Foshan: is it better to sell or rent a second-hand house?"
</task>
<output>
<analysis>
When evaluating the clarity and readability of a report on this task, the key is to ensure that its complex analyses and conclusions can be easily understood and absorbed by the target audience (who may be non-experts). Even if a report is insightful and logically sound, its practical value is significantly diminished if the expression is obscure or the formatting is messy. Therefore, the criteria must cover all aspects of the reading experience—from language and visualization to overall layout.
As for weight distribution, formatting and language clarity are fundamental and should have the highest weight. The effectiveness of data visualization is crucial for conveying complex information and should also receive a significant weight. The remaining parts should collectively serve to improve the overall reading experience.
</analysis>
<json_output>
[
  {{
    "criterion": "Cleanliness and Standardization of Formatting/Layout",
    "explanation": "Evaluates whether the report’s overall layout is clean and standardized, with clear heading hierarchy, appropriate paragraph spacing, reasonable font size and line spacing, making it easy to read.",
    "weight": 0.30
  }},
  {{
    "criterion": "Clarity, Accuracy, and Professionalism of Language Expression",
    "explanation": "Evaluates whether the language is smooth and easy to understand, free of ambiguity, with accurate word choice; whether essential technical terms (e.g., floor area ratio, LPR) are clearly explained to lower the comprehension barrier for readers.",
    "weight": 0.25
  }},
  {{
    "criterion": "Effectiveness and Intuitiveness of Data and Chart Presentation",
    "explanation": "Evaluates whether the charts are well-designed, clear, and visually appealing, and whether they convey the core information intuitively (e.g., housing price trends, rent-sale return comparison tables), effectively complementing the textual explanation.",
    "weight": 0.20
  }},
  {{
    "criterion": "Highlighting of Key Information and Layout Readability",
    "explanation": "Evaluates whether the report effectively highlights key points and conclusions using headings, bold text, summaries, and bullet points, while maintaining clean layout and adequate white space to improve long-term reading comfort.",
    "weight": 0.15
  }},
  {{
    "criterion": "Conciseness of Summary and Conclusion",
    "explanation": "Evaluates whether the report provides a high-quality executive summary and conclusion section that allows readers to quickly grasp the core findings and final recommendations.",
    "weight": 0.10
  }}
]
</json_output>
</output>
</example>

Please strictly follow the above instructions and methodology. Now, based on the specific task below, start your work:
<task>
"{task_prompt}"
</task>
Please output your `<analysis>` and `<json_output>`.
</user_prompt>
"""