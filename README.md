# ClipOCR

ClipOCR 是一个轻量级 Windows 托盘应用和命令行工具，用于把截图转换成干净、可编辑的 Markdown。它从剪切板读取图片，将选中的截图发送到兼容 OpenAI 的视觉 Chat Completions API，清理 OCR 和版面理解结果，然后把 Markdown 写回剪切板。

它适合笔记整理、博客写作、论文阅读、课件摘录、文档编写、Obsidian、Typora、GitHub Issue，以及任何需要把截图文字快速转换为结构化 Markdown 的场景。

[English README](README.en.md)

## 产品概览

ClipOCR 专注于一个快速流程：

1. 复制一张截图。
2. 让 ClipOCR 识别文字和版面结构。
3. 将可编辑的 Markdown 粘贴到编辑器中。

Windows 托盘应用是主要使用方式。它可以持续监听剪切板、手动识别当前剪切板图片，并通过窗口和托盘图标显示状态。项目也包含 CLI，便于脚本和终端工作流使用。

## 核心功能

- Windows 托盘常驻应用，带清晰的状态颜色。
- 监听剪切板中的新截图。
- 监听模式下发送图片前可确认，默认开启。
- 手动一键识别当前剪切板图片。
- 全局快捷键：`Ctrl+Alt+O` 切换监听状态。
- 支持配置兼容 OpenAI 的视觉 Chat Completions API。
- 清理 Markdown 标题、列表、表格、代码块、数学内容和空行。
- 上传前自动压缩和缩放大截图。
- 识别完成后自动写回剪切板。
- 本地轮转日志，便于排查问题。
- CLI 模式支持单次 OCR。

## 工作原理

ClipOCR 从剪切板读取图片，先进行上传前规范化处理，再连同 OCR/版面理解提示词一起发送给配置的视觉模型。模型返回内容后，ClipOCR 会清理外层 Markdown 代码块、多余空行和尾随空格，并把结果写回剪切板。

监听截图时，`confirm_auto_send` 默认开启。应用会在上传检测到的图片前询问确认，避免私密截图在没有最终确认的情况下发送到远程 API。手动识别会立即发送当前剪切板图片。

## 状态标识

| 颜色 | 状态 | 含义 |
| --- | --- | --- |
| 灰色 | 关闭 | 未监听剪切板 |
| 蓝色 | 等待截图 | 正在监听，等待新的截图图片 |
| 橙色 | 识别中 | 正在调用模型识别截图 |
| 绿色 | 识别完成 | Markdown 已写回剪切板 |
| 红色 | 错误 | 配置、API 或剪切板操作失败 |

## 下载和运行

1. 从 GitHub Releases 下载最新 Windows zip。
2. 解压到本地文件夹。
3. 运行 `clipocr.exe`。
4. 在窗口中填写 API Base URL、API Key、Model 和 Timeout。
5. 设置会保存到 `config.json`，下次启动自动加载。

Windows 发布包包含：

- `clipocr.exe`：托盘应用
- `clipocr-cli.exe`：命令行应用
- `README.md`：中文说明
- `README.en.md`：英文说明

## 配置说明

ClipOCR 使用一个本地配置文件：`config.json`。通常不需要手动编辑，因为托盘应用会自动保存设置。

示例：

```json
{
  "api_base_url": "https://api.openai.com/v1",
  "api_key": "your_api_key_here",
  "model": "gpt-4o-mini",
  "timeout": 60,
  "start_on_launch": false,
  "confirm_auto_send": true
}
```

| 字段 | 是否必填 | 说明 |
| --- | --- | --- |
| `api_base_url` | 是 | API Base URL，期望兼容 OpenAI `/v1` 接口 |
| `api_key` | 是 | API Key，以 Bearer Token 方式使用 |
| `model` | 是 | 支持图片输入的视觉模型名称 |
| `timeout` | 否 | 请求超时时间，单位秒，默认 `60`，有效范围 `5` 到 `600` |
| `start_on_launch` | 否 | 托盘应用启动时是否自动开始监听 |
| `confirm_auto_send` | 否 | 监听到图片后，上传到 API 前是否需要确认，默认 `true` |

