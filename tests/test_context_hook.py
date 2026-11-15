import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_SCRIPT = REPO_ROOT / "agy-context-hook"
INSTALL_SCRIPT = REPO_ROOT / "install.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ContextHookCrossPlatformTests(unittest.TestCase):
    def test_cp1252_hook_mode_with_utf8_stdin(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            transcript = Path(tmpdir) / "transcript.jsonl"
            steps = [
                {"type": "USER_INPUT", "content": "Hello 🌍"},
                {
                    "type": "PLANNER_RESPONSE",
                    "input_tokens": 2000,
                    "cache_read_tokens": 18000,
                    "output_tokens": 300,
                    "content": "Response ✅",
                },
            ]
            transcript.write_text(
                "\n".join(json.dumps(s, ensure_ascii=False) for s in steps) + "\n",
                encoding="utf-8",
            )

            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "cp1252"
            payload = json.dumps(
                {
                    "transcriptPath": str(transcript),
                    "lastUserInput": "Hello 🌍",
                },
                ensure_ascii=False,
            ).encode("utf-8")

            proc = subprocess.run(
                [sys.executable, str(HOOK_SCRIPT), "pre"],
                input=payload,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", errors="replace"))
            out = proc.stdout.decode("ascii")
            parsed = json.loads(out)
            self.assertIn("injectSteps", parsed)
            msg = parsed["injectSteps"][0]["ephemeralMessage"]
            self.assertIn("20.0k / 1M", msg)
            self.assertIn("90% cached", msg)

    def test_cp1252_panel_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            transcript = Path(tmpdir) / "transcript.jsonl"
            transcript.write_text(
                json.dumps(
                    {
                        "type": "PLANNER_RESPONSE",
                        "input_tokens": 5000,
                        "cache_read_tokens": 5000,
                        "output_tokens": 100,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "cp1252"
            proc = subprocess.run(
                [sys.executable, str(HOOK_SCRIPT), "--panel", "--transcript", str(transcript)],
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", errors="replace"))
            out = proc.stdout.decode("utf-8")
            self.assertIn("Antigravity Context Usage (/context)", out)
            self.assertIn("10.0k / 1M", out)

    def test_context_slash_command_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            transcript = Path(tmpdir) / "transcript.jsonl"
            steps = [
                {"type": "USER_INPUT", "content": "<USER_REQUEST>\n/context\n</USER_REQUEST>"},
                {
                    "type": "PLANNER_RESPONSE",
                    "input_tokens": 1000,
                    "cache_read_tokens": 9000,
                    "output_tokens": 50,
                },
            ]
            transcript.write_text("\n".join(json.dumps(s) for s in steps) + "\n", encoding="utf-8")
            payload = json.dumps({"transcriptPath": str(transcript)}).encode("utf-8")
            proc = subprocess.run(
                [sys.executable, str(HOOK_SCRIPT), "pre"],
                input=payload,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0)
            parsed = json.loads(proc.stdout.decode("utf-8"))
            msg = parsed["injectSteps"][0]["ephemeralMessage"]
            self.assertIn("The user invoked `/context`", msg)

    def test_normal_turn_avoids_wrapper_tags_and_instructs_subagents_to_ignore(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            transcript = Path(tmpdir) / "transcript.jsonl"
            steps = [
                {"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "Fix bug"},
                {
                    "type": "PLANNER_RESPONSE",
                    "input_tokens": 1000,
                    "cache_read_tokens": 9000,
                    "output_tokens": 50,
                },
            ]
            transcript.write_text("\n".join(json.dumps(s) for s in steps) + "\n", encoding="utf-8")
            payload = json.dumps({"transcriptPath": str(transcript)}).encode("utf-8")
            proc = subprocess.run(
                [sys.executable, str(HOOK_SCRIPT), "pre"],
                input=payload,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0)
            parsed = json.loads(proc.stdout.decode("utf-8"))
            msg = parsed["injectSteps"][0]["ephemeralMessage"]
            self.assertNotIn("<context_status_badge>", msg)
            self.assertIn("If you are a subagent", msg)
            self.assertIn("10.0k / 1M", msg)

    def test_subagent_detection_skips_injection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            transcript = Path(tmpdir) / "transcript.jsonl"
            transcript.write_text(
                json.dumps({"type": "USER_INPUT", "source": "SUBAGENT", "content": "Research X"}) + "\n",
                encoding="utf-8",
            )
            for extra in (
                {"transcriptPath": str(transcript)},
                {"isSubagent": True},
                {"parentConversationId": "parent-123"},
            ):
                payload = json.dumps(extra).encode("utf-8")
                proc = subprocess.run(
                    [sys.executable, str(HOOK_SCRIPT), "pre"],
                    input=payload,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(proc.returncode, 0)
                parsed = json.loads(proc.stdout.decode("utf-8"))
                self.assertEqual(parsed, {})

    def test_installer_preserves_existing_hooks_and_uninstalls(self) -> None:
        install_mod = load_module("install", INSTALL_SCRIPT)
        with tempfile.TemporaryDirectory() as tmpdir:
            gemini_dir = Path(tmpdir) / ".gemini"
            config_dir = gemini_dir / "config"
            config_dir.mkdir(parents=True)
            hooks_json = config_dir / "hooks.json"
            hooks_json.write_text(
                json.dumps({"existing-hook": {"Stop": [{"type": "command", "command": "echo ok"}]}}),
                encoding="utf-8",
            )

            rc = install_mod.install(gemini_dir=gemini_dir, dry_run=False)
            self.assertEqual(rc, 0)

            self.assertTrue((gemini_dir / "hooks" / "agy-context-hook.py").is_file())
            self.assertTrue((config_dir / "skills" / "context" / "SKILL.md").is_file())

            data = json.loads(hooks_json.read_text(encoding="utf-8"))
            self.assertIn("existing-hook", data)
            self.assertIn("context-status-hook", data)
            cmd = data["context-status-hook"]["PreInvocation"][0]["command"]
            self.assertIn("agy-context-hook.py", cmd)
            self.assertNotIn("~", cmd)

            rc_un = install_mod.uninstall(gemini_dir=gemini_dir, dry_run=False)
            self.assertEqual(rc_un, 0)
            self.assertFalse((gemini_dir / "hooks" / "agy-context-hook.py").exists())
            self.assertFalse((config_dir / "skills" / "context" / "SKILL.md").exists())
            data_after = json.loads(hooks_json.read_text(encoding="utf-8"))
            self.assertIn("existing-hook", data_after)
            self.assertNotIn("context-status-hook", data_after)

    def test_windows_command_formatting(self) -> None:
        from pathlib import PureWindowsPath

        install_mod = load_module("install", INSTALL_SCRIPT)
        with mock.patch.object(install_mod.os, "name", "nt"):
            cmd = install_mod.build_hook_command(
                r"C:\Program Files\Python312\python.exe",
                PureWindowsPath(r"C:\Users\Alice Smith\.gemini\hooks\agy-context-hook.py"),
            )
        self.assertTrue(cmd.startswith('call "C:\\Program Files\\Python312\\python.exe"'))
        self.assertIn('"C:\\Program Files\\Python312\\python.exe"', cmd)
        self.assertTrue(cmd.endswith("pre || echo {}"))
        self.assertNotIn("~", cmd)

    @unittest.skipUnless(os.name == "nt", "Windows cmd.exe /c quoting test")
    def test_windows_cmd_c_spaced_paths_execution(self) -> None:
        install_mod = load_module("install", INSTALL_SCRIPT)
        with tempfile.TemporaryDirectory(prefix="agy space ") as tmpdir:
            root = Path(tmpdir)
            py_dir = root / "Program Files Python"
            py_dir.mkdir()
            py_wrapper = py_dir / "python wrap.cmd"
            py_wrapper.write_text(f'@"{sys.executable}" %*\r\n', encoding="utf-8")

            hook_dir = root / "Alice Smith" / ".gemini" / "hooks"
            hook_dir.mkdir(parents=True)
            hook_copy = hook_dir / "agy context hook.py"
            hook_copy.write_text(HOOK_SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")

            transcript = root / "transcript.jsonl"
            transcript.write_text(
                json.dumps(
                    {
                        "type": "PLANNER_RESPONSE",
                        "input_tokens": 1200,
                        "cache_read_tokens": 8800,
                        "output_tokens": 40,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            cmd = install_mod.build_hook_command(str(py_wrapper), hook_copy)
            payload = json.dumps({"transcriptPath": str(transcript)}).encode("utf-8")
            proc = subprocess.run(
                "cmd.exe /c " + cmd,
                input=payload,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", errors="replace"))
            self.assertEqual(proc.stderr.decode("utf-8", errors="replace").strip(), "")
            parsed = json.loads(proc.stdout.decode("ascii"))
            self.assertIn("injectSteps", parsed)
            self.assertIn("10.0k / 1M", parsed["injectSteps"][0]["ephemeralMessage"])


if __name__ == "__main__":
    unittest.main()
