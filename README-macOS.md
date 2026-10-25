# macOS 新手操作指南

本指南适用于 macOS 和“终端”或 VS Code 的 bash/zsh 终端。请按顺序操作。

## 1. 打开仓库和终端

1. 在 VS Code 中打开本仓库文件夹，也就是里面能看到 `README.md` 的那一层目录。
2. 在 VS Code 左侧资源管理器中找到 `你的手写笔记请放在这个文件夹` 文件夹。如果没看到文件列表，可点击左侧文件图标，或按 `Cmd+Shift+E`。
3. 用 Finder 找到你的手写笔记 PDF，将它复制并粘贴到 `你的手写笔记请放在这个文件夹` 里面。不要把 PDF 放到 `Uri Onn作业模板` 或 `手写pdf转换latex脚本工具` 里。
4. 回到 VS Code，展开该文件夹，确认里面有且只有一个要转换的 PDF。无需改文件名；如果里面有多个 PDF，请先把本次不转换的 PDF 暂时移到其他位置。
5. 选择“终端 → 新建终端”。输入 `ls` 后按 Enter，应能看到 `README.md` 和 `手写pdf转换latex脚本工具`。如果没有，请在 VS Code 中重新打开正确的文件夹。

## 2. 安装命令行工具 Homebrew

Homebrew 用来安装 Poppler 和相关软件。如果已经安装，可跳到下一步。

1. 打开 macOS 的“终端”应用。
2. 从 [Homebrew 官方网站](https://brew.sh/)复制当前显示的安装命令，粘贴到终端并按 Enter。
3. 按屏幕提示输入 Mac 登录密码。输入密码时终端不会显示字符，这是正常的；输入后按 Enter。
4. 关闭并重新打开终端，然后验证：

```bash
brew --version
```

若提示找不到 `brew`，请按 Homebrew 网站给出的提示，将 Homebrew 加入 shell 的 PATH。

## 3. 安装 Python 和 Poppler

在终端运行：

```bash
brew install python poppler
```

安装后检查：

```bash
python3 --version
pdfinfo -v
pdftoppm -h
```

Python 版本应为 3.10 或更新版本；Poppler 两个命令都应显示版本或帮助信息。

## 4. 安装 LaTeX

推荐安装 MacTeX，它包含 `pdflatex` 和模板需要的宏包。MacTeX 文件较大，请确保网络和磁盘空间足够。

1. 打开 [MacTeX 官方下载页](https://tug.org/mactex/)并按页面说明下载、安装。
2. 安装完成后关闭并重新打开终端或 VS Code。
3. 验证：

```bash
pdflatex --version
```

若提示找不到命令，重启 Mac 后再检查；也可以确认 MacTeX 安装目录的 `bin` 路径已在 PATH 中。

## 5. 创建 Python 环境并安装绘图依赖

在 VS Code 仓库根目录终端逐行运行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install matplotlib
```

激活成功后，终端提示符前通常会出现 `(.venv)`。以后每次新开终端，都要先进入仓库根目录并运行：

```bash
source .venv/bin/activate
```

## 6. 设置 Kimi API Key

1. 在 [Kimi 开放平台](https://platform.moonshot.cn/)登录或注册。
2. 在控制台创建 API Key，确认账户有可用额度，并选择支持图片输入的模型。
3. 不要把 Key 放进代码、README、PDF 或聊天记录。在当前终端中运行：

```bash
export MOONSHOT_API_KEY='在这里粘贴你自己的API Key'
```

变量只在当前终端会话有效。新开终端后需要重新设置。安全地检查变量是否存在，不要打印 Key：

```bash
test -n "$MOONSHOT_API_KEY" && echo "API key is set" || echo "API key is missing"
```

## 7. 运行转换

把命令中的姓名、学号和作业编号替换成自己的信息。命令必须在仓库根目录运行。输入路径直接指向笔记文件夹，不用填写 PDF 文件名，也不用重命名：

```bash
python "手写pdf转换latex脚本工具/handwriting_to_latex.py" "你的手写笔记请放在这个文件夹" --api-url "https://api.moonshot.cn/v1/chat/completions" --model "kimi-k3" --api-key-env MOONSHOT_API_KEY --author "StudentName" --student-id "000000" --assignment 1 --compile
```

图形识别默认开启，不需要额外写开关。若要关闭，可在命令末尾加 `--no-draw-diagrams`。`--compile` 会生成 PDF 预览；若暂时不想编译，删掉这个参数即可。

姓名请使用英文字母或拼音，避免当前模板的 `pdflatex` 因中文姓名报 Unicode 错误。运行期间请不要关闭终端；完成时会显示输出目录。

## 8. 找到结果并校对

输出默认在输入 PDF 旁边、以原 PDF 文件名命名的 `_latex` 文件夹中。例如原文件叫 `GroupTheoryNotes.pdf`，输出目录就是 `GroupTheoryNotes_latex`。重点检查：

- `transcription.tex`：可编辑 LaTeX 草稿。
- `transcription.pdf`：编译后的预览（使用了 `--compile` 才会生成）。
- `transcription_body.tex`：模型识别出的正文。
- `figures`：识别并绘制出的图形 PDF。

打开 `transcription.pdf` 和原手写 PDF 对照检查。模型可能误认公式、点线关系或标签，确认无误后再提交。

## 常见问题

- **`brew` 找不到**：按 Homebrew 网站的安装后提示配置 PATH，并重新打开终端。
- **`pdfinfo` 或 `pdftoppm` 找不到**：运行 `brew install poppler`，然后重开终端。
- **`pdflatex` 找不到**：确认 MacTeX 安装完成，重启终端或 Mac 后再试。
- **提示缺少 Matplotlib**：激活 `.venv` 后运行 `python -m pip install matplotlib`。
- **API 返回 HTTP 401/400**：检查 Key、模型名、接口地址、图片输入权限和账户额度；不要把 Key 发给别人。
- **LaTeX 编译报错**：打开 `transcription.tex`，从编译日志第一条 `!` 错误开始检查；通常需要修正模型生成的 LaTeX。
- **输入 PDF 含有很多页或请求超时**：在转换命令中加 `--dpi 100` 降低图片分辨率，或将 PDF 拆成较短的部分。
