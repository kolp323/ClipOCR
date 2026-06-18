# 我做了一个截图转 Markdown 的 Windows 小工具：ClipOCR

> 复制一张截图，等待大模型 OCR 和版面理解完成，然后直接 `Ctrl+V` 粘贴成 Markdown。适合论文摘录、课程笔记、博客写作和 Obsidian/Typora/GitHub 文档整理。

标签建议：工具推荐、Python、Windows、OCR、Markdown、AI、效率工具

平时写笔记、整理论文、看课件或者写博客时，我经常遇到一个问题：

> 截图里的内容想复制出来，但普通 OCR 只能给我一段纯文本，标题、列表、表格、代码块这些结构基本都丢了。

所以我做了一个轻量级工具：**ClipOCR**。

它的使用方式很简单：

1. 打开 ClipOCR
2. 开始监听剪贴板
3. 复制一张截图
4. 等待识别完成
5. 直接 `Ctrl+V` 粘贴 Markdown

项目地址：

```text
https://github.com/kolp323/ClipOCR
```

下载地址：

```text
https://github.com/kolp323/ClipOCR/releases/tag/v0.2.1
```

## ClipOCR 是什么？

ClipOCR 是一个 Windows 托盘工具和命令行工具。

它会监听剪贴板里的截图，把图片发送给兼容 OpenAI Vision Chat Completions 格式的视觉模型，然后让模型完成：

- OCR 文字识别
- 文档结构理解
- Markdown 整理
- 表格转换
- 代码块保留
- 无意义换行清理

最后，ClipOCR 会把整理后的 Markdown 自动写回剪贴板。

也就是说，你复制的是截图，粘贴出来的是 Markdown。

## 适合哪些场景？

### 1. 论文和课件摘录

看到 PDF、课件、网页里的内容，不想手动打字，也不想只得到一堆乱掉的纯文本，就可以截图后交给 ClipOCR。

适合粘贴到：

- Obsidian
- Notion
- Typora
- VS Code
- GitHub README
- 博客编辑器

### 2. 表格截图转 Markdown 表格

普通 OCR 经常会把表格识别成错乱文本。

ClipOCR 会尽量把表格整理成 Markdown 表格，例如：

```markdown
| Item | Owner | Status |
| --- | --- | --- |
| CLI MVP | Alice | Done |
| GUI | Later | Planned |
```

### 3. 代码截图转代码块

如果截图中包含代码，ClipOCR 会尽量用 fenced code block 输出：

````markdown
```python
print("hello clipocr")
```
````

这样粘贴到 Markdown 编辑器里可以直接继续编辑。

## 下载和安装

打开 Release 页面：

```text
https://github.com/kolp323/ClipOCR/releases/tag/v0.2.1
```

下载：

```text
ClipOCR-v0.2.1-windows-x64.zip
```

解压后可以看到：

```text
clipocr.exe
clipocr-cli.exe
README.md
README.zh-CN.md
```

日常使用推荐双击运行：

```text
clipocr.exe
```

这是 Windows 托盘版本。

> 配图建议：GitHub Release 下载页面，标出 `ClipOCR-v0.2.1-windows-x64.zip`。

## 第一次使用：填写 API 配置

打开 `clipocr.exe` 后，需要填写几个参数：

```text
API Base URL
API Key
Model
Timeout seconds
```

示例：

```text
API Base URL: https://api.openai.com/v1
API Key: your_api_key_here
Model: gpt-4o-mini
Timeout seconds: 60
```

注意：

- 模型必须支持图片输入。
- 接口需要兼容 OpenAI `/v1/chat/completions` 图片输入格式。
- API Key 会保存在本地 `config.json` 中，不会提交到仓库。

填写完成后，点击：

```text
Save config
```

配置会自动持久化保存，下次打开会自动加载。

> 配图建议：ClipOCR 配置窗口，API Key 打码。

## 开始监听截图

点击：

```text
Start listening
```

状态会变成：

```text
running: waiting for screenshot
```

也可以使用全局快捷键：

```text
Ctrl+Alt+O
```

来启动或停止监听。

> 配图建议：主窗口显示 `running: waiting for screenshot`。

## 复制截图并自动识别

使用任意截图工具复制一张图片到剪贴板，例如：

- Windows 截图工具
- 微信截图
- QQ 截图
- 浏览器截图插件
- PDF 阅读器截图

ClipOCR 检测到新的剪贴板图片后，会自动开始识别。

状态会变成：

```text
running: recognizing
```

识别完成后：

```text
running: completed
```

此时 Markdown 已经自动写回剪贴板。

> 配图建议：日志中显示 `Recognition completed: xxx characters copied`。

## 直接粘贴 Markdown

打开你的 Markdown 编辑器，例如 Obsidian、Typora、VS Code，然后按：

```text
Ctrl+V
```

就可以得到整理后的 Markdown。

示例：

```markdown
# Meeting Notes

## Action Items

- Update the project README
- Verify the OCR workflow on Windows
- Publish the demo blog post

| Item | Owner | Status |
| --- | --- | --- |
| CLI MVP | Alice | Done |
| GUI | Later | Planned |
```

> 配图建议：左边截图，右边粘贴后的 Markdown 效果。

## 托盘行为说明

ClipOCR 是托盘常驻工具。

- 点击窗口右上角 `X`：窗口隐藏，程序继续在托盘运行
- 托盘菜单 `Open ClipOCR`：重新打开窗口
- 托盘菜单 `Start listening / Stop listening`：启动或停止监听
- 托盘菜单 `Quit`：真正退出程序
- `Ctrl+Alt+O`：切换监听状态

## CLI 使用方式

除了桌面版本，ClipOCR 也提供 CLI：

```powershell
.\clipocr-cli.exe
```

如果希望同时在终端打印 Markdown：

```powershell
.\clipocr-cli.exe --print
```

源码运行：

```powershell
python clipocr.py --print
```

## 当前限制

目前这个工具还是一个轻量版本，有一些限制：

- Windows 是主要支持平台。
- API 必须兼容 OpenAI Chat Completions 图片输入格式。
- OCR 质量取决于模型能力和截图质量。
- 同一时间只处理一张截图。
- 暂时没有 OCR 历史数据库。
- API Key 保存在本地 `config.json`，建议使用专用 Key。

## 配图清单

建议准备这些图：

1. GitHub Release 下载页，框出 `ClipOCR-v0.2.1-windows-x64.zip`
2. 解压后的文件夹，框出 `clipocr.exe`
3. ClipOCR 主窗口配置页，API Key 打码
4. 点击 `Start listening` 后的运行状态
5. 一张待识别截图，最好包含标题、列表、表格
6. 日志显示 `Recognition completed`
7. 在 Obsidian / Typora / VS Code 中 `Ctrl+V` 后的 Markdown 效果

## 总结

ClipOCR 解决的是一个很具体的小问题：

> 把截图快速变成可编辑、可复制、可继续整理的 Markdown。

它不追求复杂功能，而是希望把「截图 -> OCR -> Markdown -> 粘贴」这个流程压缩到最低摩擦。

如果你经常整理论文、课件、网页截图、技术文档或者博客素材，可以试试看。

项目地址：

```text
https://github.com/kolp323/ClipOCR
```

Release 下载：

```text
https://github.com/kolp323/ClipOCR/releases/tag/v0.2.1
```
