import random
import re
import json
import yaml
from api import call_api

with open("../config/config.yaml", "r") as file:
    config = yaml.safe_load(file)

DEEPSEEK_API_URL = config["api"]["deepseek_url"]

    
def get_word_len(input_text):
    prompt = f"""请分析以下文本，并输出其 token 计数，如果是中文就是字数，如果是英文就可以比如像split()函数默认按空格分割，格式如下：

    
    {{"token_count": <integer>}}
    
    请保证思考过程和结果加起来不超过2000个token

    文本:
    {input_text}"""

    response = call_api(prompt,"qwq-32B",5000)
    print(response)
    
    match = re.search(r"\{.*?\}", response, re.DOTALL)
    if match:
        json_str = match.group(0)
        try:
            json_data = json.loads(json_str)
            token_count = json_data.get("token_count", None)
            return token_count
        except json.JSONDecodeError:
            print(f"Error: 提取的 JSON 解析失败 -> {json_str}")
            return None
    else:
        print("Error: 未找到 JSON 结构的数据")
        return None

def build_ext_instruction(model, question, answer, content, support, min_res_tokens):
    support="\n".join(support)
    prompt = f"""{support}.\nBased on the above background only, please output the original information that needs to be cited to answer the following questions. Please ensure that the information cited is detailed and comprehensive.\nQuestion: {question}.\nOutput only the original information of the required reference:"""
    
    try:
        response = call_api(prompt)
        if response is None:
            print("Error: API response is None")
            return None 
        
        print(response)

        # token_count = get_word_len(response)

        # if token_count is None or token_count < min_res_tokens:
        #     print(f"Error: Token count too low ({token_count})")
        #     return None
    except Exception as e:
        print(f"Error calling API: {e}")
        return None

    verify_prompt = f"""I am going to provide you a question, the background information, and the answer to that question. Please evaluate whether the answer can be solely derived from the given background information. If it can, set the status value as True, if it can't, set the status value as False.\nQuestion: {question}\nBackground Information: {response}\nAnswer: {answer}\nYour output format should be the following json format: {{"status": "{{the value of status}}"}}"""
    succeed=False
    try:
        flag = call_api(verify_prompt)
        if flag is None:
            print("Error: API response is None")
            return None
        
        match_flag = match_flag = re.search(r"\{.*?\}", str(flag), re.DOTALL)

        if match_flag:
            json_str = match_flag.group(0)
            try:
                flag_data = json.loads(json_str)
                status_value = flag_data.get("status","").lower()
                if status_value == "true":
                    succeed = True
            except json.JSONDecodeError:
                print(f"Error: JSON decoding failed -> {json_str}")
        else:
            print(f"Warning: No valid JSON found in response: {flag}")

    except json.JSONDecodeError as e:
        print(f"Error: JSON decoding failed -> {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    if succeed:
        return {
            "instruction": f"{content}\n\nBased on the above background, please output the information you need to cite to answer the question below.\n{question}",
            "input": "",
            "output": response
        }

    return None

def build_cot_instruction(model, question, answer, content, support, min_res_tokens):
    support="\n".join(support)
    prompt = f"""{support}\n\nGiven question: {question}\nThe answer is: {answer}\nYour task is to give your thought process for this given question based on the above information, only give me your thought process and do not output other information.\nThought process:"""

    try:
        response = call_api(prompt)
        if response is None:
            print("Error: API response is None")
            return None
        
        print(f"API Response: {response}")
        
        # token_count = get_word_len(response)
        # if token_count is None or token_count < min_res_tokens:
        #     print(f"Error: Token count too low ({token_count})")
        #     return None
    except Exception as e:
        print(f"Error calling API: {e}")
        return None

    verify_prompt = f"""Question: {question},\nThought process of the question: {response}\nAnswer: {answer}\nPlease evaluate whether the thought process of this question can explain the answer to this question. If it can explain the answer, set the value of status to "True". If it cannot explain the answer, set the value of status to "False".\nYour output format should be the following json format: {{"status": "{{the value of status}}"}}"""
    
    succeed=False
    try:
        flag = call_api(verify_prompt)
        if flag is None:
            print("Error: Verification API response is None")
            return None
        match_flag = re.search(r"\{.*?\}", str(flag), re.DOTALL)
        if match_flag:
            json_str = match_flag.group(0)
            try:
                flag_data = json.loads(json_str)
                status_value = flag_data.get("status", "").lower()
                if status_value == "true":
                    succeed = True
            except json.JSONDecodeError:
                print(f"Error: JSON decoding failed -> {json_str}")
    except json.JSONDecodeError as e:
        print(f"Error: JSON decoding failed -> {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    if succeed:
        return {
            "instruction": f"{content}\nPlease combine the above information and give your thought process for the following question:\n{question}.",
            "input": "",
            "output": response
        }

    return None

def build_rag_instruction(model, question, answer, content):
    return {
        "instruction": f"{content}\nBased on the above information, only give me the answer and do not output any other words.\nQuestion: {question}\nAnswer: ",
        "input": "",
        "output": answer
    }

def build_fil_instruction(model, question, answer, support, non_support, sup_flag):
    support_paragraphs=support
    non_paragraphs=non_support

    if not support_paragraphs and not non_paragraphs:
        print("Error: Both support_paragraphs and non_paragraphs are empty.")
        return None

    support = "\n".join(support)
    prompt = f"""{support}\n\nGiven question: {question}\nThe answer is: {answer}\nYour task is to give your thought process for this given question based on the above information, only give me your thought process and do not output other information.\nThought process:"""

    try:
        response = call_api(prompt)
        if response is None:
            print("Error: API response is None")
            return None
    except Exception as e:
        print(f"Error calling API: {e}")
        return None
    
    print(f"API Response: {response}")

    verify_prompt = f"""Question: {question},\nThought process of the question: {response}\nAnswer: {answer}\nPlease evaluate whether the thought process of this question can explain the answer to this question. If it can explain the answer, set the value of status to "True". If it cannot explain the answer, set the value of status to "False".\nYour output format should be the following json format: {{"status": "{{the value of status}}"}}"""
    
    try:
        flag = call_api(verify_prompt)
        if flag is None:
            print("Error: Verification API response is None")
            return None
        match_flag = re.search(r"\{.*?\}", str(flag), re.DOTALL)
        if match_flag:
            json_str = match_flag.group(0)
            try:
                flag_data = json.loads(json_str)
                status_value = flag_data.get("status", "").lower()
                if status_value != "true":
                    return None
            except json.JSONDecodeError:
                print(f"Error: JSON decoding failed -> {json_str}")
                return None
        else:
            print(f"Warning: No valid JSON found in response: {flag}")
            return None
        
    except json.JSONDecodeError as e:
        print(f"Error: JSON decoding failed -> {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


    if sup_flag :
        if not support_paragraphs:
            return None  # 避免 random.choice() 返回 None 但仍继续执行
        content = random.choice(support_paragraphs)
        status = '{"status":"True"}'
    else:
        if not non_paragraphs:
            return None
        content = random.choice(non_paragraphs)
        status = '{"status":"False"}'

    return {
        "instruction": f"""Given an article: {content}\nQuestion: {question}.\nThought process for the question: {response}\nYour task is to use the thought process provided to decide whether you need to cite the article to answer this question. If you need to cite the article, set the status value to True. If not, set the status value to False. Please output the response in the following json format: {{"status": "{{the value of status}}"}}""",
        "input": "",
        "output": status
    }

if __name__ == "__main__":
    print(get_word_len("我的测试文本"))
    