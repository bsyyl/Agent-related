from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

class CustomerState(TypedDict):
    question: str
    category: str
    answer: str

# 分类节点
def classify_question(state: CustomerState):
    question = state["question"].lower()
    
    if "退款" in question or "退货" in question:
        category = "refund"
    elif "物流" in question or "配送" in question:
        category = "shipping"
    elif "产品" in question or "使用" in question:
        category = "product"
    else:
        category = "general"
    
    return {"category": category}

# 处理节点
def handle_refund(state):
    return {"answer": "退款专员：请提供订单号，3个工作日内处理。"}

def handle_shipping(state):
    return {"answer": "物流客服：您的包裹正在配送中。"}

def handle_product(state):
    return {"answer": "产品顾问：请查看说明书第3页。"}

def handle_general(state):
    return {"answer": "客服：感谢咨询，还有其他问题吗？"}

# 路由函数
def route_question(state: CustomerState) -> str:
    return state["category"]

# 构建图
workflow = StateGraph(CustomerState)

workflow.add_node("classify", classify_question)
workflow.add_node("refund", handle_refund)
workflow.add_node("shipping", handle_shipping)
workflow.add_node("product", handle_product)
workflow.add_node("general", handle_general)

workflow.add_edge(START, "classify")

# 关键：条件路由
workflow.add_conditional_edges(
    "classify",
    route_question,
    {
        "refund": "refund",
        "shipping": "shipping",
        "product": "product",
        "general": "general"
    }
)

# 所有分支都到 END
workflow.add_edge("refund", END)
workflow.add_edge("shipping", END)
workflow.add_edge("product", END)
workflow.add_edge("general", END)

app = workflow.compile()

# 测试
test_questions = [
    "我想申请退款",
    "我的快递到哪了？",
    "这个产品怎么使用？",
]

for q in test_questions:
    result = app.invoke({"question": q, "category": "", "answer": ""})
    print(f"问题: {q}")
    print(f"回答: {result['answer']}\n")