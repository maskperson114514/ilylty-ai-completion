# ilylty-ai-completion 

VSCode 代码补全插件

> 我是一名学生，代码写得烂，别骂，你觉得可以优化的话，可以提PR，谢谢    :P

## AI 支持模型
- **Yuanbao API 逆向**（默认）
- 硅基流动 API(你可以自行修改server.py的代码)


## 安装方法
- vscode
  - 将插件拖入vscode的扩展侧边栏，
  - 配置快捷键 先按ctrl+k，再按ctrl+s, 搜索ilylty.AI.completion.trigger
    - 推荐按住F1+点按F2         :D
- server
  - ```bash
    pip install -r requirement.txt
    ```
  - 运行前，需要对服务器进行配置serverConfig.json
## 服务器配置
```json
{
    "host": "127.0.0.1",
    "port": 18090,
    "completionModel": "deep_seek_v3",
    "completionMaxRound": 10,
    "yuanbaoCookieString": ""
}
```

### 配置参数说明
- `completionModel` 可选模型：
  - `deep_seek` - R1模型（代码补全前会思考）
  - `hunyuan_t1` - R1的皮
  - `deep_seek_v3` - V3模型（不需要思考）
- `completionMaxRound` - 单次对话最大消息轮数（过高会导致模型响应迟钝）
- `yuanbaoCookieString` - Yuanbao 的 Cookie 信息

## 运行
```bash
python server.py
```
```bash
code --enable-proposed-api ilylty.ilylty-ai-completion
```
注意加上--enable-proposed-api ilylty.ilylty-ai-completion参数
然后可以
在vscode中对任意代码按快捷键了. :)


## 编译指南(如果你想修改插件配置的话)
VSCode 插件默认连接地址：`http://127.0.0.1:18090/code_completion`

如需修改地址，请按以下步骤重新编译：
```bash
git clone https://github.com/maskperson114514/ilylty-ai-completion
cd ilylty-ai-completion
npm i
# 使用 VSCode 打开该项目
```
> vscode 可能需要加上--enable-proposed-api ilylty.ilylty-ai-completion，使插件能被调试

## 打包命令
```bash
npm install -g vsce
vsce package
```

走过路过，求求点一个star吧 ，谢谢  :D