import torch

model_path = "/home/jsj201-2/mount1/ZhuZiXuan/LongRAG-main/models/multilingual-e5-large/pytorch_model.bin"
try:
    state_dict = torch.load(model_path)
    print("PyTorch模型文件完整，加载成功！")
except Exception as e:
    print(f"模型文件损坏: {e}")
