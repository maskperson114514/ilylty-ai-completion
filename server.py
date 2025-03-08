from flask import Flask, jsonify, request
import requests
import json

system_prompt= """
请补全以下代码片段中的 <cursor> 部分。只输出 <cursor> 部分应该填入的代码，不要包含任何其他字符、单词、解释、说明或代码分隔符（例如 ```）。严格按照原代码的缩进和格式。
- 用户可能发送路径，注意路径结构和后缀，你可以预测要补全什么代码。例如，如果路径是 "/static/js/main.js"，则可能与静态文件服务相关；如果路径是 "/api/users"，则可能与 API 路由相关；如果路径是 "/templates/index.html",则可能与模板渲染有关。

预期输出格式：
[直接输出<cursor>部分的代码，不包含任何其他内容]

用户:$
"""

def parse_sse_data_many(sse_text):
    """
    Parses SSE (Server-Sent Events) data from a text string and structures it into a list of dictionaries.

    Args:
        sse_text: A string containing the SSE data, where each event/data is separated by a newline.

    Returns:
        A list of dictionaries, where each dictionary represents a parsed SSE event or data payload.
        The dictionary structure depends on the type of SSE data.
        - For 'event' lines: {'type': 'event', 'name': event_name}
        - For 'data' lines with JSON: {'type': 'data', 'content': json_payload}
        - For 'data' lines with plain text: {'type': 'data', 'content': text_string}
        - For 'data' lines with special markers (like [plugin: ], [MSGINDEX:4], etc.): {'type': 'marker', 'content': marker_string}
    """
    parsed_data = []
    lines = sse_text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith("event:"):
            event_name = line[len("event:"):].strip()
            parsed_data.append({"type": "event", "name": event_name})
        elif line.startswith("data:"):
            data_content = line[len("data:"):].strip()
            if data_content.startswith('{') and data_content.endswith('}'):
                try:
                    json_payload = json.loads(data_content)
                    parsed_data.append({"type": "data", "content": json_payload})
                except json.JSONDecodeError:
                    parsed_data.append({"type": "err_data", "content": data_content}) # Treat as string if JSON parsing fails
            elif data_content.startswith('[') and data_content.endswith(']'):
                marker_string = data_content[1:-1] # Remove brackets
                parsed_data.append({"type": "marker", "content": marker_string})
            else:
                parsed_data.append({"type": "other_data", "content": data_content})
    return parsed_data
def parse_sse_data(line):
    line = line.strip()
    if line.startswith("event:"):
        event_name = line[len("event:"):].strip()
        return {"type": "event", "name": event_name}
    elif line.startswith("data:"):
        data_content = line[len("data:"):].strip()
        if data_content.startswith('{') and data_content.endswith('}'):
            try:
                json_payload = json.loads(data_content)
                return {"type": "data", "content": json_payload}
            except json.JSONDecodeError:
                return {"type": "err_data", "content": data_content} # Treat as string if JSON parsing fails
        elif data_content.startswith('[') and data_content.endswith(']'):
            marker_string = data_content[1:-1] # Remove brackets
            return {"type": "marker", "content": marker_string}
        else:
            return {"type": "other_data", "content": data_content}


