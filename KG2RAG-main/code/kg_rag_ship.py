import os
import ujson as json
import argparse
from tqdm import tqdm
from FlagEmbedding import FlagReranker

# llama_index / transformers
from llama_index.core import Settings, VectorStoreIndex, PromptTemplate
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.schema import TextNode
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import ResponseMode
import torch

# util 中的后处理器（保持原样）
from util.kg_post_processor import NaivePostprocessor, KGRetrievePostProcessor, GraphFilterPostProcessor
from util.kg_response_synthesizer import get_response_synthesizer

# transformers 仅在需要时导入（这里不直接用 pipeline）
from transformers import AutoTokenizer, AutoModelForCausalLM


from builtins import print as _print
from sys import _getframe
def print(*arg, **kw):
    s = f'Line {_getframe(1).f_lineno}'
    return _print(f"Func {__name__} - {s}", *arg, **kw)

# ==================== 初始化本地模型（使用 llama_index 的 HuggingFace 接口） ====================
def init_model(args):
    print(f"Loading local HF model from {args.model_path} ...")
    # --------------------------
    # 1) 初始化 LLM
    # --------------------------
    try:
        Settings.llm = HuggingFaceLLM(
            model_name=args.model_path,
            tokenizer_name=args.model_path
        )
        print("HuggingFaceLLM loaded successfully.")
    except Exception as e:
        print(f"[Standard HuggingFaceLLM failed] {e}")
        raise e

    # --------------------------
    # 2) 初始化 Embedding（关键）
    # --------------------------
    print(f"Loading embedding model from {args.embed_model_path} ...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(args.embed_model_path)
        # if tokenizer.pad_token is None:
        #     tokenizer.add_special_tokens({"pad_token": "[PAD]"})
        #     tokenizer.save_pretrained(args.embed_model_path)
        Settings.embed_model = HuggingFaceEmbedding(
            model_name=args.embed_model_path,
            device="cpu"
        )
        print("HuggingFaceEmbedding loaded successfully.")
    except Exception as e:
        print(f"Failed to load embedding: {e}")
        raise e


# ==================== 文本读取 / 切块 ====================
def split_text_to_paragraphs(txt_path):
    """
    将 txt 按换行切块，去掉空行，返回 paragraphs 列表 [{'id':int,'text':str}, ...]
    """
    if not os.path.exists(txt_path):
        raise FileNotFoundError(f"txt file not found: {txt_path}")
    paragraphs = []
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            # 你可以在这里根据需要合并短行或识别章节标题
            paragraphs.append({'id': len(paragraphs), 'text': s})
    return paragraphs


def read_kg(kg_path):
    """
    读取已生成好的 knowledge graph JSON (doc2kg 格式)
    """
    if not os.path.exists(kg_path):
        raise FileNotFoundError(f"KG file not found: {kg_path}")
    with open(kg_path, 'r', encoding='utf-8') as f:
        kg = json.load(f)
    return kg


# ==================== RAG 问答主逻辑 ====================
def answer_question_with_text(question, paragraphs, kg, args):
    """
    question: str
    paragraphs: List[ {'id': str|int, 'text': str} ]
    kg: dict, 结构为：{ head_entity: { relation: [ tail1, tail2, ... ] } }
    """

    # --------------------------------------------------
    # 1. 构造文本节点 TextNode（纯文本段落）
    # --------------------------------------------------
    doc_chunks = []
    chunks_index = {}

    for p in paragraphs:
        node_id = f"TXT_{p['id']}"
        doc_chunks.append(TextNode(text=p["text"], id_=node_id))

    # --------------------------------------------------
    # 2. 处理 KG：展开成标准三元组 (h,r,t)
    # --------------------------------------------------
    doc2kg = {}  # GraphRAG 后处理使用的 KG

    for head_entity, ent_info in kg.items():
        chunks_index[head_entity] = {}
        doc2kg[head_entity] = {}

        if not isinstance(ent_info, dict):
            print(f"🚨 KG 实体 {head_entity} 的结构不是 dict：{ent_info}")
            continue

        for relation, tails in ent_info.items():
            if not isinstance(tails, list):
                tails = [tails]

            # 转换成标准三元组列表
            triple_list = [(head_entity, relation, tail) for tail in tails]

            # 保存到 chunks_index 用于展示
            chunks_index[head_entity][relation] = "； ".join([f"({h},{r},{t})" for h,r,t in triple_list])

            # 保存到 doc2kg 用于 GraphRAG 后处理
            doc2kg[head_entity][relation] = triple_list

    # --------------------------------------------------
    # 3. 构建文本向量索引（KG 不加入向量库）
    # --------------------------------------------------
    index = VectorStoreIndex(doc_chunks)
    retriever = VectorIndexRetriever(index=index, similarity_top_k=args.top_k)

    # --------------------------------------------------
    # 4. Prompt template（中文）
    # --------------------------------------------------
    qa_rag_template_str = (
        "你是一个船舶与海事法规领域的专业法律顾问，请根据以下参考资料回答问题，并展示基于这些资料的推理过程。\n"
        "### 问题：\n{query_str}\n\n"
        "### 参考资料（文本段落 + 三元组）：\n{context_str}\n\n"
        "请基于上述参考资料进行回答，要求：\n"
        "1. 首先分析每条资料与问题的相关性。\n"
        "2. 对三元组内容进行逻辑推理，连接相关信息以支持结论。\n"
        "3. 如果资料不足以完全回答问题，可补充你的专业知识，但请明确区分引用内容与自身知识。\n"
        "4. 最后给出明确、专业且可追溯的答案。"
    )
    qa_rag_prompt_template = PromptTemplate(qa_rag_template_str)

    response_synthesizer = get_response_synthesizer(
        response_mode=ResponseMode.COMPACT,
        text_qa_template=qa_rag_prompt_template
    )

    # --------------------------------------------------
    # 5. 后处理组件：KG 扩展 + GraphRAG
    # --------------------------------------------------
    ents = list(kg.keys())

    expansion_pp = KGRetrievePostProcessor(
        dataset=args.dataset,
        ents=ents,
        doc2kg=doc2kg,
        chunks_index=chunks_index
    )

    bge_reranker = FlagReranker(model_name_or_path=args.reranker, device=args.device)

    # filter_pp = GraphFilterPostProcessor(
    #     dataset=args.dataset,
    #     use_tpt=args.use_tpt,
    #     topk=args.top_k,
    #     ents=ents,
    #     doc2kg=doc2kg,
    #     chunks_index=chunks_index,
    #     reranker=bge_reranker
    # )

    naive_pp = NaivePostprocessor(dataset=args.dataset)

    query_engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
        node_postprocessors=[]
    )

    # --------------------------------------------------
    # 6. 执行查询
    # --------------------------------------------------
    try:
        response = query_engine.query(question)
        prediction = response.response
    except Exception as e:
        print(f"❌ Error generating answer: {e}")
        prediction = "抱歉，无法生成答案。"

    return prediction



