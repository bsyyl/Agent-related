import os
from tavily import TavilyClient

# 填入你的 Key
tavily = TavilyClient(api_key="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")

# 执行一次搜索测试
response = tavily.search("人工智能的最新发展")
print(response)

# 测试tavily的连接