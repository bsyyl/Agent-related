import os
import ujson as json
from tqdm import tqdm

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


# ========== 模型加载 ==========
MODEL_PATH = "/data/user/zhuzixuan/mount/KG2RAG-main/model/Llama-7b-hf"

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    device_map="auto",
    torch_dtype=torch.float16
)


def complete_llama(query, max_new_tokens=256):
    inputs = tokenizer(query, return_tensors="pt").to("cuda")
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)


# ========== 法规三元组抽取 ==========
def extract_triplets(llm, ctx):
    query = f"""
You are extracting factual regulatory triplets from maritime regulations or resolutions.

Each triplet must strictly follow this format:
<Head Entity##Relation##Tail Entity>

Rules:
1. Extract only facts explicitly stated in the text.
2. Do NOT infer, summarize, or add external knowledge.
3. Use exact wording from the text for entities and relations.
4. Relations should reflect regulatory actions, requirements, scope, adoption, repeal, reference, or responsibility.
5. Output triplets only, separated by $$, with no extra text.

--------------------
Text:
The Assembly adopts the 2021 Port State Control Procedures and requests Governments to apply them.

Triplets:
<Assembly##adopts##2021 Port State Control Procedures>$$
<Governments##apply##2021 Port State Control Procedures>$$
--------------------
Text:
{ctx}

Triplets:
""".strip()

    resp = llm(query)

    triplets = set()
    for triplet_text in resp.split('$$'):
        triplet_text = triplet_text.strip()
        if not (triplet_text.startswith('<') and triplet_text.endswith('>')):
            continue

        tokens = triplet_text[1:-1].split('##')
        if len(tokens) != 3:
            continue

        h, r, t = [x.strip() for x in tokens]

        if h == t:
            continue
        if any(x.lower() in ["unknown", "null", "none"] for x in [h, r, t]):
            continue
        if (h not in ctx) and (t not in ctx):
            continue

        triplets.add((h, r, t))

    return [[h, r, t] for h, r, t in triplets]


# ========== 主流程 ==========
data_path = "/data/user/zhuzixuan/mount/KG2RAG-main/data/cug_ship/cug_ship.json"
out_dir = "/data/user/zhuzixuan/mount/KG2RAG-main/data/cug_ship/kgs/extract_subkgs"
os.makedirs(out_dir, exist_ok=True)

with open(data_path, "r", encoding="utf-8") as f:
    dataset = json.load(f)

count = 0

for file_id in tqdm(dataset.keys()):
    file_data = dataset[file_id]
    file_name = file_data["文件名"]
    blocks = file_data["文本块"]

    out_path = os.path.join(out_dir, f"{file_name}.json")
    if os.path.exists(out_path):
        continue

    file_triplets = {}

    for block_id, block_text in blocks.items():
        triplets = extract_triplets(complete_llama, block_text)
        if len(triplets) > 0:
            file_triplets[block_id] = triplets

    if len(file_triplets) > 0:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(file_triplets, f, ensure_ascii=False, indent=2)
        count += 1

print(f"Extracted regulatory KGs: {count}")
