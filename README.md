# 手写群论作业转 LaTeX

这个仓库提供一个脚本：把手写作业 PDF 的每一页转成图片，再把这些图片发给 Kimi K3 视觉模型识别成 LaTeX，然后把识别结果插入老师的群论作业模板，最后可选直接编译成 PDF。默认模板位于 `Uri Onn作业模板/TemplateHW.tex`。

> 识别结果只是草稿，不是最终答案。请务必对照原 PDF 逐页检查公式、上下标、证明、颜色笔记和题号，确保最终提交内容正确。视觉模型可能会把手写的符号或公式看错。

## 1. 先看清楚：这个脚本的目标和要求

这套脚本适合以下情况：

- 你有老师给的群论作业模板；
- 你有手写 PDF 或扫描件；
- 你想把手写内容转成 LaTeX 草稿，减少手打公式的工作量；
- 你愿意使用 Kimi API（这里的示例模型固定为 `kimi-k3`）来做图片识别。

本仓库默认就是按 Kimi K3 来写的，不是通用任意模型接口；你需要在后续步骤中注册并开通 Kimi API 账户，并设置好环境变量。

由于老师模板和作业板式较固定，脚本会保留模板样式、群论宏和作业格式，只把手写题解替换进模板正文部分。

## 2. 需要安装哪些软件

你至少需要安装下面 4 样：

1. Python 3
2. Poppler（用于提取 PDF 页面并转成图片）
3. LaTeX 发行版（用于编译成 PDF）
4. Kimi 账号 + API Key + 余额

脚本本身只依赖 Python 标准库，不需要额外 `pip install`。但它会调用 `pdfinfo`、`pdftoppm` 和 `pdflatex`，所以这些命令必须能在终端中直接运行。

### 2.1 安装 Python

如果你还没装 Python，请先安装 Python 3.10 或以上版本。

- Linux/macOS：

```bash
python3 --version
```

- Windows：

```powershell
py --version
```

如果没有输出版本号，说明还没安装或没加入系统 `PATH`，请重新安装 Python，并勾选“Add Python to PATH”。

### 2.2 安装 Poppler

Poppler 提供 `pdfinfo` 和 `pdftoppm`，脚本需要它们从 PDF 中提取页面和渲染图片。

#### Linux（Ubuntu / Debian）

```bash
sudo apt update
sudo apt install poppler-utils
```

安装后检查：

```bash
pdfinfo -v
pdftoppm -h
```

#### macOS

使用 Homebrew：

```bash
brew install poppler
```

然后检查：

```bash
pdfinfo -v
pdftoppm -h
```

#### Windows

推荐安装 Poppler for Windows，并把其中的 `bin` 目录加入 `PATH`。

常见做法：

- 下载并解压到例如 `C:\poppler\poppler-24.08.0\Library\bin`
- 把该目录加入系统环境变量 `PATH`
- 重新打开终端后再检查：

```powershell
pdfinfo -v
pdftoppm -h
```

### 2.3 安装 LaTeX（TeX Live / MiKTeX / MacTeX）

如果你要让脚本自动编译出 `transcription.pdf`，就必须安装 LaTeX，并确保 `pdflatex` 命令可用。

#### Linux（推荐 TeX Live）

```bash
sudo apt update
sudo apt install texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-science
```

如果你的系统里没有 `pdflatex`，再补充：

```bash
sudo apt install texlive-full
```

不过 `texlive-full` 比较大，通常用于服务器或电脑空间充足的情况；小型环境建议用上面的常用套件即可。

检查：

```bash
pdflatex --version
```

#### macOS

推荐安装 MacTeX：

```bash
brew install --cask mactex
```

或者直接安装 MacTeX 官方包。安装后检查：

```bash
pdflatex --version
```

#### Windows

推荐安装 MiKTeX：

- 安装 MiKTeX 后，确保 `pdflatex` 在命令行中能用；
- 如果无法识别命令，重启终端或重新打开 VS Code；
- 也可以在 MiKTeX 安装时勾选“将 MiKTeX 加到 PATH”。

