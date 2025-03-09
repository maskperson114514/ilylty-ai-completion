"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
const vscode = require("vscode");
// 全局状态跟踪
const triggerState = {
    active: false,
    position: null,
    documentVersion: 0
};
function activate(context) {
    // 注册鼠标中键命令
    context.subscriptions.push(vscode.commands.registerCommand('ilylty.AI.completion.trigger', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor)
            return;
        // 记录触发时的文档状态
        triggerState.active = true;
        triggerState.position = editor.selection.active;
        triggerState.documentVersion = editor.document.version;
        // 主动唤起内联补全
        // 先隐藏当前的建议候选框
        await vscode.commands.executeCommand('hideSuggestWidget');
        await vscode.commands.executeCommand('editor.action.inlineSuggest.trigger');
    }));
    // 通用补全提供器
    const provider = {
        async provideInlineCompletionItems(document, position) {
            // 验证触发有效性
            if (!triggerState.active ||
                !triggerState.position?.isEqual(position) ||
                document.version !== triggerState.documentVersion) {
                return null;
            }
            // 重置触发状态
            triggerState.active = false;
            // 获取上下文内容
            const line = document.lineAt(position.line).text;
            const modifiedLine = line.slice(0, position.character) + "<cursor>" + line.slice(position.character);
            // 获取前两行
            const previousLines = [];
            for (let i = 10; i >= 1; i--) {
                if (position.line - i >= 0) {
                    previousLines.push(document.lineAt(position.line - i).text);
                }
            }
            // 获取后两行
            const nextLines = [];
            for (let i = 1; i <= 10; i++) {
                if (position.line + i < document.lineCount) {
                    nextLines.push(document.lineAt(position.line + i).text);
                }
            }
            // 将前两行和后两行合并为一个字符串
            const surroundingLines = [...previousLines, modifiedLine, ...nextLines].join('\n');
            // 生成通用补全建议（示例逻辑）
            return this.generateCompletions(surroundingLines, position, document.uri.fsPath);
        },
        // 定义返回数据的接口
        // 补全生成逻辑（可根据需求扩展）
        async generateCompletions(line, pos, filePath) {
            const items = [];
            vscode.window.showInformationMessage('代码生成已开始，请稍候...');
            try {
                // 准备POST请求数据
                const requestData = JSON.stringify({
                    context: line,
                    position: {
                        line: pos.line,
                        character: pos.character
                    },
                    path: filePath
                });
                // 发送POST请求到指定地址
                const response = await fetch('http://127.0.0.1:18090/code_completion', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: requestData
                });
                if (response.ok) {
                    const data = await response.json(); // 使用定义的接口
                    // 从返回的JSON中获取code字段并添加到补全项
                    if (data && data.code) {
                        items.push({
                            insertText: data.code,
                            range: new vscode.Range(pos, pos)
                        });
                    }
                }
                else {
                    // 处理HTTP错误响应
                    vscode.window.showErrorMessage(`代码补全请求失败: HTTP ${response.status} - ${response.statusText}`);
                }
            }
            catch (error) {
                console.error('补全请求失败:', error);
                // 向用户显示错误通知
                vscode.window.showErrorMessage(`代码补全生成失败: ${error instanceof Error ? error.message : '未知错误'}`);
            }
            return { items };
        }
    };
    vscode.languages.registerInlineCompletionItemProvider({ pattern: '**' }, provider);
}
//# sourceMappingURL=extension.js.map