class yuanBao:
    def __init__(self, model = "deep_seek", cookies = ""):#deep_seek,hunyuan_t1,deep_seek_v3
        self.session = requests.Session()
        self.model = model

        cookies_dict = self.cookies_string_to_dict(cookies)
        self.session.headers.update({
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://yuanbao.tencent.com',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            't-userid': cookies_dict["hy_user"],
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36',
            'x-agentid': 'naQivTmsDa',
            'x-id': cookies_dict["hy_user"],
            'x-requested-with': 'XMLHttpRequest',
            'x-source': 'web',
            })
        self.session.cookies.update(cookies_dict)

        #创建会话

        url = "https://yuanbao.tencent.com/api/user/agent/conversation/create"

        payload = {
            "agentId": "naQivTmsDa"
        }
        response = self.session.request("POST", url, json=payload)
        if response.status_code == 200:
            self.chat_id = response.json()["id"]
        else:
            raise response.status_code

    def chat_with_stream(self,prompt,needSearch = False):
        url = f'https://yuanbao.tencent.com/api/chat/{self.chat_id}'
        payload = {"model":"gpt_175B_0404","prompt":prompt,"plugin":"Adaptive","displayPrompt":prompt,"displayPromptType":1,"options":{"imageIntention":{"needIntentionModel":True,"backendUpdateFlag":2,"intentionStatus":True}},"multimedia":[],"agentId":"naQivTmsDa","supportHint":1,"version":"v2","chatModelId":self.model}
        if needSearch:
            payload["supportFunctions"] = ["supportInternetSearch"]
        data = ""
        with self.session.post(url, json=payload, stream=True) as response:
            for line in response.iter_lines():
                try:
                    decoded_line = line.decode('utf-8')
                    format_data = parse_sse_data(decoded_line)
                    yield format_data  # 直接抛出原始数据流
                except Exception as e:
                    yield {'content': e, 'type': 'error'}
    def chat_with_block(self,prompt,needSearch = False):
        url = f'https://yuanbao.tencent.com/api/chat/{self.chat_id}'
        payload = {"model":"gpt_175B_0404","prompt":prompt,"plugin":"Adaptive","displayPrompt":prompt,"displayPromptType":1,"options":{"imageIntention":{"needIntentionModel":True,"backendUpdateFlag":2,"intentionStatus":True}},"multimedia":[],"agentId":"naQivTmsDa","supportHint":1,"version":"v2","chatModelId":self.model}
        if needSearch:
            payload["supportFunctions"] = ["supportInternetSearch"]
        data = ""
        response =  self.session.post(url, json=payload)
        return parse_sse_data_many(response.text)

    def stop_chat(self):
        url = f'https://yuanbao.tencent.com/api/stop/chat/{self.chat_id}'
        resp = self.session.request("POST", url)
        if resp.status_code == 200:
            return True
        return False
    def cookies_string_to_dict(self,cookie_string):
        """
        将 cookies 字符串转换为字典。

        Args:
            cookie_string: cookies 字符串，例如 "cookieName1=cookieValue1; cookieName2=cookieValue2"

        Returns:
            一个字典，键是 cookie 名称，值是 cookie 值。
            如果输入字符串为空或格式不正确，则返回空字典。
        """
        cookies_dict = {}
        if not cookie_string:
            return cookies_dict  # 返回空字典如果输入为空

        cookie_pairs = cookie_string.split(';')
        for pair in cookie_pairs:
            pair = pair.strip()  # 去除首尾空格
            if not pair:
                continue  # 跳过空字符串

            if '=' in pair:
                name, value = pair.split('=', 1)  # 只分割第一个 '='
                cookies_dict[name.strip()] = value.strip()
            # else:
            #     # 可选：处理没有值的 cookie，例如 "cookieNameWithoutValue;"
            #     # 你可以决定如何处理这种情况，例如忽略或者将值设置为 None
            #     pass  # 这里选择忽略没有值的 cookie

        return cookies_dict
        
    def test_cookie(self):
        d = self.session.get("https://httpbin.org/get").text
        print(d)


def openai_api_call(user_prompt, api_key="", model="Qwen/Qwen2.5-Coder-32B-Instruct"):
    # API 的 URL
    print(user_prompt)
    url = "https://api.siliconflow.cn/v1/chat/completions"
    
    # 请求头，包含 API 密钥
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    
    # 请求体，包含模型和消息
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    
    # 发送 POST 请求
    response = requests.post(url, headers=headers, json=data)
    
    # 检查响应状态码
    if response.status_code == 200:
        # 解析响应内容
        response_data = response.json()
        return response_data['choices'][0]['message']['content']
    else:
        # 如果请求失败，抛出异常或返回错误信息
        raise Exception(f"API 请求失败，状态码: {response.status_code}, 错误信息: {response.text}")


app = Flask(__name__)
YB_sessions = {}
def read_config(file_path):
    """读取配置文件并返回配置内容"""
    with open(file_path, 'r', encoding='utf-8') as file:
        config = json.load(file)
    return config
#init
CONFIG = read_config('serverConfig.json')


@app.route('/code_completion', methods=['POST'])
def code_completion():
    global YB_sessions
    # 示例数据
    """
    payload:{
                    context: line,
                    position: {
                        line: pos.line,
                        character: pos.character
                    }
                    path
                }
    """
    payload = request.json  # 获取请求中的 JSON 数据
    print(payload)
    #code = openai_api_call(f"//path:{payload['path']}\n" + payload['context'])
    #yuanbao
    current_session,current_round = YB_sessions.get("p"+payload['path'],[None,CONFIG["completionMaxRound"]])
    if (not current_session) or (current_round<=0):
        current_session = yuanBao(model=CONFIG["completionModel"],cookies=CONFIG["yuanbaoCookieString"])
        YB_sessions["p"+payload['path']] = [current_session, CONFIG["completionMaxRound"]]
        current_round = CONFIG["completionMaxRound"]
    user_prompt = f"//path:{payload['path']}\n" + payload['context']
    if current_round%3==CONFIG["completionMaxRound"]%3:#每3次发送system_prompt,防止llm忘记
        user_prompt = system_prompt.replace("$", user_prompt, 1)
    
    code_list = []
    for word in current_session.chat_with_stream(prompt=user_prompt):
        if word == None:
            continue
        if word["type"] == 'data':
            if word["content"]["type"] == "text":
                code_list.append(word["content"].get('msg',""))
    YB_sessions["p"+payload['path']][1] -=1
    data = {
        "code": ''.join(map(str, code_list))
    }
    #后处理,害得靠自己
    data["code"].replace(r"\n","\n")
    print(data)
    return jsonify(data)
if __name__ == '__main__':
    app.run(host=CONFIG["host"], port=CONFIG["port"],debug=False)
    