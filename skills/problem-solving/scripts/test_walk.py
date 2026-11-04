"""Regression checks for the shared investigation and its two subscription transports."""
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import walk


def native_reply(text="답", observations=(), returncode=0):
    def invoke(args, prompt, cwd, events_file, run, env=None):
        events = [{"type": "thread.started", "thread_id": "native-session"}]
        events += [{"type": "item.completed", "item": item} for item in observations]
        events += [{"type": "item.completed", "item": {"type": "agent_message", "text": text}}, {"type": "turn.completed"}]
        payloads = [{"type": "turn_context", "payload": {}}]
        for number, item in enumerate(observations):
            payloads += [{"type": "response_item", "payload": {"type": "custom_tool_call", "call_id": str(number), "name": "exec", "input": item["command"]}},
                         {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": str(number), "output": item["aggregated_output"]}}]
        (Path(cwd).parent / "native-session.jsonl").write_text("\n".join(json.dumps(item) for item in payloads), encoding="utf-8")
        events_file.write_text("\n".join(json.dumps(item) for item in events) + "\n", encoding="utf-8")
        return returncode, "native error" if returncode else ""
    return invoke


def streamed(text, returncode=0):
    """A mocked investigator turn whose output lines are `text`."""
    def invoke(args, prompt, cwd, events, run, env=None):
        events.write_text(text, encoding="utf-8")
        return returncode, ""
    return invoke


def reply(name, value, evidence="기록이 그렇다", checked="기록을 읽음"):
    """An investigator's JSON reply with `name` as its main field."""
    return json.dumps({name: value, "evidence": evidence, "checked": checked}, ensure_ascii=False)


def said(value, grounds=True):
    """What the mocked Jev says about one answer: its judgment, and whether the answer gave its grounds."""
    return {"said": value, "grounds": grounds}


class WalkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.patch = patch.object(walk, "RUNS", self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        sessions = patch.object(walk, "SESSIONS", self.root)
        sessions.start()
        self.addCleanup(sessions.stop)
        self.settings = self.root / "settings.env"
        self.settings.write_text("INVESTIGATOR_CLAUDE_MODEL=test-claude-model\nINVESTIGATOR_CODEX_MODEL=test-codex-model\n"
                                 "TYPESAFE_API_KEY=test-key\n", encoding="utf-8")
        for target in (patch.object(walk, "SETTINGS", self.settings), patch.dict(walk.os.environ),
                       patch.object(walk.shutil, "which", side_effect=lambda name: f"/bin/{name}")):
            target.start()
            self.addCleanup(target.stop)
        for name in ("INVESTIGATOR_CLAUDE_MODEL", "INVESTIGATOR_CODEX_MODEL", "TYPESAFE_API_KEY", "JEV_MODEL"):
            walk.os.environ.pop(name, None)

    def run_state(self, app="codex"):
        run = {"id": "test", "app": app, "session": "session", "asked": False,
               "input": {"현상": "입력 후 결과가 없음", "요청": "확인", "대상": "fixture"}, "log": []}
        (self.root / run["id"]).mkdir(exist_ok=True)
        return run

    def test_settings_read_from_file_and_environment_wins(self):
        self.settings.write_text('OTHER_KEY=unrelated\nTYPESAFE_API_KEY="test-canonical"\n', encoding="utf-8")
        self.assertEqual(walk.jev_key(), "test-canonical")
        with patch.dict(walk.os.environ, {"TYPESAFE_API_KEY": "from-env"}):
            self.assertEqual(walk.jev_key(), "from-env")
        self.assertEqual(walk.setting("JEV_MODEL", "jev-latest"), "jev-latest")

    def test_empty_or_missing_setting_names_where_to_set_it(self):
        for text in ('TYPESAFE_API_KEY=""\n', "TYPESAFE_API_KEY=  \n", "OTHER_KEY=unrelated\n"):
            with self.subTest(text=text):
                self.settings.write_text(text, encoding="utf-8")
                with self.assertRaisesRegex(KeyError, "TYPESAFE_API_KEY.*settings.env"):
                    walk.jev_key()
        self.settings.unlink()
        with self.assertRaisesRegex(KeyError, "INVESTIGATOR_CODEX_MODEL"):
            walk.setting("INVESTIGATOR_CODEX_MODEL")

    def test_unset_key_stops_before_the_first_question(self):
        with patch.object(walk, "ask") as ask, self.assertRaises(SystemExit) as stop, \
                patch.object(walk.sys, "stdin", io.StringIO(json.dumps({"현상": "x", "요청": "y", "대상": "z"}))):
            self.settings.write_text("INVESTIGATOR_CLAUDE_MODEL=m\n", encoding="utf-8")
            walk.start("claude")
        ask.assert_not_called()
        self.assertIn("TYPESAFE_API_KEY", str(stop.exception.code))
        self.assertEqual(list(self.root.glob("*.json")), [])

    def test_unset_model_leaves_the_cli_default(self):
        self.settings.write_text("TYPESAFE_API_KEY=k\n", encoding="utf-8")
        run = self.run_state("claude")
        events = [{"type": "result", "result": "답", "is_error": False}]
        with patch.object(walk, "stream", side_effect=streamed(json.dumps(events[0]))) as call:
            walk.ask(run, "질문")
        self.assertNotIn("--model", call.call_args.args[0])
        with patch.object(walk, "stream", side_effect=native_reply("답")) as call:
            walk.ask(self.run_state("codex"), "질문")
        self.assertNotIn("-m", call.call_args.args[0])

    def start(self, app, answers, judgments):
        """walk.start with the investigator's answers (or an exception) and Jev's judgments given in order."""
        with patch.object(walk, "jev", side_effect=judgments), \
                patch.object(walk, "claude", side_effect=answers) as claude, \
                patch.object(walk.sys, "stdin", io.StringIO(json.dumps({"현상": "입력 후 결과가 없음", "요청": "확인", "대상": "fixture"}))), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            walk.start(app)
        return output.getvalue(), claude

    def test_start_and_recheck_share_the_same_workflow(self):
        answers = [reply("phenomenon", "입력 후 결과가 없음"), reply("cause", "조건 누락"), reply("cause", "앞선 원인 없음"),
                   "흐름 설명", "조건을 반영", reply("result", "다시 해 보니 결과가 나옴")]
        for app in ("claude", "codex"):
            with self.subTest(app=app), patch.object(walk, "jev", side_effect=[said(True), said("cause"), said("none"), said("gone")]), \
                    patch.object(walk, "claude", side_effect=answers) as claude, \
                    patch.object(walk, "codex", side_effect=answers) as codex, \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                with patch.object(walk.sys, "stdin", io.StringIO(json.dumps({"현상": "입력 후 결과가 없음", "요청": "확인", "대상": "fixture"}))):
                    walk.start(app)
                run = json.loads(next(p for p in self.root.glob("*.json") if json.loads(p.read_text(encoding="utf-8"))["app"] == app).read_text(encoding="utf-8"))
                with patch.object(walk.sys, "stdin", io.StringIO("조건 반영")):
                    walk.recheck(run["id"])
                saved = json.loads((self.root / (run["id"] + ".json")).read_text(encoding="utf-8"))
                self.assertEqual(saved["app"], app)
                self.assertIn("## 근본 원인\n원인: 조건 누락\n근거: 기록이 그렇다\n찾아본 것: 기록을 읽음", output.getvalue())
                self.assertIn("재발 판정: 닫힘", output.getvalue())
                self.assertIn(f"진행: 기록 파일: {self.root / (run['id'] + '.json')}", output.getvalue())
                self.assertIn("진행: 질문 2: What in the target's operating flow caused that phenomenon?", output.getvalue())
                self.assertIn('진행: Jev 판정: {"said": "cause", "grounds": true}', output.getvalue())
                self.assertEqual(len([x for x in saved["log"] if "question" in x]), 6)
                if app == "claude":
                    self.assertEqual(claude.call_count, 6)
                    self.assertFalse(claude.call_args_list[0].kwargs["resume"])
                    self.assertTrue(claude.call_args_list[-1].kwargs["resume"])
                    self.assertIn('"cause": "what caused it"', claude.call_args_list[1].args[0])
                    codex.assert_not_called()
                else:
                    claude.assert_not_called()
                    self.assertEqual(codex.call_count, 6)
                    self.assertEqual(saved["asked"], True)

    def test_jev_reads_the_fields_and_the_previous_cause(self):
        with patch.object(walk, "ask", side_effect=[reply("phenomenon", "결과 없음"), reply("cause", "조건 누락"), reply("cause", "출발점"),
                                                    "흐름", "해결책"]), \
                patch.object(walk, "jev", side_effect=[said(True), said("cause"), said("none")]) as jev, \
                patch.object(walk.sys, "stdin", io.StringIO(json.dumps({"현상": "x", "요청": "y", "대상": "z"}))), \
                contextlib.redirect_stdout(io.StringIO()):
            walk.start("claude")
        states = [call.args[2] for call in jev.call_args_list]
        self.assertEqual(states[0], {"target": "z", "phenomenon": "결과 없음", "evidence": "기록이 그렇다", "checked": "기록을 읽음", "observations": []})
        self.assertEqual(states[1]["previous"], "결과 없음")
        self.assertEqual(states[2]["previous"], "조건 누락")
        self.assertEqual(set(jev.call_args_list[0].args[1]), {"said", "grounds"})

    def test_cause_not_found_is_not_reported_as_root(self):
        output, _ = self.start("claude", [reply("phenomenon", "현상"), reply("cause", "조건 누락"), reply("cause", "조건 누락을 다시 말함"), "흐름", "해결책"],
                               [said(True), said("cause"), said("same")])
        self.assertIn("## 더 앞선 원인을 확인하지 못해 여기서 멈춘 원인\n원인: 조건 누락", output)
        self.assertIn("## 현상에서 거슬러 올라간 원인\n1. 조건 누락\n", output)
        self.assertNotIn("## 근본 원인", output)

    def test_phenomenon_not_stated_twice_stops_with_saved_record(self):
        with self.assertRaisesRegex(ValueError, "다시 물어도 답하지 못함"), contextlib.redirect_stderr(io.StringIO()):
            self.start("claude", [reply("phenomenon", "원인은 A")] * 2, [said(False), said(False)])
        saved = json.loads(next(self.root.glob("*.json")).read_text(encoding="utf-8"))
        self.assertEqual(len([x for x in saved["log"] if "question" in x]), 2)
        self.assertIn(walk.Q_PHENOMENON_AGAIN, saved["error"])

    def test_failure_before_any_answer_is_recorded(self):
        with self.assertRaises(RuntimeError), contextlib.redirect_stderr(io.StringIO()):
            self.start("claude", [RuntimeError("claude 오류")], [])
        saved = json.loads(next(self.root.glob("*.json")).read_text(encoding="utf-8"))
        self.assertEqual(saved["error"], "RuntimeError: claude 오류")

    def test_no_cause_at_all_is_not_reported_as_root(self):
        output, _ = self.start("claude", [reply("phenomenon", "현상"), reply("cause", "원인은 더 없음"), "흐름", "해결책"], [said(True), said("none")])
        self.assertIn("## 원인을 찾지 못했습니다", output)
        self.assertNotIn("## 근본 원인", output)

    def test_jev_asks_in_its_own_formats(self):
        def answer(answers):
            response = io.BytesIO(json.dumps({"answers": answers}).encode())
            response.__enter__ = lambda *a: response
            response.__exit__ = lambda *a: None
            return response
        run = self.run_state()
        questions = {"said": walk.J_CHAIN, "grounds": walk.J_GROUNDS}
        with patch.object(walk, "jev_key", return_value="key"), patch.object(walk.urllib.request, "urlopen") as call:
            call.return_value = answer({"said": {"type": "choice", "choice": "none", "confidence": 0.9},
                                        "grounds": {"type": "noul", "noul": 0.82}})
            self.assertEqual(walk.jev(run, questions, {"cause": "x"}), {"said": "none", "grounds": True})
            sent = json.loads(call.call_args.args[0].data)["questions"]
            self.assertEqual({name: q["type"] for name, q in sent.items()}, {"said": "choice", "grounds": "noul"})
            bad = {"said": {"type": "choice", "choice": "모름"}, "grounds": {"type": "noul", "noul": 0.9}}
            call.side_effect = [answer(bad), answer(bad)]
            with self.assertRaises(ValueError):
                walk.jev(run, questions, {"cause": "x"})
        self.assertEqual([x["answer"] for x in run["log"]], [{"said": "none", "grounds": 0.82}])

    def test_answer_without_grounds_is_asked_again(self):
        output, claude = self.start("claude", [reply("phenomenon", "현상"), reply("cause", "못 찾음", checked="없음"), reply("cause", "조건 누락"),
                                               reply("cause", "출발점"), "흐름", "해결책"],
                                    [said(True), said("not found", grounds=False), said("cause"), said("none")])
        self.assertIn("## 근본 원인\n원인: 조건 누락", output)
        self.assertIn("## 현상에서 거슬러 올라간 원인\n1. 조건 누락\n", output)
        self.assertTrue(claude.call_args_list[2].args[0].startswith(walk.Q_GROUNDS_AGAIN))

    def test_answer_without_grounds_twice_stops(self):
        with self.assertRaisesRegex(ValueError, "다시 물어도 답하지 못함"), contextlib.redirect_stderr(io.StringIO()):
            self.start("claude", [reply("phenomenon", "현상")] + [reply("cause", "못 찾음", checked="없음")] * 2,
                       [said(True), said("not found", False), said("not found", False)])
        saved = json.loads(next(self.root.glob("*.json")).read_text(encoding="utf-8"))
        self.assertIn(walk.Q_GROUNDS_AGAIN, saved["error"])

    def test_reply_is_normalized_and_unreadable_json_is_asked_once_more(self):
        fenced = '```json\n{"Cause ": "조건 누락", "EVIDENCE": "기록", "checked": ["로그 읽음", "다시 실행"]}\n```'
        self.assertEqual(walk.fields(fenced, ("cause", "evidence", "checked")),
                         {"cause": "조건 누락", "evidence": "기록", "checked": "로그 읽음\n다시 실행"})
        for bad in ("JSON 없음", '{"cause": "x", "evidence": "y"}', '{"cause": "", "evidence": "y", "checked": "z"}', "[1, 2]"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                walk.fields(bad, ("cause", "evidence", "checked"))
        with patch.object(walk, "ask", side_effect=["원인은 조건 누락입니다", reply("cause", "조건 누락")]) as ask, \
                patch.object(walk, "jev", return_value=said("cause")):
            answer, _ = walk.judged(self.run_state(), "질문", "cause", walk.J_CHAIN, {})
        self.assertEqual(answer["cause"], "조건 누락")
        self.assertTrue(ask.call_args_list[1].args[1].startswith("Your reply could not be read"))
        with patch.object(walk, "ask", side_effect=["아님", "또 아님"]), patch.object(walk, "jev") as jev, self.assertRaises(ValueError):
            walk.judged(self.run_state(), "질문", "cause", walk.J_CHAIN, {})
        jev.assert_not_called()


    def test_empty_claude_answer_or_boolean_probability_is_not_success(self):
        with patch.object(walk.shutil, "which", return_value="claude"), \
                patch.object(walk, "stream", side_effect=streamed(json.dumps({"type": "result", "result": "  "}))), \
                self.assertRaises(RuntimeError):
            walk.claude("질문", "지시", "session", False, self.root)
        response = io.BytesIO(json.dumps({"answers": {"answer": {"type": "noul", "noul": True}}}).encode())
        with patch.object(walk, "jev_key", return_value="key"), \
                patch.object(walk.urllib.request, "urlopen", return_value=contextlib.nullcontext(response)), \
                self.assertRaises(ValueError):
            walk.jev(self.run_state(), {"answer": walk.J_PHENOMENON}, {"답": "x"})

    def test_native_codex_owns_tools_and_resumes_same_session(self):
        run = self.run_state("codex")
        scratch = self.root / run["id"]
        observation = {"type": "command_execution", "command": "read file", "aggregated_output": "actual contents", "exit_code": 0, "status": "completed"}
        with patch.object(walk.shutil, "which", return_value="codex"), \
                patch.object(walk, "stream", side_effect=native_reply("현상", [observation])) as call:
            self.assertEqual(walk.ask(run, "질문"), "현상")
            self.assertEqual(run["session"], "native-session")
            self.assertEqual(walk.ask(run, "다음 질문"), "현상")
        first, second = (item.args[0] for item in call.call_args_list)
        self.assertNotIn("resume", first)
        self.assertEqual(second[-3:], ["resume", "native-session", "-"])
        self.assertIn("test-codex-model", first)
        self.assertEqual(first[first.index("-s") + 1], "workspace-write")
        self.assertEqual(first[first.index("-C") + 1], str(scratch))
        self.assertNotIn("--ignore-rules", first)
        self.assertEqual([item["observation"] for item in run["log"] if "observation" in item], [{"tool": "exec", "input": "read file", "output": "actual contents"}] * 2)
        self.assertTrue((scratch / "codex-0.jsonl").is_file())
        self.assertTrue((scratch / "codex-1.jsonl").is_file())

    def test_failed_or_empty_native_turn_is_not_success(self):
        for text, returncode in (("", 0), ("partial", 1)):
            with self.subTest(text=text), patch.object(walk.shutil, "which", return_value="codex"), \
                    patch.object(walk, "stream", side_effect=native_reply(text, returncode=returncode)), self.assertRaises(RuntimeError):
                walk.ask(self.run_state("codex"), "질문")

    def test_unavailable_codex_does_not_fall_back_to_claude(self):
        with patch.object(walk.shutil, "which", return_value=None), patch.object(walk, "claude") as claude:
            with self.assertRaises(FileNotFoundError):
                walk.respond(self.run_state(), "질문", "지시", self.root)
            claude.assert_not_called()

    def test_jev_gets_only_this_questions_actual_tool_results(self):
        run = self.run_state()
        observation = {"command": "inspect", "aggregated_output": "observed value", "exit_code": 0}
        run["log"].append({"observation": observation})
        def answer(*args):
            run["log"].append({"observation": {"tool": "read", "output": "current result"}})
            return reply("cause", "결과")
        with patch.object(walk, "ask", side_effect=answer), patch.object(walk, "jev", return_value=said("cause")) as jev:
            walk.judged(run, "질문", "cause", walk.J_CHAIN, {"previous": "현상"})
        self.assertEqual(jev.call_args.args[2]["observations"], [json.dumps({"tool": "read", "output": "current result"}, ensure_ascii=False)])

    def test_claude_stream_collects_actual_tool_results(self):
        run = self.run_state("claude")
        events = [{"type": "user", "message": {"content": "harness notification"}},
                  {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "read1", "name": "Read", "input": {"file_path": "target"}}]}},
                  {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "read1", "content": "actual data"}]}},
                  {"type": "result", "result": "답", "is_error": False}]
        with patch.object(walk.shutil, "which", return_value="claude"), \
                patch.object(walk, "stream", side_effect=streamed("\n".join(json.dumps(item) for item in events))) as call:
            self.assertEqual(walk.ask(run, "질문"), "답")
        self.assertEqual(call.call_args.kwargs["env"]["CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"], "1")
        args = call.call_args.args[0]
        self.assertEqual(args[args.index("--model") + 1], "test-claude-model")
        self.assertEqual([x["observation"] for x in run["log"] if "observation" in x],
                         [{"tool": "Read", "input": {"file_path": "target"}, "output": "actual data", "is_error": False}])
        self.assertEqual([walk.commentary(event) for event in events],
                         [[], ['실행: Read {"file_path": "target"}'], ["결과: actual data"], []])

    def test_stream_shows_and_records_each_line_of_the_turn(self):
        run = self.run_state()
        events = self.root / "test" / "codex-0.jsonl"
        lines = [{"type": "item.started", "item": {"type": "command_execution", "command": "ls"}},
                 {"type": "item.completed", "item": {"type": "command_execution", "command": "ls", "aggregated_output": "x" * 2000}},
                 {"type": "item.completed", "item": {"type": "agent_message", "text": "다 봤습니다"}}]
        script = "import sys; sys.stdin.read(); sys.stderr.write('warn'); " + "; ".join(f"print({json.dumps(json.dumps(line))}, flush=True)" for line in lines)
        with patch.object(walk.subprocess, "Popen", wraps=subprocess.Popen) as popen, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(walk.stream([sys.executable, "-c", script], "질문", self.root, events, run), (0, "warn"))
        shown = [x["progress"] for x in run["log"] if "progress" in x]
        self.assertEqual(shown[0], "실행: ls")
        self.assertIn("중략", shown[1])
        self.assertLess(len(shown[1]), 700)
        self.assertEqual(shown[2], "조사 에이전트: 다 봤습니다")
        self.assertEqual(output.getvalue().splitlines(), [f"진행: {x}" for x in shown])
        self.assertEqual(len(events.read_text(encoding="utf-8").splitlines()), 3)
        self.assertIn("creationflags", popen.call_args.kwargs)

    def test_observed_excerpt_has_a_bounded_payload_and_keeps_full_records(self):
        run = self.run_state()
        full = {"tool": "exec", "output": "x" * 1000000}
        run["log"] += [{"observation": full}, {"observation": {"tool": "exec", "output": "new result"}}]
        bounded = walk.observed(run, 0)
        self.assertLess(len(json.dumps(bounded)), 25000)
        self.assertIn("middle omitted", bounded["observations"][0])
        self.assertEqual(len(walk.observed(run, 1)["observations"]), 1)
        self.assertEqual(len(run["log"][0]["observation"]["output"]), 1000000)

    def test_phenomenon_rewrite_retains_this_steps_original_inspection(self):
        run = self.run_state()
        observed = {"tool": "read", "output": "actual phenomenon"}
        def answer(_run, question):
            if not any("observation" in x for x in run["log"]):
                run["log"].append({"observation": observed})
            return reply("phenomenon", "phenomenon")
        with patch.object(walk, "ask", side_effect=answer), patch.object(walk, "jev", side_effect=[said(False), said(True)]) as jev:
            walk.judged(run, "question", "phenomenon", walk.J_PHENOMENON, {}, again=walk.Q_PHENOMENON_AGAIN, grounds=walk.J_SEEN)
        self.assertEqual(jev.call_args_list[0].args[2]["observations"], jev.call_args_list[1].args[2]["observations"])
        self.assertEqual(jev.call_args_list[1].args[1]["grounds"], walk.J_SEEN)

    def test_legacy_run_resumes_claude(self):
        run = self.run_state("claude")
        del run["app"]
        run["asked"] = True
        with patch.object(walk, "claude", return_value="답") as call:
            self.assertEqual(walk.respond(run, "질문", "지시"), "답")
        self.assertTrue(call.call_args.kwargs["resume"])

    def test_watch_wakes_the_agent_only_at_stage_starts_and_ends_long_stages_and_the_end(self):
        out = self.root / "output"
        out.write_text("진행: 기록 파일: x\n진행: 질문 1: 현상\n", encoding="utf-8")
        def write():
            for wait, text in ((0.1, "진행: 조사 에이전트: 읽는 중\n"), (0.8, "진행: Jev 판정: {}\n진행: 질문 2: 원인\n"),
                               (1.2, "# 조사 결과\n\n진행 번호: id\n")):
                time.sleep(wait - (time.monotonic() - begin))
                with out.open("a", encoding="utf-8") as file:
                    file.write(text)
        begin = time.monotonic()
        writer = threading.Thread(target=write)
        writer.start()
        with patch.multiple(walk, INTERIM=0.3, SETTLE=0.05, POLL=0.02), contextlib.redirect_stdout(io.StringIO()) as output:
            walk.watch(out)
        writer.join()
        self.assertEqual(output.getvalue().splitlines(), ["단계: 1~2줄", "중간 보고: 3~3줄", "단계: 4~5줄", "끝: 6~8줄"])



if __name__ == "__main__":
    unittest.main()