`config.json` 只用于本地，不应提交到仓库。API Key 会保存在此文件中，建议使用专用 Key。

## 托盘应用使用方法

运行：

```powershell
.\clipocr.exe
```

常用操作：

- `Start listening`：开始监听剪切板截图。
- `Stop listening`：暂停剪切板监听。
- `Recognize current clipboard`：手动识别当前剪切板图片。
- 托盘菜单：打开窗口、切换监听、执行单次识别或退出。
- `Ctrl+Alt+O`：切换监听状态。

典型流程：

1. 启动 ClipOCR。
2. 填写并保存 API 设置。
3. 开始监听，或选择单次识别。
4. 复制一张截图到剪切板。
5. 如有提示，确认上传到 API。
6. 等待托盘图标变为绿色。
7. 将生成的 Markdown 粘贴到编辑器。

## 命令行使用

CLI 和托盘应用读取同一个 `config.json`。

```powershell
.\clipocr-cli.exe
.\clipocr-cli.exe --print
```

从源码运行：

```powershell
python clipocr.py --print
```

## 从源码安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python clipocr_app.py
```

运行测试：

```powershell
pip install -r requirements-dev.txt
python -m pytest
python -m py_compile clipocr_core.py clipocr_app.py clipocr.py
```

## 从源码构建

生成 Windows 发布文件：

```powershell
.\build-windows.ps1
```

发布文件会输出到 `release\windows`。

在 Linux 或安装了 `python3-venv` 的 WSL 中生成 Linux CLI：

```bash
bash build-linux.sh
```

Linux 剪切板支持依赖以下工具之一：

- Wayland：`wl-paste` 和 `wl-copy`
- X11：`xclip`
- 兜底：`xsel`

## 本地文件和日志

ClipOCR 可能会在程序目录旁生成这些本地文件：

- `config.json`：应用设置和 API 配置。
- `logs/clipocr.log`：本地日志文件，约 1 MB 时轮转，并保留一个 `.log.1` 备份。

这些文件已在 Git 中忽略。

## 输出示例

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

## 常见问题

### `Config file not found`

运行 `clipocr.exe`，在窗口中填写设置，让应用自动创建 `config.json`。

### 缺少配置字段

请在窗口中填写 API Base URL、API Key 和 Model，或手动创建 `config.json`。

### 托盘图标一直是蓝色

ClipOCR 正在等待剪切板图片。请复制截图，而不是普通文本。

### 识别失败

请检查 API Key 是否有效、模型是否支持图片输入、Base URL 是否兼容 OpenAI、网络是否可用。ClipOCR 会缩放大图并回退到 JPEG 压缩，但极大或非常复杂的截图仍可能需要裁剪。

### 应用为什么会询问是否发送图片

这由 `confirm_auto_send` 控制。监听模式下默认开启，避免私密截图在没有确认的情况下发送到远程 API。手动单次识别会立即发送当前剪切板图片。

### 快捷键无效

`Ctrl+Alt+O` 可能被其他应用占用。可以改用窗口按钮或托盘菜单。

## 当前限制

- Windows 是托盘应用的主要支持平台。
- Linux 目前以 CLI 支持为主，依赖系统剪切板工具。
- API 必须支持兼容 OpenAI Chat Completions 的图片输入格式。
- OCR 质量取决于所选视觉模型和截图质量。
- 同一时间只处理一张截图。
- 暂无 OCR 历史数据库。
- API Key 会保存在本地 `config.json` 中。

## 后续计划

- 可配置快捷键。
- 支持从图片文件输入。
- CLI 增加 `--no-copy` 模式。
- 失败时保存调试图片。
- OCR 历史导出。
- Markdown 清理预设。
