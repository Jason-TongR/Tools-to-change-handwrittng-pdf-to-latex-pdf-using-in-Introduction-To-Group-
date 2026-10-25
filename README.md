# 手写群论作业转 LaTeX

这个工具会把手写作业 PDF 发给 Kimi 视觉模型识别，生成可编辑的 LaTeX 草稿，并可选择编译成 PDF。图形识别默认开启，会将模型识别出的点、线、箭头、圆和文字绘制成矢量图插入 LaTeX。

## 先选择你的操作系统（点击下面的中文即可）

- [Windows 操作指南](README-Windows.md)
- [macOS 操作指南](README-macOS.md)
- [Linux 操作指南](README-Linux.md)

请进入与你电脑系统对应的指南，按顺序完成安装、设置 API Key 和运行步骤。若使用 VS Code 集成终端，请选择对应操作系统的终端类型（Windows 通常为 PowerShell，macOS/Linux 通常为 bash 或 zsh）。

## 开始前：放入手写 PDF

先把你要转换的手写笔记 PDF 复制到仓库里的 `你的手写笔记请放在这个文件夹` 文件夹中。它与根目录的 `README.md`、`Uri Onn作业模板` 和 `手写pdf转换latex脚本工具` 文件夹在同一层。无需把 PDF 改名；程序会自动读取该文件夹中唯一的 PDF。若放入多个 PDF，程序会说明文件不唯一；请先移走其他 PDF，或在命令中直接指定目标文件。

## 开始前要知道

- 你需要 Python、Poppler、LaTeX，以及一个有可用额度且支持图片输入的 Kimi API Key。
- 图形绘制默认开启，需要 Matplotlib；各系统指南会带你安装。
- 识别结果是草稿。请对照原 PDF 检查公式、证明、题号、图形关系和标签，再决定是否提交。
- 手写 PDF 会上传到你配置的模型服务商。请先确认你接受服务商的数据处理方式和 API 费用。

## 其他帮助

- [老师模板](Uri%20Onn作业模板/TemplateHW.tex)
- [离线测试命令](手写pdf转换latex脚本工具/README.md)
