import os
import re
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from prompt import SYSTEM_PROMPT 

load_dotenv()

def run_extraction(input_json_path="/data/user/zhuzixuan/mount/Agent-related/LLM-KG/processed_chunk/all_chunks_v1.json", output_file="processed_kg/maritime_kg_final.json"):
    # 1. 初始化输出目录
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 2. 初始化 LLM
    llm = ChatOpenAI(
        base_url="http://10.126.126.209:8000/v1",
        api_key="EMPTY",
        model="llm",
        temperature=0
    )

    # 3. 读取分块数据
    if not os.path.exists(input_json_path):
        print(f"错误：找不到分块文件 {input_json_path}")
        return

    with open(input_json_path, "r", encoding="utf-8") as f:
        chunks_data = json.load(f)

    # 这是最终存储所有知识条目的列表
    kg_triples_collection = []

    print(f"开始构建知识图谱，共需处理 {len(chunks_data)} 个分块...")

    # 4. 逐个 Chunk 处理
    for item in chunks_data:
        meta = item["metadata"]
        chunk_id = meta["chunk_id"]
        source_file = meta["source_file"]
        
        print(f"正在抽取: {source_file} [Chunk {chunk_id}]...")

        try:
            res = llm.invoke([
                ("system", SYSTEM_PROMPT),
                ("user", item["content"])
            ])
            
            # 清洗 DeepSeek/R1 等模型的思考过程
            content = res.content
            if "</think>" in content:
                match = re.search(r"</think>\s*(.*)", content, re.DOTALL)
                final_json_str = match.group(1).strip() if match else content.strip()
            else:
                final_json_str = content.strip()

            # 清洗 Markdown 标签
            clean_json_str = re.sub(r"```json|```", "", final_json_str).strip()
            
            # 解析得到当前 Chunk 的三元组列表
            current_chunk_triples = json.loads(clean_json_str)
            
            if isinstance(current_chunk_triples, list):
                # 5. 为每个三元组注入溯源信息，并存入总表
                for triple in current_chunk_triples:
                    # 给每个三元组打上“出生证明”
                    triple["source_info"] = {
                        "file": source_file,
                        "chunk_id": chunk_id
                    }
                    kg_triples_collection.append(triple)
                
                # 每处理完一个 Chunk，就保存一次，防止程序意外中断
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(kg_triples_collection, f, ensure_ascii=False, indent=4)
                    
        except Exception as e:
            print(f"警告：Chunk {chunk_id} 抽取失败，错误原因: {e}")
            continue

    print(f"\n--- 知识图谱构建完成 ---")
    print(f"1. 最终 KG 文件位置: {output_file}")
    print(f"2. 累计抽取三元组数量: {len(kg_triples_collection)} 条")

if __name__ == "__main__":
    run_extraction()