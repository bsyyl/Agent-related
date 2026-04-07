import re

def clean_maritime_text(text):
    """专门用于清洗海事文档页眉页脚的工具"""
    # 匹配特定的路径和页码模式
    pattern = r"DANKA\\CHINESE\\ASSEMBLY\\32\\A 32-Res\.1155\.docx.*第 A 32/Res\.1155 号决议.*附件，第 \d+ 页"
    text = re.sub(pattern, "", text)
    text = text.replace('\x0c', '') # 移除换页符
    return text

def fixed_size_splitter(text, chunk_size=2000, overlap=200):
    """策略A：固定窗口分割（带重叠，防止语义在切割点断裂）"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

def paragraph_splitter(text, max_chars=3000):
    """策略B：基于段落的分割（尽量保持条文完整）"""
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = ""
    for p in paragraphs:
        if len(current_chunk) + len(p) < max_chars:
            current_chunk += p + "\n"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = p + "\n"
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks


def sentence_sliding_window_splitter(text, chunk_size_limit=500, overlap_rate=0.1):
    """
    策略C：基于句子的滑动窗口分割
    1. 先按句号/问号/感叹号切分成独立的句子。
    2. 将句子作为最小单元，累加至接近 chunk_size_limit。
    3. 保持 10% 的滑动窗口（即下一个 chunk 会包含上一个 chunk 末尾的一部分句子）。
    """
    # 使用正则切分句子，保留分隔符（。？！）
    # [^。？！]+[。？！]? 匹配非标点字符加一个标点
    sentences = re.findall(r'[^。？！\n]+[。？！\n]?', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    if not sentences:
        return chunks

    overlap_size = int(chunk_size_limit * overlap_rate)
    
    current_idx = 0
    while current_idx < len(sentences):
        current_chunk_text = ""
        current_chunk_len = 0
        
        # 记录本块包含的最后一个句子索引，用于下一次计算起点
        last_sentence_in_chunk = current_idx
        
        for i in range(current_idx, len(sentences)):
            sent = sentences[i]
            # 简单估算：中文字符数近似为 Token 数
            sent_len = len(sent)
            
            # 如果单句就超过限制，强制放入（保证不拆散句子）
            if current_chunk_len + sent_len <= chunk_size_limit or current_chunk_len == 0:
                current_chunk_text += sent
                current_chunk_len += sent_len
                last_sentence_in_chunk = i
            else:
                break
        
        chunks.append(current_chunk_text)
        
        # 计算滑动窗口起点
        # 我们寻找从当前块末尾往前数，凑够 overlap_size 的起始句子索引
        back_len = 0
        next_start_idx = last_sentence_in_chunk + 1
        
        for j in range(last_sentence_in_chunk, current_idx, -1):
            back_len += len(sentences[j])
            if back_len >= overlap_size:
                next_start_idx = j
                break
        
        # 防止死循环（如果窗口完全没移动）
        if next_start_idx <= current_idx:
            next_start_idx = last_sentence_in_chunk + 1
            
        current_idx = next_start_idx
        
        # 如果已经处理完最后一句，跳出
        if last_sentence_in_chunk == len(sentences) - 1:
            break

    return chunks