检查：

```powershell
pdflatex --version
```

### 2.4 这三个命令必须都能跑

在终端直接执行下面三条命令都能输出版本信息，说明环境已经准备好：

```bash
python3 --version
pdfinfo -v
pdftoppm -h
pdflatex --version
```

如果其中任何一个报“command not found”，先安装对应工具，并重新打开终端，再继续。

## 3. 注册并充值 Kimi API

你需要一个 Kimi 的账号，并拿到 API Key。这个脚本的默认模型就是 `kimi-k3`，API 地址就是 Moonshot 的 Chat Completions 接口：

```text
https://api.moonshot.cn/v1/chat/completions
```

### 3.1 注册账号

1. 打开 Kimi / Moonshot 官方网站；
2. 注册账号；
3. 完成邮箱验证；
4. 登录后进入控制台或 API 管理页面；
5. 创建/查看 API Key；
6. 确认你的账号具备可用额度，并确认你使用的是允许图像输入的模型。

### 3.2 充值 / 获取余额

很多平台需要先充值或绑定支付方式。请按平台提示操作：

- 进入“账户余额 / 计费 / API Key / 充值”页面；
- 查看可用额度；
- 确认你要用的 `kimi-k3` 可以进行图片识别；
- 复制 API Key，这个值非常敏感，不要发给别人，也不要直接贴到代码或 README 中。

### 3.3 你要用的模型名

这个脚本默认使用：

```text
--model "kimi-k3"
```

也就是说，后续运行时必须写：

```bash
--api-url "https://api.moonshot.cn/v1/chat/completions" \
--model "kimi-k3"
```

如果你用的是其他服务商或不同接口地址，`--api-url` 和 `--model` 也要按实际情况调整；不过本仓库默认以及命令示例都按 Kimi K3 来写。

## 4. 设置 API Key（环境变量）

请勿把真实 API Key 写进脚本、README、Git 仓库、作业 `.tex` 文件或聊天记录里。正确做法是把它放进终端环境变量。

### Linux / macOS / VS Code 集成终端（bash / zsh）

```bash
export MOONSHOT_API_KEY='把你自己的Kimi API Key放在这里'
```

这个变量只在当前终端会话中有效。关闭终端后需要重新设置。

如果要长期保留一个终端中可用，常见方式是把它写进 `~/.bashrc` 或 `~/.zshrc`：

```bash
echo 'export MOONSHOT_API_KEY="你的key"' >> ~/.bashrc
source ~/.bashrc
```

### Windows PowerShell

```powershell
$env:MOONSHOT_API_KEY = '把你自己的Kimi API Key放在这里'
```

如果要让它在当前 PowerShell 会话中长期可用，可以写入用户环境变量：

```powershell
[Environment]::SetEnvironmentVariable("MOONSHOT_API_KEY", "你的key", "User")
```

然后重开 PowerShell。验证变量是否存在时，不要打印真实内容：

```bash
test -n "$MOONSHOT_API_KEY" && echo "API key is set"
```

PowerShell：

```powershell
if ($env:MOONSHOT_API_KEY) { "API key is set" }
```

## 5. 开始使用！在仓库根目录运行脚本

先打开 VS Code，选中这个仓库根目录，打开集成终端，然后切到仓库根目录。下面的命令假设当前目录正是本仓库根目录。

非常重要：你自己的手写作业 PDF 一般要放在这个仓库的根目录里，而不是放进 `手写pdf转换latex脚本工具/` 里面。也就是说，推荐长这样：

```text
Tools-to-change-handwrittng-pdf-to-latex-pdf-using-in-Introduction-To-Group-/
├── README.md
├── 手写作业.pdf
├── Uri Onn作业模板/
├── 手写pdf转换latex脚本工具/
└── ...
```

这样你在终端中运行脚本时，直接写：

```bash
python3 "手写pdf转换latex脚本工具/handwriting_to_latex.py" "手写作业.pdf" ...
```

如果你把 PDF 放在别的文件夹里，也可以直接写完整路径，例如：

