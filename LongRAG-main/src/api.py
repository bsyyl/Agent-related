import json
import re
import requests
import yaml
with open("../config/config.yaml", "r") as file:
    config = yaml.safe_load(file)["api"]


DEEPSEEK_API_URL = "http://192.168.148.10:8000/v1/chat/completions"



def remove_consecutive_repeated_sentences(text, threshold=5):
    sentences = re.split(r'([。！？,，])', text)
    
    cleaned_sentences = []
    current_sentence = None
    count = 0

    for i in range(0, len(sentences), 2):
        sentence = sentences[i].strip()
        if i + 1 < len(sentences):
            delimiter = sentences[i + 1]
        else:
            delimiter = ''

        if sentence == current_sentence:
            count += 1
        else:
            if count >= threshold:
                cleaned_sentences.append(current_sentence + delimiter)
            elif current_sentence:
                cleaned_sentences.extend([current_sentence + delimiter] * count)
            current_sentence = sentence
            count = 1

    if count >= threshold:
        cleaned_sentences.append(current_sentence + delimiter)
    else:
        cleaned_sentences.extend([current_sentence + delimiter] * count)
    
    cleaned_text = ''.join(cleaned_sentences)
    return cleaned_text


def call_api(prompt,model="qwq-32B",max_tokens=1000):
    headers = {"Content-Type": "application/json"}
    
    data = {
        "model": model,  # 你的 DeepSeek 模型名称
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        # "temperature": 0.7,
        "top_p": 0.9,
        "stop": None
    }

    print(f"📤 Sending Request: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, verify=False)
        response.raise_for_status()  # 确保请求成功
    except requests.exceptions.RequestException as err:
        print(f"Request Exception: {err}")
        return None

    try:
        response_data = response.json()
        if "choices" not in response_data:
            print("Error: API 返回缺少 'choices' 字段")
            return None
        return response_data["choices"][0]["message"]["content"]
    except (json.JSONDecodeError, KeyError) as err:
        print(f"Error parsing response: {err}")
        return None

if __name__ == "__main__":

    print(call_api("hello","qwq-32B"))
    