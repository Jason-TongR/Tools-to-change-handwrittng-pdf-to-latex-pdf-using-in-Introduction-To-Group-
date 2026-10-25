# Windows 新手操作指南

本指南适用于 Windows 10/11 和 PowerShell。请按顺序操作；命令中的路径和示例信息都可以按你的实际情况替换。

## 1. 打开仓库和终端

1. 在 VS Code 中打开本仓库文件夹，也就是里面能看到 `README.md` 的那一层目录。
2. 在 VS Code 左侧“资源管理器”中找到 `你的手写笔记请放在这个文件夹` 文件夹。如果没看到左侧文件列表，可点击左侧文件图标，或按 `Ctrl+Shift+E`。
3. 用 Windows 文件资源管理器找到你的手写笔记 PDF，将它复制并粘贴到 `你的手写笔记请放在这个文件夹` 里面。不要把 PDF 放到 `Uri Onn作业模板` 或 `手写pdf转换latex脚本工具` 里。
4. 回到 VS Code，展开该文件夹，确认里面有且只有一个要转换的 PDF。无需改文件名；如果里面有多个 PDF，请先把本次不转换的 PDF 暂时移到其他位置。
5. 在 VS Code 菜单中选择“终端 → 新建终端”。如果终端不是 PowerShell，可点终端面板右上角的下拉菜单并选择 PowerShell。
6. 输入 `dir` 后按 Enter。输出中应能看到 `README.md` 和 `手写pdf转换latex脚本工具`。如果没有，请在 VS Code 中重新打开正确的仓库目录。

## 2. 安装 Python

1. 打开 [Python for Windows 官方下载页](https://www.python.org/downloads/windows/)并下载 Python 3.10 或更新版本。
2. 运行安装程序，务必勾选 **Add python.exe to PATH**，再选择安装。
3. 完成后关闭并重新打开 VS Code。
4. 在 PowerShell 中运行：

```powershell
py --version
```

看到 `Python 3...` 版本号即安装成功。若提示找不到 `py`，重新运行安装程序并确认已安装 Python Launcher。

## 3. 安装 Poppler

Poppler 提供 `pdfinfo` 和 `pdftoppm`，用来读取 PDF 页数和把页面转换成图片。

1. 打开 [Poppler for Windows 发布页](https://github.com/oschwartz10612/poppler-windows/releases)，下载最新版本的 ZIP 压缩包。
2. 将 ZIP 解压到一个固定位置，例如 `C:\Tools\poppler`。
3. 在解压文件夹中找到同时包含 `pdfinfo.exe` 和 `pdftoppm.exe` 的 `bin` 文件夹。常见路径类似 `C:\Tools\poppler\Library\bin`，具体以你下载的压缩包结构为准。
4. 复制这个 `bin` 文件夹的完整路径。在 Windows 搜索“编辑系统环境变量”，打开“环境变量”，在用户变量中选中 `Path`，点击“编辑 → 新建”，粘贴路径并确认所有窗口。
5. 关闭并重新打开 VS Code。在 PowerShell 中分别运行：

```powershell
pdfinfo -v
pdftoppm -h
```

两条命令都能显示版本或帮助信息就可以继续。

## 4. 安装 LaTeX

1. 从 [MiKTeX 官方网站](https://miktex.org/download)下载并安装 MiKTeX。
2. 安装过程中建议选择允许 MiKTeX 自动安装缺少的宏包。
3. 安装完成后关闭并重新打开 VS Code。
4. 验证命令：

```powershell
pdflatex --version
```

如果提示找不到命令，请打开 MiKTeX Console 完成更新，再重启终端。自动编译时如果 MiKTeX 询问是否安装缺失宏包，选择允许。

## 5. 创建 Python 环境并安装绘图依赖

在 VS Code 仓库根目录的 PowerShell 终端中逐行运行。若 `.venv` 文件夹尚不存在，先创建环境；若已经存在，跳过创建这一步：

```powershell
py -m venv .venv
```

```powershell
.\.venv\Scripts\Activate.ps1
```

如果 PowerShell 阻止激活脚本，仅为当前终端临时放行，然后重试激活：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

安装 Matplotlib：

```powershell
python -m pip install --upgrade pip
python -m pip install matplotlib
```

看到安装成功后，以后每次新开终端都先运行：

```powershell
.\.venv\Scripts\Activate.ps1
```

## 6. 设置 Kimi API Key

1. 在 [Kimi 开放平台](https://platform.moonshot.cn/)登录或注册。
2. 在控制台创建 API Key，确认账户有可用额度，并选择支持图片输入的模型。
3. 不要把 Key 放进代码、README、PDF 或聊天记录。在 PowerShell 中设置当前终端变量：

```powershell
$env:MOONSHOT_API_KEY = '在这里粘贴你自己的API Key'
```

这会在当前终端关闭前有效。检查是否已设置，但不要打印 Key 内容：

```powershell
if ($env:MOONSHOT_API_KEY) { "API key is set" } else { "API key is missing" }
```

## 7. 运行转换

把下面命令里的姓名、学号和作业编号替换成自己的信息。命令必须在仓库根目录运行。输入路径直接指向笔记文件夹，不用填写 PDF 文件名，也不用重命名：

```powershell
py "手写pdf转换latex脚本工具/handwriting_to_latex.py" "你的手写笔记请放在这个文件夹" --api-url "https://api.moonshot.cn/v1/chat/completions" --model "kimi-k3" --api-key-env MOONSHOT_API_KEY --author "StudentName" --student-id "000000" --assignment 1 --compile
```

图形识别默认开启，不需要额外写开关。若要关闭，可在命令末尾加 `--no-draw-diagrams`。`--compile` 会生成 PDF 预览；若暂时不想编译，删掉这个参数即可。

姓名请使用英文字母或拼音，避免当前模板的 `pdflatex` 因中文姓名报 Unicode 错误。命令运行期间请不要关闭终端；完成时会显示输出目录。

## 8. 找到结果并校对

输出默认在输入 PDF 旁边、以原 PDF 文件名命名的 `_latex` 文件夹中。例如原文件叫 `GroupTheoryNotes.pdf`，输出目录就是 `GroupTheoryNotes_latex`。重点检查：

- `transcription.tex`：可编辑 LaTeX 草稿。
- `transcription.pdf`：编译后的预览（使用了 `--compile` 才会生成）。
- `transcription_body.tex`：模型识别出的正文。
- `figures`：识别并绘制出的图形 PDF。

打开 `transcription.pdf` 和原手写 PDF 对照检查。模型可能误认公式、点线关系或标签，确认无误后再提交。

## 常见问题

- **`pdfinfo` 或 `pdftoppm` 找不到**：检查 Poppler 的 `bin` 路径是否加进用户 `Path`，然后彻底重开 VS Code。
- **`pdflatex` 找不到**：重开 VS Code；检查 MiKTeX 是否安装完成并在 MiKTeX Console 更新。
- **提示缺少 Matplotlib**：先激活 `.venv`，再运行 `python -m pip install matplotlib`。
- **API 返回 HTTP 401/400**：检查 Key、模型名、接口地址、图片输入权限和账户额度；不要把 Key 发给别人。
- **LaTeX 编译报错**：打开 `transcription.tex`，从编译日志第一条 `!` 错误开始检查；通常需要修正模型生成的 LaTeX。
- **输入 PDF 含有很多页或请求超时**：可在转换命令中加 `--dpi 100` 降低发给模型的图片分辨率，或将 PDF 拆成较短的部分。