```bash
python3 "手写pdf转换latex脚本工具/handwriting_to_latex.py" "/Users/你/Downloads/作业一.pdf" ...
```

但新手最省事的做法是：把 PDF 放进仓库根目录，文件名尽量简短、无中文空格，方便拷贝命令。

### 5.1 运行示例（推荐新手先使用）

把 `手写作业.pdf` 换成你自己真实的 PDF 文件名，并把 `你的姓名`、`你的学号` 替换掉：

```bash
python3 "手写pdf转换latex脚本工具/handwriting_to_latex.py" \
  "手写作业.pdf" \
  --api-url "https://api.moonshot.cn/v1/chat/completions" \
  --model "kimi-k3" \
  --api-key-env MOONSHOT_API_KEY \
  --author "你的姓名" \
  --student-id "你的学号" \
  --assignment 1 \
  --compile
```

Windows PowerShell：

```powershell
py "手写pdf转换latex脚本工具/handwriting_to_latex.py" "手写作业.pdf" --api-url "https://api.moonshot.cn/v1/chat/completions" --model "kimi-k3" --api-key-env MOONSHOT_API_KEY --author "你的姓名" --student-id "你的学号" --assignment 1 --compile
```

### 5.2 这个命令中每个参数是干什么的

- `手写作业.pdf`：输入的手写作业 PDF 文件；
- `--api-url`：模型服务的接口地址；
- `--model`：这里固定是 `kimi-k3`；
- `--api-key-env`：告诉脚本从哪个环境变量读取 API Key；
- `--author`：输出 LaTeX 中的作者姓名；
- `--student-id`：输出 LaTeX 中的学号；
- `--assignment`：作业编号，例如 1、2、3；
- `--compile`：在生成 LaTeX 后立即编译成 PDF 预览；
- `--template`：如果老师换模板，可显式指定模板路径；
- `-o`：输出目录别名，避免覆盖旧结果。

### 5.3 可选：不调用模型，只生成原件视觉版

如果你只是想保留手写作业的视觉效果，不需要转成可编辑 LaTeX，可以直接执行：

```bash
python3 "手写pdf转换latex脚本工具/handwriting_to_latex.py" "手写作业.pdf" --mode faithful --compile
```

这会生成 `faithful.tex` 和 `faithful.pdf`，但它不是“可编辑公式版”的 LaTeX，只是原件视觉封装。

## 6. 输出文件位置

脚本默认把结果输出到和 PDF 同级目录下的 `<PDF文件名>_latex/` 文件夹中。

例如：

```text
作业一.pdf
作业一_latex/
├── transcription.tex
├── transcription.pdf
├── transcription_body.tex
├── faithful.tex
├── faithful.pdf
├── pages/
├── source.pdf
├── manifest.json
└── ...
```

这些文件的含义：

- `transcription.tex`：插入老师模板后的可编辑 LaTeX 草稿；
- `transcription.pdf`：编译后的 PDF 预览；
- `transcription_body.tex`：模型只返回的正文部分；
- `faithful.tex`：保留原 PDF 页面视觉效果的 LaTeX；
- `faithful.pdf`：原稿视觉版 PDF；
- `pages/`：模型实际看见的图片页面；
- `source.pdf`：输入 PDF 的副本；
- `manifest.json`：本次转换元信息，包含模型名、页数和文件记录，不写 API 密钥。

如果你想保留之前的输出，不想覆盖原目录，可以指定新输出目录：

```bash
python3 "手写pdf转换latex脚本工具/handwriting_to_latex.py" "手写作业.pdf" --api-url "https://api.moonshot.cn/v1/chat/completions" --model "kimi-k3" --api-key-env MOONSHOT_API_KEY -o "作业一_第二次转换" --compile
```

## 7. 老师模板的使用方式

默认模板路径：

```text
Uri Onn作业模板/TemplateHW.tex
```

如果老师换了模板，先备份原模板，确保不丢原文件。然后在运行中指定：

