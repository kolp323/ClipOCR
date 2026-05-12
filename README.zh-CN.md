# ClipOCR

ClipOCR 是一个轻量级 Windows 托盘应用和命令行工具。它可以持续监听剪切板中的截图，将图片发送给可配置的视觉大模型 API，完成 OCR 和版面理解，然后整理成干净的 Markdown，并自动写回剪切板。

它适合低摩擦笔记、博客写作、论文/课件摘录、Obsidian、Typora、GitHub 文档，以及任何“截图转可编辑 Markdown”的场景。

[English README](README.md)

## 功能特性

- Windows 托盘常驻应用，带状态颜色标识
- 可通过窗口、托盘菜单或快捷键启动/停止剪切板监听
- 全局快捷键：`Ctrl+Alt+O` 切换监听状态
- 支持手动识别当前剪切板图片
- 支持配置 OpenAI-compatible Vision Chat Completions API
- 自动进行 OCR 和版面理解，输出 Markdown
- 尽量保留标题、列表、表格、代码块和合理空行
- 识别完成后自动把 Markdown 写回剪切板
- 支持窗口日志和本地日志文件
- 保留 CLI 模式，方便脚本或终端使用

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
5. 设置会自动保存到 `config.json`，下次启动自动加载。

发布包包含：

- `clipocr.exe`：托盘应用
- `clipocr-cli.exe`：命令行应用
- `README.md`：英文说明
- `README.zh-CN.md`：中文说明

## 配置说明

程序只使用一个本地配置文件：`config.json`。

通常不需要手动编辑它。你在窗口中填写参数后，ClipOCR 会自动保存。

手动 `config.json` 示例：

```json
{
  "api_base_url": "https://api.openai.com/v1",
  "api_key": "your_api_key_here",
  "model": "gpt-4o-mini",
  "timeout": 60,
  "start_on_launch": false
}
```

配置项：

| 字段 | 是否必填 | 说明 |
| --- | --- | --- |
| `api_base_url` | 是 | API Base URL，期望兼容 OpenAI `/v1` 接口 |
| `api_key` | 是 | API Key，以 Bearer Token 方式使用 |
| `model` | 是 | 支持图片输入的视觉模型名称 |
| `timeout` | 否 | 请求超时时间，单位秒，默认 `60` |
| `start_on_launch` | 否 | 托盘应用启动时是否自动开始监听 |

`config.json` 只用于本地，不应提交到仓库。

注：对于没有用过 api 的朋友可以使用这个中转站的 api 服务 https://www.duckcoding.ai/register?aff=Uh5W。

## 托盘应用使用方法

运行：

```powershell
.\clipocr.exe
```

可用操作：

- 点击 `Start listening` 开始监听剪切板截图。
- 点击 `Stop listening` 暂停监听。
- 点击 `Recognize current clipboard` 手动识别当前剪切板图片。
- 通过托盘右键菜单执行同样操作。
- 按 `Ctrl+Alt+O` 切换监听状态。
- 关闭窗口后程序仍在托盘运行。
- 通过托盘菜单中的 `Quit` 完全退出。

典型流程：

1. 启动 ClipOCR。
2. 在窗口中填写并保存 API 设置。
3. 开始监听。
4. 复制一张截图到剪切板。
5. 等待托盘图标变为绿色。
6. 直接粘贴生成的 Markdown 到编辑器。

## 命令行使用方法

CLI 和托盘应用读取同一个 `config.json`。

单次识别：

```powershell
.\clipocr-cli.exe
```

同时在终端打印 Markdown：

```powershell
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

## 从源码打包

生成 Windows 发布文件：

```powershell
.\build-windows.ps1
```

发布文件会输出到 `release\windows`：

- `clipocr.exe`：托盘应用
- `clipocr-cli.exe`：命令行应用
- `README.md`
- `README.zh-CN.md`

在 Linux 或安装了 `python3-venv` 的 WSL 中生成 Linux CLI：

```bash
bash build-linux.sh
```

Linux 剪切板支持依赖以下工具之一：

- Wayland：`wl-paste` 和 `wl-copy`
- X11：`xclip`
- 兜底：`xsel`

## 日志和本地文件

ClipOCR 可能会在程序目录旁生成这些本地文件：

- `config.json`：应用设置和 API 配置
- `logs/clipocr.log`：本地日志

这些文件已在 `.gitignore` 中忽略。

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

### 报错 `Config file not found`

运行 `clipocr.exe`，在窗口中填写配置，让程序自动创建 `config.json`。

### 报错 `Missing environment variables` 或配置字段缺失

旧版本使用 `.env`。新版本使用 `config.json`。请在窗口中填写配置，或手动创建 `config.json`。

### 托盘图标一直是蓝色

说明程序正在等待剪切板图片。请复制截图图片，而不是普通文本。

### 识别失败

请检查：

- API Key 是否有效。
- 模型是否支持图片输入。
- Base URL 是否兼容 OpenAI 接口。
- 网络是否可用。
- 截图是否过大，超过模型限制。

### 快捷键无效

`Ctrl+Alt+O` 可能被其他程序占用。可以改用窗口按钮或托盘菜单。

## 当前限制

- Windows 是托盘应用的主要支持平台。
- Linux 目前偏 CLI 支持，依赖系统剪切板工具。
- API 必须支持 OpenAI-compatible Chat Completions 图片输入格式。
- OCR 质量取决于模型能力和截图质量。
- 同一时间只处理一张截图。
- 暂无 OCR 历史数据库。
- API Key 会保存在本地 `config.json` 中，建议使用专用 Key。

## 后续计划

- 可配置快捷键
- 支持从图片文件输入
- CLI 增加 `--no-copy` 模式
- 失败时保存调试图片
- OCR 历史导出
- 更细的 Markdown 清洗预设
