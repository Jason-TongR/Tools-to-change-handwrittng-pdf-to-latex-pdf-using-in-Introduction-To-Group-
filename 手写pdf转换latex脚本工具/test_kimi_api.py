from __future__ import annotations

import importlib.util
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).with_name("handwriting_to_latex.py")
SPEC = importlib.util.spec_from_file_location("handwriting_to_latex", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
converter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(converter)


class KimiApiTests(unittest.TestCase):
    def test_resolve_pdf_input_accepts_folder_with_one_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            pdf_path = folder / "笔记原始文件名.PDF"
            pdf_path.write_bytes(b"pdf")
            (folder / "ignore.txt").write_text("not a PDF", encoding="utf-8")

            self.assertEqual(converter.resolve_pdf_input(folder), pdf_path)

    def test_resolve_pdf_input_rejects_folder_with_multiple_pdfs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "first.pdf").write_bytes(b"pdf")
            (folder / "second.pdf").write_bytes(b"pdf")

            with self.assertRaisesRegex(ValueError, "More than one PDF"):
                converter.resolve_pdf_input(folder)

    def test_diagram_rendering_is_enabled_by_default_and_can_be_disabled(self) -> None:
        with patch("sys.argv", ["handwriting_to_latex.py", "input.pdf"]):
            self.assertTrue(converter.parse_args().draw_diagrams)
        with patch(
            "sys.argv", ["handwriting_to_latex.py", "input.pdf", "--no-draw-diagrams"]
        ):
            self.assertFalse(converter.parse_args().draw_diagrams)

    def test_default_template_uses_current_repository_location(self) -> None:
        template = converter.default_template_path()
        self.assertEqual(template.name, "TemplateHW.tex")
        self.assertEqual(template.parent.name, "Uri Onn作业模板")
        self.assertTrue(template.is_file())

    def start_server(self, handler_type: type[BaseHTTPRequestHandler]):
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler_type)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 2)
        self.addCleanup(server.shutdown)
        return server

    def test_kimi_k3_uses_documented_request_fields(self) -> None:
        captured: dict[str, object] = {}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                captured["auth"] = self.headers.get("Authorization")
                captured["payload"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                data = json.dumps(
                    {"choices": [{"message": {"content": r"\\begin{ej}x\\end{ej}"}}]}
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, format: str, *args: object) -> None:
                return

        server = self.start_server(Handler)
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "page.jpg"
            image.write_bytes(b"fake-jpeg")
            result = converter.transcribe_images(
                [image],
                api_url=f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
                model="kimi-k3",
                api_key="mock-secret",
                timeout=5,
                max_tokens=1234,
                reasoning_effort="low",
            )

        payload = captured["payload"]
        self.assertEqual(captured["auth"], "Bearer mock-secret")
        self.assertEqual(payload["model"], "kimi-k3")
        self.assertEqual(payload["max_completion_tokens"], 1234)
        self.assertEqual(payload["reasoning_effort"], "low")
        self.assertNotIn("temperature", payload)
        self.assertNotIn("max_tokens", payload)
        image_part = payload["messages"][1]["content"][1]
        self.assertEqual(set(image_part["image_url"]), {"url"})
        self.assertTrue(image_part["image_url"]["url"].startswith("data:image/jpeg;base64,"))
        self.assertEqual(result, r"\\begin{ej}x\\end{ej}")

    def test_http_error_detail_is_reported_without_api_key(self) -> None:
        api_key = "secret-value-do-not-print"

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                self.rfile.read(int(self.headers["Content-Length"]))
                data = json.dumps(
                    {"error": {"message": f"unsupported field temperature for {api_key}"}}
                ).encode()
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, format: str, *args: object) -> None:
                return

        server = self.start_server(Handler)
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "page.jpg"
            image.write_bytes(b"fake-jpeg")
            with self.assertRaisesRegex(RuntimeError, "unsupported field temperature") as caught:
                converter.transcribe_images(
                    [image],
                    api_url=f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
                    model="kimi-k3",
                    api_key=api_key,
                    timeout=5,
                    max_tokens=1234,
                )
        self.assertIn("HTTP 400", str(caught.exception))
        self.assertNotIn(api_key, str(caught.exception))

    def test_render_diagrams_replaces_marker_and_writes_pdf(self) -> None:
        try:
            import matplotlib  # noqa: F401
        except ImportError:
            self.skipTest("Matplotlib is not installed")

        body = r"""Before \PYFIGURE{figure1} after
%% PYFIGURES_BEGIN
{"figures":[{"id":"figure1","xlim":[-2,2],"ylim":[-2,2],"elements":[{"type":"point","at":[0,0],"label":"e"},{"type":"arrow","from":[0,0],"to":[1,1],"label":"a"},{"type":"circle","center":[0,0],"radius":1}]}]}
%% PYFIGURES_END"""
        with tempfile.TemporaryDirectory() as directory:
            converted, files = converter.render_diagrams(body, Path(directory))
            self.assertIn(r"\includegraphics[width=0.8\linewidth]{figures/figure1.pdf}", converted)
            self.assertNotIn("PYFIGURES_", converted)
            self.assertEqual(files, ["figures/figure1.pdf"])
            self.assertTrue((Path(directory) / files[0]).is_file())

    def test_render_diagrams_rejects_unmatched_placeholders(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "without a PYFIGURES data block"):
            converter.render_diagrams(r"\PYFIGURE{figure1}", Path("unused"))

    def test_render_diagrams_rejects_non_finite_coordinates(self) -> None:
        body = r"""\PYFIGURE{figure1}
%% PYFIGURES_BEGIN
{"figures":[{"id":"figure1","xlim":[-2,2],"ylim":[-2,2],"elements":[{"type":"point","at":[NaN,0]}]}]}
%% PYFIGURES_END"""
        with self.assertRaisesRegex(RuntimeError, "not valid JSON"):
            converter.render_diagrams(body, Path("unused"))


if __name__ == "__main__":
    unittest.main()
