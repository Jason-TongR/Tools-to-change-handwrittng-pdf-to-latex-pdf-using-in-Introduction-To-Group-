# 手写作业视觉转写工具

脚本把 PDF 页面图像发送到用户指定的视觉模型，并把返回的 LaTeX 正文放入课程提供的 `TemplateHW.tex`。API 密钥从环境变量读取，不会写入命令参数、源码、输出文件或日志。

视觉模型的结果仍需人工对照原稿校对，特别是数学符号、上下标和颜色批注。脚本会要求模型把确实辨认不出的内容标注为红色 `[unclear: ...]`，不应把未经校对的结果直接当最终提交稿。

## 支持的 API

目前使用 OpenAI Chat Completions 兼容的视觉请求格式：`POST <api-url>`，`Authorization: Bearer ...`，JSON 中包括 `model`、`messages`、`temperature`、`max_tokens`；页面图片以 JPEG data URL 发送。确认你的服务商支持 `image_url` 图片输入和所选模型的视觉能力。API URL 应是完整 endpoint，例如服务商文档提供的 `/v1/chat/completions` 地址。

图片会发送给该 API 服务商。请只使用你信任且有权上传作业内容的服务。

## 准备

- Python 3
- Poppler：`pdfinfo`、`pdftoppm`
- 若需生成 PDF：TeX Live 的 `pdflatex` 及模板所用 LaTeX 套件
- 一个支持图片输入且兼容上述 API 格式的视觉模型

把密钥放入环境变量，不要写入脚本或仓库：

```bash
export VISION_API_KEY='你的服务商API密钥'
```

## 使用

从仓库根目录运行：

```bash
python3 "手写pdf转换latex脚本工具/handwriting_to_latex.py" \
  "Jason的群论作业/Assignment 1/Handwriting version/Assignment 1.pdf" \
  --api-url "https://你的服务商/v1/chat/completions" \
  --model "你的视觉模型ID" \
  --author "Rui Tang" \
  --student-id "999025489" \
  --assignment 1 \
  --compile
```

默认自动使用 `Jason的群论作业/TemplateHW.tex`，输出到 PDF 旁的 `<PDF名称>_latex/`。主要文件：

- `transcription.tex`：使用老师模板生成的可编辑 LaTeX 作业。
- `transcription_body.tex`：模型原样返回的转写正文，便于单独检查。
- `faithful.tex` / `faithful.pdf`：把源 PDF 原样嵌入 LaTeX，作为视觉备份。
- `pages/`：发给模型的页面图片。
- `manifest.json`：记录模型名、页数和生成文件；不含 API 密钥或完整 API URL。

仅做视觉转写而不生成原样备份，可加 `--mode visual`。只制作嵌入原稿的忠实副本、完全不调用 API，可用 `--mode faithful`。如模板不在默认位置，使用 `--template /path/to/TemplateHW.tex`。更多选项见：

```bash
python3 "手写pdf转换latex脚本工具/handwriting_to_latex.py" --help
```

脚本默认会把整份文档图片放进一次模型请求，以便模型保持题目上下文；长 PDF 可能超过服务商的请求大小或上下文限制。可降低 `--dpi`（默认 160，范围 72-300），或先拆分 PDF 分段转写。`--max-tokens` 和 `--timeout` 可按服务商限制调整。

## 离线测试

不调用外部 API、不需要密钥：

```bash
python3 -m unittest discover -s "手写pdf转换latex脚本工具" -p 'test_*.py' -v
```