# ==================== 主流程 ====================
def main():
    parser = argparse.ArgumentParser(description="KG-RAG Q&A for maritime regulations (local HF + llama_index)")
    parser.add_argument('--txt_path', type=str, default='../data/cug_ship/A 32-Res.1155 - 2021 年港口国监督程序 (秘书处).txt', help='Path to the input text file')
    parser.add_argument('--kg_path', type=str, default='../data/cug_ship/ship_rule_kg.json', help='Path to the KG JSON file')
    parser.add_argument('--model_path', type=str, default='/data/user/zhuzixuan/mount/KG2RAG-main/model/Llama-7b-hf', help='Local HF model path or model id')
    parser.add_argument('--embed_model_path', type=str, default='/data/user/zhuzixuan/mount/KG2RAG-main/model/bge-base-zh-v1.5', help='Local embedding model path or model id')
    parser.add_argument('--reranker', type=str, default='../model/bge-reranker-large', help='Path of the reranker model')
    parser.add_argument('--top_k', type=int, default=10, help='Top k similar documents')
    parser.add_argument('--use_tpt', type=bool, default=True, help='Whether to use triplet representation')
    parser.add_argument('--dataset', type=str, default='maritime', help='Dataset name (used in postprocessors)')
    parser.add_argument('--device', type=int, default=0, help='GPU device id for models (int)')
    args = parser.parse_args()

    # 初始化模型（会设置 Settings.llm 与 Settings.embed_model）
    init_model(args)

    # 读取并切块文本
    paragraphs = split_text_to_paragraphs(args.txt_path)
    print(f"Loaded {len(paragraphs)} paragraphs from {args.txt_path}")

    # 加载 KG
    kg = read_kg(args.kg_path)
    print(f"Loaded KG for {len(kg)} entities")

    # 用户问题（直接在这里写问题即可）
    user_question = "这里写你想提问的问题"

    # 生成答案
    answer = answer_question_with_text(user_question, paragraphs, kg, args)
    print(f"\nQ: {user_question}\nA: {answer}")


if __name__ == '__main__':
    main()
