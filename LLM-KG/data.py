import os
import json
from utils import clean_maritime_text, sentence_sliding_window_splitter 

def prepare_chunks(input_file, output_file="processed_chunks.json"):
    """
    业务逻辑层：清洗、切分，并将所有分块汇总到一个 JSON 文件中
    """
    with open(input_file, "r", encoding="utf-8") as f:
        raw_content = f.read()

    # 1. 执行清洗
    cleaned_content = clean_maritime_text(raw_content)

    # 2. 执行基于句子的滑动窗口分割 (500 token, 10% overlap)
    chunks = sentence_sliding_window_splitter(
        cleaned_content, 
        chunk_size_limit=500, 
        overlap_rate=0.1
    )

    # 3. 汇总所有分块及其元数据
    file_basename = os.path.basename(input_file)
    all_chunks_data = []
    
    for idx, content in enumerate(chunks):
        chunk_entry = {
            "metadata": {
                "source_file": file_basename,
                "chunk_id": idx,
                "length": len(content)
            },
            "content": content
        }
        all_chunks_data.append(chunk_entry)

    # 4. 持久化为一个统一的 JSON 文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks_data, f, ensure_ascii=False, indent=4)
            
    return all_chunks_data  # 返回列表供 main 预览使用


if __name__ == "__main__":
    # --- 配置路径 ---
    input_folder = "/data/user/zhuzixuan/mount/船级社法律法规txt"
    master_json = "all_chunks_v2.json"
    
    # 存放所有文件分块的全局列表
    all_data_collector = []

    # 1. 检查目录是否存在
    if not os.path.isdir(input_folder):
        print(f"错误: 路径 {input_folder} 不是有效的目录")
    else:
        # 2. 遍历文件夹下所有的 txt 文件
        txt_files = [f for f in os.listdir(input_folder) if f.endswith(".txt")]
        print(f"找到 {len(txt_files)} 个待处理文件，准备开始分块...")

        for file_name in txt_files:
            file_path = os.path.join(input_folder, file_name)
            
            try:
                # 执行分块逻辑 (这里调用的就是你定义的 prepare_chunks)
                # 注意：为了汇总，我们可以临时传入一个占位输出名，或者修改 prepare_chunks 不让它每次都写文件
                file_chunks = prepare_chunks(file_path, output_file="last_run_temp.json")
                
                # 将该文件的分块加入全局汇总
                all_data_collector.extend(file_chunks)
                print(f"成功处理: {file_name} (分块数: {len(file_chunks)})")
                
            except Exception as e:
                print(f"处理文件 {file_name} 时发生错误: {e}")

        # 3. 最终统一保存汇总后的 master_json
        with open(master_json, "w", encoding="utf-8") as f:
            json.dump(all_data_collector, f, ensure_ascii=False, indent=4)
            
        print(f"\n--- 任务全部完成 ---")
        print(f"总计处理分块: {len(all_data_collector)}")
        print(f"汇总文件已生成: {master_json}")

        # 4. 生成简易预览文件 (debug_view.json)
        test_preview = []
        for chunk in all_data_collector[:20]: # 抽取前20个分块预览
            test_preview.append({
                "file": chunk["metadata"]["source_file"],
                "id": chunk["metadata"]["chunk_id"],
                "len": chunk["metadata"]["length"],
                "text": chunk["content"][:50].replace("\n", " ") + "..."
            })

        with open("debug_view.json", "w", encoding="utf-8") as f:
            json.dump(test_preview, f, ensure_ascii=False, indent=4)
        print(f"预览文件已更新: debug_view.json")