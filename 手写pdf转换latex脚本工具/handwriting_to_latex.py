#!/usr/bin/env python3
"""Transcribe handwritten PDF pages with an OpenAI-compatible vision API."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_PROMPT = """Transcribe the handwritten homework in the attached page images into LaTeX.
Return ONLY the content that belongs between \\begin{document} and \\end{document}; do not return a preamble, markdown fences, or explanations.
Use the provided group-theory homework template conventions: each exercise uses \\begin{ej}...\\end{ej}, and handwritten solutions use \\begin{sol}...\\end{sol}. Preserve the order, wording, notation, proof steps, crossed-out or annotated meaning where legible, and visible colored notes. Do not correct mathematics, silently complete missing arguments, or invent unreadable text. Represent genuinely unclear handwriting as \\textcolor{red}{[unclear: short visual description]}. Keep all LaTeX syntactically balanced. Use only standard LaTeX and the macros defined by the template. For colors use xcolor names such as red, green, orange, or blue. The source images are in page order."""


def run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def find_tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(f"Required command not found: {name}")
    return path


def default_template_path() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent / "Jason的群论作业" / "TemplateHW.tex",
        Path(__file__).resolve().parent / "TemplateHW.tex",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError("Could not find TemplateHW.tex; pass --template explicitly")


def render_pages(pdf_path: Path, image_dir: Path, dpi: int, pdftoppm: str) -> list[Path]:
    image_dir.mkdir(parents=True, exist_ok=True)
    prefix = image_dir / "page"
    run(
        [
            pdftoppm,
            "-jpeg",
            "-jpegopt",
            "quality=88,progressive=y",
            "-r",
            str(dpi),
            str(pdf_path),
            str(prefix),
        ]
    )
    pages = sorted(image_dir.glob("page-*.jpg"))
    if not pages:
        raise RuntimeError("PDF rendering produced no page images")
    return pages


def response_text(payload: dict[str, Any]) -> str:
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("Vision API response did not contain choices[0].message.content") from error

    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = "\n".join(
            item["text"]
            for item in content
            if isinstance(item, dict) and isinstance(item.get("text"), str)
        )
    else:
        raise RuntimeError("Vision API returned an unsupported message content format")

    text = text.strip()
    fenced = re.fullmatch(r"```(?:latex|tex)?\s*\n?(.*?)\n?```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()

    document_body = re.search(
        r"\\begin\s*\{document\}(.*?)\\end\s*\{document\}", text, re.DOTALL
    )
    if document_body:
        text = document_body.group(1).strip()

    if not text:
        raise RuntimeError("Vision API returned an empty transcription")
    if r"\begin{document}" in text or r"\end{document}" in text:
        raise RuntimeError("Could not isolate the transcription body from the API response")
    return text


def transcribe_images(
    images: list[Path],
    *,
    api_url: str,
    model: str,
    api_key: str,
    timeout: int,
    max_tokens: int,
    prompt: str = DEFAULT_PROMPT,
) -> str:
    image_parts = []
    for page_number, image_path in enumerate(images, start=1):
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        image_parts.append(
            {
                "type": "text",
                "text": f"Source page {page_number}:",
            }
        )
        image_parts.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{encoded}", "detail": "high"},
            }
        )

    request_body = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": image_parts},
        ],
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    request = urllib.request.Request(
        api_url,
        data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        # Do not print provider response bodies; they may echo request data.
        raise RuntimeError(f"Vision API returned HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not connect to the vision API: {error.reason}") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("Vision API response was not valid UTF-8 JSON") from error

    if not isinstance(response_payload, dict):
        raise RuntimeError("Vision API response must be a JSON object")
    return response_text(response_payload)


def build_template_document(
    template_path: Path,
    output_path: Path,
    body: str,
    *,
    author: str | None,
    student_id: str | None,
    assignment: str | None,
) -> None:
    template = template_path.read_text(encoding="latin-1")
    parts = re.split(r"\\begin\s*\{document\}", template, maxsplit=1)
    if len(parts) != 2:
        raise RuntimeError("Template is missing \\begin{document}")
    preamble, document_tail = parts
    tail = re.split(r"\\end\s*\{document\}", document_tail, maxsplit=1)
    if len(tail) != 2:
        raise RuntimeError("Template is missing \\end{document}")

    preamble = preamble.replace(r"\usepackage[latin1]{inputenc}", r"\usepackage[utf8]{inputenc}")
    solution_environment = re.compile(r"\\newenvironment\{sol\}\{.*?\n\}", re.DOTALL)
    replacement = r"""\newenvironment{sol}{
    \par\medskip
    \def\FrameCommand##1{\fcolorbox{black}{gray!20}{##1}}%
    \MakeFramed{\advance\hsize-\width \FrameRestore}%
    \noindent\textbf{Answer:} \ignorespaces
}{
    \endMakeFramed
    \par\medskip
}
"""
    preamble, substitutions = solution_environment.subn(lambda _: replacement, preamble, count=1)
    if substitutions != 1:
        raise RuntimeError("Could not safely replace the template's solution-box definition")
    if r"\usepackage{framed}" not in preamble:
        preamble = preamble.replace(r"\usepackage{calc}", r"\usepackage{calc}" + "\n" + r"\usepackage{framed}")

    document_body = tail[0]
    center_match = re.search(r"\\begin\{center\}.*?\\end\{center\}", document_body, re.DOTALL)
    if center_match is None:
        raise RuntimeError("Template is missing the author and student-ID block")
    author_block = center_match.group(0)
    if author is not None:
        author_block = re.sub(r"Autor:\s*xxx\s*xxxxxx", lambda _: f"Autor: {author}", author_block)
    if student_id is not None:
        author_block = re.sub(r"ID:\s*xxxxxx", lambda _: f"ID: {student_id}", author_block)
    if assignment is not None:
        preamble = re.sub(
            r"Homework Assignment\s+x", lambda _: f"Homework Assignment {assignment}", preamble
        )

    output_path.write_text(
        preamble
        + r"\begin{document}"
        + "\n    \\thispagestyle{fancy}\n\n"
        + author_block
        + "\n\n"
        + body
        + "\n\\end{document}\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe handwritten PDF pages with a user-selected vision model into the group-theory homework template."
    )
    parser.add_argument("pdf", type=Path, help="Input handwritten PDF")
    parser.add_argument("--api-url", help="Full OpenAI-compatible Chat Completions endpoint URL")
    parser.add_argument("--model", help="Vision model identifier accepted by your API")
    parser.add_argument(
        "--api-key-env",
        default="VISION_API_KEY",
        help="Environment variable holding the API key (default: VISION_API_KEY)",
    )
    parser.add_argument(
        "--template",
        type=Path,
        help="Teacher's TemplateHW.tex (auto-detected from Jason的群论作业/ by default)",
    )
    parser.add_argument("-o", "--output-dir", type=Path, help="Output folder (default: <PDF name>_latex)")
    parser.add_argument("--mode", choices=("both", "visual", "faithful"), default="both")
    parser.add_argument("--author", help="Replace the template author placeholder")
    parser.add_argument("--student-id", help="Replace the template ID placeholder")
    parser.add_argument("--assignment", help="Replace the assignment number in the header")
    parser.add_argument("--dpi", type=int, default=160, help="Page image resolution, 72-300 DPI (default: 160)")
    parser.add_argument("--timeout", type=int, default=240, help="API request timeout in seconds (default: 240)")
    parser.add_argument("--max-tokens", type=int, default=16000, help="Maximum API response tokens")
    parser.add_argument("--prompt-file", type=Path, help="Optional UTF-8 file with custom transcription instructions")
    parser.add_argument("--compile", action="store_true", help="Compile generated .tex files using pdflatex")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pdf_path = args.pdf.expanduser().resolve()
    if not pdf_path.is_file() or pdf_path.suffix.lower() != ".pdf":
        print(f"Error: input is not an existing PDF: {pdf_path}", file=sys.stderr)
        return 2
    if not 72 <= args.dpi <= 300:
        print("Error: --dpi must be between 72 and 300", file=sys.stderr)
        return 2
    if args.timeout < 1 or args.max_tokens < 1:
        print("Error: --timeout and --max-tokens must be positive", file=sys.stderr)
        return 2

    api_key: str | None = None
    if args.mode in ("both", "visual"):
        if not args.api_url or not args.model:
            print("Error: --api-url and --model are required for visual transcription", file=sys.stderr)
            return 2
        api_key = os.environ.get(args.api_key_env)
        if not api_key:
            print(f"Error: set the API key in environment variable {args.api_key_env}", file=sys.stderr)
            return 2

    output_dir = (args.output_dir or pdf_path.with_name(f"{pdf_path.stem}_latex")).expanduser().resolve()
    template_path = args.template.expanduser().resolve() if args.template else None
    if args.mode in ("both", "visual"):
        try:
            template_path = template_path or default_template_path()
        except RuntimeError as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1
        if not template_path.is_file():
            print(f"Error: template file does not exist: {template_path}", file=sys.stderr)
            return 2

    output_dir.mkdir(parents=True, exist_ok=True)
    source_copy = output_dir / "source.pdf"
    shutil.copy2(pdf_path, source_copy)
    manifest: dict[str, Any] = {
        "source_pdf": source_copy.name,
        "mode": args.mode,
        "model": args.model if args.mode in ("both", "visual") else None,
        "api_key_value_saved": False,
        "page_count": None,
        "generated_files": [],
    }

    try:
        if args.mode in ("both", "faithful"):
            faithful_tex = output_dir / "faithful.tex"
            faithful_tex.write_text(
                "\\documentclass{article}\n"
                "\\usepackage[final]{pdfpages}\n"
                "\\begin{document}\n"
                "\\includepdf[pages=-,fitpaper=true]{source.pdf}\n"
                "\\end{document}\n",
                encoding="utf-8",
            )
            manifest["generated_files"].append(faithful_tex.name)

        if args.mode in ("both", "visual"):
            pdfinfo = find_tool("pdfinfo")
            metadata = run([pdfinfo, str(source_copy)]).stdout
            page_match = re.search(r"^Pages:\s+(\d+)\s*$", metadata, re.MULTILINE)
            if page_match is None:
                raise RuntimeError("Could not determine the source PDF page count")
            page_count = int(page_match.group(1))
            manifest["page_count"] = page_count

            page_dir = output_dir / "pages"
            page_dir.mkdir(exist_ok=True)
            for stale_image in page_dir.glob("page-*.jpg"):
                stale_image.unlink()
            pages = render_pages(source_copy, page_dir, args.dpi, find_tool("pdftoppm"))
            if len(pages) != page_count:
                raise RuntimeError(f"Expected {page_count} page images, rendered {len(pages)}")

            prompt = args.prompt_file.read_text(encoding="utf-8") if args.prompt_file else DEFAULT_PROMPT
            body = transcribe_images(
                pages,
                api_url=args.api_url,
                model=args.model,
                api_key=api_key,
                timeout=args.timeout,
                max_tokens=args.max_tokens,
                prompt=prompt,
            )
            tex_path = output_dir / "transcription.tex"
            build_template_document(
                template_path,
                tex_path,
                body,
                author=args.author,
                student_id=args.student_id,
                assignment=args.assignment,
            )
            manifest["generated_files"].append(tex_path.name)
            (output_dir / "transcription_body.tex").write_text(body + "\n", encoding="utf-8")
            manifest["generated_files"].append("transcription_body.tex")

        if args.compile:
            pdflatex = find_tool("pdflatex")
            for tex_name in manifest["generated_files"]:
                if tex_name.endswith(".tex") and tex_name != "transcription_body.tex":
                    run([pdflatex, "-interaction=nonstopmode", "-halt-on-error", tex_name], cwd=output_dir)
                    manifest["generated_files"].append(Path(tex_name).with_suffix(".pdf").name)

        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Created output in: {output_dir}")
    for file_name in manifest["generated_files"]:
        print(f"  {file_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