```bash
python3 "手写pdf转换latex脚本工具/handwriting_to_latex.py" "手写作业.pdf" \
  --api-url "https://api.moonshot.cn/v1/chat/completions" \
  --model "kimi-k3" \
  --api-key-env MOONSHOT_API_KEY \
  --template "模板文件夹/TemplateHW.tex" \
  --compile
```

脚本会保留模板的格式、导言区和群论宏，只把手写题解替换到正文部分；同时支持自定义：

- `--author`
- `--student-id`
- `--assignment`

## 8. 常见问题与解决办法

### `set the API key in environment variable ...`

说明脚本没有找到你设置好的环境变量。

检查办法：

```bash
echo "$MOONSHOT_API_KEY"
```

不要直接把它打印出来给别人；只确认它是否存在。正确做法是：

```bash
test -n "$MOONSHOT_API_KEY" && echo "API key is set"
```

### `Vision API returned HTTP 400`

通常是因为：

- 模型名写错；
- API 地址写错；
- 账户不支持图片输入；
- 余额或权限不足；
- 传入的数据格式不符合服务商要求。

你可以把报错里列出的服务商返回消息看一眼，但不要把 API Key 贴出来。

### `HTTP 401`

大概率是密钥不正确、已失效，或者你使用了错误的平台账号中的 Key。

### `Could not find TemplateHW.tex`

说明脚本没找到老师模板。可显式指定：

```bash
--template "Uri Onn作业模板/TemplateHW.tex"
```

### `pdflatex` 编译错误

很多时候不是 Python 脚本出问题，而是模型生成的 LaTeX 语法不规范。解决办法：

1. 打开生成的 `transcription.tex`；
2. 看第一条 `!` 报错；
3. 修正对应环境或公式；
4. 重新运行编译，或者直接在 VS Code 中用 LaTeX 扩展查看；
5. 视觉识别结果一定要人工校对。

### 图片太大、请求超时、或者看起来很慢

脚本默认可能一次发很多页图片；长作业可以拆成几段分开跑。常见方案：

```bash
--dpi 100
```

降低图片分辨率，减小请求体大小。

## 9. 隐私与费用说明

- 手写作业 PDF 会上传到你指定的模型服务商；
- 这意味着你必须确认自己接受该服务商的数据处理方式；
- 作业内容属于你的学习材料，不能随意上传到不受信任的平台；
- 视觉 API 通常按图片输入和文本输出计费；
- 具体费用、速率限制、图片大小限制和可用模型，请以服务商官方文档为准；
- 第一次使用时，建议先用一页 PDF 测试，确认费用和识别质量都合适，再批量跑整份作业。

## 10. 离线测试（不需要真实 API）

这个仓库有离线测试，模拟 API 返回，不会真实上传内容，也不需要 API 密钥：

```bash
python3 -m unittest discover -s "手写pdf转换latex脚本工具" -p 'test_*.py' -v
```

如果要看脚本参数：

```bash
python3 "手写pdf转换latex脚本工具/handwriting_to_latex.py" --help
```

## 11. 新手最简操作顺序

如果你是第一次使用，可以按这个顺序：

1. 安装 Python 3；
2. 安装 Poppler；
3. 安装 LaTeX（TeX Live / MiKTeX / MacTeX）；
4. 确认 `python3 --version`、`pdfinfo`、`pdftoppm`、`pdflatex` 都能用；
5. 在 Kimi 平台注册账号并充值；
6. 创建或复制 API Key；
7. 在终端设置 `MOONSHOT_API_KEY`；
8. 运行脚本；
9. 检查生成的 `transcription.tex` 和 `transcription.pdf`；
10. 对照原 PDF 手动修正公式、符号和结论；
11. 再提交最终结果。

## 12. 结论

这套脚本不是“无脑一键生成最终作业”，而是“把手写作业转成 LaTeX 草稿”的辅助工具。对于群论作业这种公式密集、证明严格的题目，视觉模型只能作为加速手段，最终质量仍然靠人工核对。

如果你按照上面的步骤完成安装与设置，基本就可以正常运行这个脚本并将 Kimi K3 作为指定模型来识别你的手写作业。