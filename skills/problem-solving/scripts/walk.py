#!/usr/bin/env python3
"""문제해결: the agent that hit a problem hands over only the phenomenon; a fresh investigator finds the cause, one question at a time.

An agent that has been working on something has usually settled on a cause already, and then fills any procedure in to fit it.
So the investigation goes to a fresh Claude or GPT with none of that context, and this script owns the order, one question at a time:
what the phenomenon is, then "what caused that?" again and again until there is no earlier cause, then the whole flow, then a fix.
Jev (TypeSafe's fast judging model) reads each answer and says only what it amounts to: a phenomenon or not, an earlier cause or
none or not found, gone or still there or not checked; and, in the same call, whether the answer gave its grounds (why, and what was
looked at or run). Judged answers come back as JSON fields; one without grounds is sent back once. Nothing is changed during the
investigation: the calling agent gets the cause and a proposed fix,
fixes with the user's approval, then asks for a recheck.

  walk.py                       how to use it (the calling agent's only instructions)
  walk.py start <app> < input.json  app: claude, codex; {"현상", "요청", "대상"} -> investigate, print the result
  walk.py recheck <id> < text   what was changed -> recheck the original failure, print the verdict
  walk.py watch <file> [<told>]  Claude Code's foreground: one line per stage start/end, long stage and end of the run's output
"""
import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

# Values the script reads (SKILL.md, 「스크립트에 필요한 것」): an environment variable, else a `name=value` line in SETTINGS.
SETTINGS = Path(os.environ.get("PROBLEM_SOLVING_SETTINGS") or Path.home() / ".config" / "problem-solving" / "settings.env")
MODEL_SETTING = {"claude": "INVESTIGATOR_CLAUDE_MODEL", "codex": "INVESTIGATOR_CODEX_MODEL"}
JEV_URL = "https://api.typesafe.ai/v1/systemone"
RUNS = Path(tempfile.gettempdir()) / "problem-solving"  # <id>.json: one investigation; <id>/: the investigator's scratch folder
SESSIONS = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "sessions"
INPUT = ("현상", "요청", "대상")

GUIDE = """문제해결은 현상 → 원인을 거슬러 묻는 연속 질문 → 버드뷰 → 해결책 순서로 합니다.

## 방식 고르기

사용자가 방식을 이미 정하지 않았으면 앱의 선택 버튼 도구로 아래 셋 중 하나를 고르게 하세요.
- 직접: 당신이 질문을 스스로 묻고 답하며 조사합니다. 아래 「직접 진행」을 따르세요.
- 스크립트 포그라운드: 이 스크립트가 조사 에이전트로 끝까지 진행하고, 당신은 출력을 지켜보다 진행 줄을 사용자에게 전합니다.
- 스크립트 백그라운드: 이 스크립트가 끝까지 진행하고, 당신은 끝나기를 기다려 결과만 보고합니다. 모든 과정은 기록 파일에 남습니다.
스크립트 방식에서 당신은 조사하지 않고 중계만 합니다.

## 스크립트 진행 (포그라운드·백그라운드)

원인 조사는 지금까지의 대화를 모르는 조사 에이전트가 질문을 하나씩 받아 합니다.

1. 조사 에이전트를 부를 CLI를 고르세요. Claude Code에서는 `claude`, 그 밖의 앱에서는 `codex`를 쓰고, 그 CLI가 없으면 설치된 다른 하나를 쓰세요. 아래 JSON을 표준입력으로 넘겨 `{run} start <앱>`을 실행하세요. 몇 분에서 수십 분 걸리니 두 방식 모두 백그라운드 프로세스로 실행하세요. 질문, 조사 에이전트가 하는 말, 실행하는 명령과 그 결과(긴 결과는 앞뒤만), Jev 판정이 나오는 즉시 `진행:`으로 시작하는 줄로 출력됩니다. 출력한 줄은 모두 기록 파일에도 남고, 첫 진행 줄이 기록 파일 위치입니다. 끝나면 마지막에 출력되는 것이 조사 결과입니다.
   {{"현상": "...", "요청": "...", "대상": "..."}}
   - 현상: 잘못된 현상과 그때의 입력·상황. 원인·해결책·짐작은 넣지 마세요. 조사 에이전트가 정해 둔 결론 없이 시작해야 하기 때문입니다.
   - 요청: 사용자가 한 말 원문 그대로.
   - 대상: 무엇에 생긴 문제인지와 그 자료가 있는 곳(서버·경로·문서·서비스 이름, 접속 방법).
   조사 에이전트는 `claude`면 Claude Code CLI(`claude -p`), `codex`면 Codex CLI(`codex exec`)로 부릅니다. 모델은 `INVESTIGATOR_CLAUDE_MODEL`·`INVESTIGATOR_CODEX_MODEL`에 정해 둔 것을 쓰고, 없으면 그 CLI의 기본 모델을 씁니다. Jev 키 `TYPESAFE_API_KEY`가 없으면 스크립트가 첫 질문 전에 멈춥니다. 그때는 SKILL.md 「스크립트에 필요한 것」대로 갖춘 뒤 다시 실행하세요.
   스크립트가 오류로 끝나면 그 오류를 사용자에게 보고하고 멈추세요. 직접 조사해서 대신하면 정해 둔 결론 없이 조사한다는 이 절차의 목적이 사라집니다.
2. 실행 중:
   - 포그라운드: 출력을 지켜보다 진행 줄이 나오면 고르거나 줄이지 말고 그대로 사용자에게 전하세요. Claude Code에서는 Monitor로 `{run} watch <출력 파일> <전한 줄 수>`를 실행하세요. 출력 파일은 `start`를 돌린 백그라운드 명령의 출력이 쌓이는 파일이고(기록 파일이 아님), 전한 줄 수는 처음엔 0, 다시 걸 때는 마지막으로 받은 끝 줄 번호입니다. 앱은 당신이 깨어나 답을 마칠 때마다 사용자에게 알림을 띄우므로, 이 명령은 질문이 시작하거나 판정이 나와 단계가 끝날 때, 한 단계가 5분 넘게 이어질 때(중간 보고), 실행이 끝날 때만 `<까닭>: <첫 줄>~<끝 줄>줄`을 한 줄 냅니다. 그때마다 출력 파일의 그 줄들을 읽어 진행 줄을 모두 한꺼번에 전하세요. Monitor가 시간이 다 돼 끝나면 같은 명령을 전한 줄 수만 바꿔 다시 거세요. 다른 앱에서는 실행 중인 프로세스의 출력을 읽는 기능으로 새 진행 줄을 받으세요.
   - 백그라운드: 진행 줄을 전하지 말고 끝나기를 기다리세요.
3. 출력된 결과를 사용자에게 보고하세요. 조사 중에는 아무것도 고치지 않았습니다. 해결까지 요청받았으면 해결책을 적용하기 전에 승인을 받으세요.
4. 고친 뒤 무엇을 바꿨는지 표준입력으로 넘겨 `{run} recheck <진행 번호>`를 실행하고 판정을 보고하세요. 열림(현상이 남음)이나 미검증(다시 해 보지 못함)이면 그 답을 보고 다시 고치거나 확인하세요.

## 직접 진행

조사 에이전트와 Jev 없이, 당신이 아래 질문을 순서대로 스스로 묻고 답합니다. 일을 해 온 에이전트는 원인을 이미 정해 두고 답을 거기에 맞추기 쉽습니다. 그러니 질문마다 그 질문에 답할 증거를 그때 새로 확인하고, 사용자에게 보이는 답에 `질문 → 확인한 것(이 질문에서 실제로 조회·실행한 것) → 결과 → 답`을 쓰세요. 새로 확인한 것이 없으면 그 답은 짐작이라고 밝히세요.
조사 중에는 원본(파일·자료·설정·서비스 상태)을 바꾸지 말고 배포·발송·게시·결제처럼 밖에 영향을 주는 일도 하지 마세요. 읽기 전용 조회, 입력·조건을 바꾼 한 번의 실행, 작업 폴더에 만든 사본에서만 확인하세요.

1. 현상: 무엇이 잘못됐는지 직접 보고, 일어난 일과 그때의 입력·상황만 쓰세요. 원인·해결책은 넣지 마세요.
2. 연속 질문: "대상의 작동 흐름에서 무엇이 그 현상을 일으켰나?"를 묻고, 답한 원인을 주어로 "무엇이 그 원인을 일으켰나?"를 더 앞선 원인이 없을 때까지 이어 물으세요. 바깥 원인(다른 서비스·장치·사용 환경)에 닿으면 그것을 받아 처리하는 우리 쪽 단계를 주어로 이으세요. 더 찾지 못하면 찾지 못했다고 쓰고, 근본 원인이라고 하지 마세요.
3. 버드뷰: 질문들과 따로 전체를 보세요. 목적, 정상 흐름, 흐름이 처음 어긋나는 곳을 실제 자료·코드·기록으로 확인하세요.
4. 해결책: 찾은 원인과 전체 흐름에 근거해 해결책과 고친 뒤 확인할 실행을 쓰세요. 원본은 바꾸지 말고, 사본에서 시험하는 것은 괜찮습니다.
5. 결과를 사용자에게 보고하세요. 해결까지 요청받았으면 해결책을 적용하기 전에 승인을 받으세요.
6. 고친 뒤 원래 상황과 같은 원인의 다른 사례를 다시 실행하고, 닫힘(둘 다 현상이 없음)·열림(현상이 남음)·미검증(다시 해 보지 못함)으로 판정해 보고하세요. 열림이나 미검증이면 다시 고치거나 확인하세요."""

INVESTIGATOR = """You investigate the cause of a problem.

Target: {target}

- Do not change originals: files, data, settings, service state. Do nothing with effects outside, such as deploying, sending, posting or paying.
- Check only by read-only queries, by running something once with changed inputs or conditions, or, when the target is code or files, by copying it into the work folder ({scratch}) and changing only the copy.
- If the target has guide files (AGENTS.md, CLAUDE.md, README and the like), read them first.
- Check the underlying execution records before drawing a cause from a report or notification. A report is a clue to inspect, not proof of what ran.
- Trace deviations within the target's purpose and workflow. For an outside condition, inspect how the target receives and handles it. The origin of the target itself is background, not a deviation in its workflow.
- Answer only the question you get, then stop.
- In `checked`, report only what you did for this question. Put results from earlier questions in `evidence`, and say when you did no new checks.
- Write in Korean."""

# Each judged answer comes back as JSON, so Jev can be pointed at one field and the script can tell a missing part from a weak one.
ANSWER = {"phenomenon": "what happened, and the input and situation at the time",
          "cause": "what caused it",
          "result": "whether the phenomenon appeared in each run"}
GROUNDS = {"evidence": "the observed results supporting your answer, including earlier results", "checked": "only queries or runs done for this question, or that none were done"}
REPLY = "\n\nReply with only this JSON:\n"
Q_PHENOMENON = ("Reported problem:\n«{report}»\n\nWhat the user said: «{request}»\n\n"
                "What is the wrong phenomenon? Look at it yourself. Write only what happened and the input and situation at the time, "
                "not causes or fixes.")
Q_CAUSE = "What in the target's operating flow caused that {subject}? Inspect that flow. If this is its first deviation, say so."
Q_RECHECK = ("This was changed:\n«{change}»\n\nRun the original situation again, and another case with the same cause. "
             "Does the phenomenon appear? Do not change originals.")
Q_PHENOMENON_AGAIN = "Write only what happened and the input and situation at the time, not causes or fixes."
Q_GROUNDS_AGAIN = "The actual tool results do not support your answer. Check the missing evidence yourself, then answer again."
Q_JSON_AGAIN = "Your reply could not be read as the JSON asked for ({problem})."
Q_BIRD = ("Apart from the questions so far, look at the whole thing. What is its purpose, what is the normal flow, "
          "and where does the flow first go wrong? Look at the actual data, code and records.")
Q_FIX = ("Propose a fix based on the causes found and the whole flow. Do not change originals; trying it on a copy is fine. "
         "Also write what to run after the fix to confirm it.")

# Jev questions in its own formats: noul answers the probability of yes, choice picks one option. Each names the JSON field it reads.
J_PHENOMENON = {"type": "noul", "instructions": "Does `phenomenon` state only what happened, with no cause and no fix?",
                "criteria": {"true": "`phenomenon` states only what happened and the input or situation at the time. "
                                     "A quoted error message or notice is something that happened.",
                             "false": "`phenomenon` says why it happened or how to fix it."}}
J_CHAIN = {'type': 'choice', 'instructions': 'Which description matches `cause`, the new answer? Use `previous` only as the thing being explained.', 'criteria': {'cause': 'The new answer names something new that caused previous, including our step that handles an outside cause.', 'same': 'The new answer only repeats previous without naming a cause.', 'none': 'The new answer says previous is the starting point with no earlier cause.', 'not found': 'The new answer gives no new cause and says it could not find or confirm one.'}}
J_GONE = {"type": "choice", "instructions": "What does `result` say happened after the change?",
          "criteria": {"gone": "The original situation and another case with the same cause were both run again, "
                               "and the phenomenon appeared in neither.",
                       "remains": "At least one of the two was run again and the phenomenon appeared.",
                       "not checked": "The phenomenon appeared in no run, and at least one of the two was not run again."}}
J_GROUNDS = {"type": "noul", "instructions": "Do `observations` show the checks and results reported in this answer?",
             "criteria": {"true": "The reported inspections, runs and results appear in the actual records.",
                          "false": "There are no investigation records, or a reported check or result is missing or contradicted."}}
J_SEEN = {"type": "noul", "instructions": "Do `observations` show the phenomenon being inspected or reproduced?",
          "criteria": {"true": "The recorded inspection or reproduction shows the stated phenomenon.",
                       "false": "There is no recorded inspection or reproduction of the stated phenomenon."}}
J_RECHECK = {"type": "noul", "instructions": "Do `observations` show the rerun attempts and outcomes described in `result`?",
             "criteria": {"true": "The actual results support the reported reruns or the reported inability to run them.",
                          "false": "A claimed rerun or outcome is missing from, or contradicted by, the actual results."}}
VERDICT = {"gone": "닫힘 (현상이 사라졌습니다)", "remains": "열림 (현상이 남았습니다)", "not checked": "미검증 (다시 해 보지 못했습니다)"}
LABELS = {"phenomenon": "현상", "cause": "원인", "result": "결과", "evidence": "근거", "checked": "찾아본 것"}

def codex(run, prompt, system, cwd):
    """One native Codex turn; resume this investigator, and retain its actual shell results."""
    exe = shutil.which("codex")
    if not exe:
        raise FileNotFoundError("codex 명령을 찾을 수 없음")
    instructions = cwd / "investigator.txt"
    instructions.write_text(system, encoding="utf-8")
    turn = sum("question" in item for item in run["log"])
    events = cwd / f"codex-{turn}.jsonl"
    args = [exe, "exec", "--ignore-user-config", "--skip-git-repo-check", "--json",
            *(["-m", model] if (model := setting(MODEL_SETTING["codex"], "")) else []),
            "-s", "workspace-write", "-C", str(cwd)]
    # Investigations read servers and services over the network; writes stay confined to the workspace.
    config = {"model_instructions_file": instructions.as_posix(), "approval_policy": "never",
              "sandbox_workspace_write.network_access": True, "tool_output_token_limit": 4000,
              "skills.include_instructions": False, "agents.enabled": False, "project_doc_max_bytes": 0,
              "sandbox_workspace_write.exclude_slash_tmp": True, "sandbox_workspace_write.exclude_tmpdir_env_var": True}
    if os.name == "nt":
        config["windows.sandbox"] = "elevated"
    for key, value in config.items():
        args += ["-c", f"{key}={json.dumps(value)}"]
    for feature in ("apps", "plugins", "memories", "hooks", "remote_plugin", "skill_search", "tool_suggest", "multi_agent", "multi_agent_v2"):
        args += ["--disable", feature]
    args += ["resume", run["session"], "-"] if run["asked"] else ["-"]
    env = None
    if os.name != "nt":
        # Inside the Linux sandbox /etc/ssh is owned by nobody, and ssh refuses to read its own system config.
        shim = cwd / "bin" / "ssh"
        shim.parent.mkdir(exist_ok=True)
        shim.write_text(f'#!/bin/sh\nexec {shutil.which("ssh")} -F /dev/null "$@"\n', encoding="utf-8")
        shim.chmod(0o755)
        env = {**os.environ, "PATH": f"{shim.parent}{os.pathsep}{os.environ['PATH']}"}
    returncode, stderr = stream(args, prompt, cwd, events, run, env=env)
    answer, complete = None, False
    with events.open(encoding="utf-8") as source:
        for line in source:
            event = json.loads(line)
            if event["type"] == "thread.started":
                run["session"] = event["thread_id"]
            if event["type"] == "item.completed":
                item = event["item"]
                if item["type"] == "agent_message":
                    answer = item["text"]
            if event["type"] == "turn.completed":
                complete = True
    run["log"].append({"events": str(events)})
    save(run)
    if returncode or not complete or not isinstance(answer, str) or not answer.strip():
        raise RuntimeError(f"codex exec가 완성된 답을 반환하지 않음 (종료 코드 {returncode}): {stderr[-1000:]}; 기록: {events}")
    sessions = list(SESSIONS.glob(f"**/*{run['session']}.jsonl"))
    if len(sessions) != 1:
        raise RuntimeError(f"Codex 실제 도구 기록을 하나로 찾지 못함: {run['session']}")
    calls, observations = {}, []
    with sessions[0].open(encoding="utf-8") as source:
        for line in source:
            event = json.loads(line)
            item = event.get("payload", {})
            if event["type"] == "turn_context":
                calls, observations = {}, []
            elif event["type"] == "response_item":
                if item.get("type") in ("custom_tool_call", "function_call"):
                    calls[item["call_id"]] = {"tool": item["name"], "input": item["input"] if item["type"] == "custom_tool_call" else item["arguments"]}
                elif item.get("type") in ("custom_tool_call_output", "function_call_output"):
                    observations.append({**calls[item["call_id"]], "output": item["output"]})
    run["log"] += [{"observation": item} for item in observations]
    save(run)
    return answer


def respond(run, prompt, system, cwd=None):
    if run.get("app", "claude") == "claude":
        return claude(prompt, system, run["session"], resume=run["asked"], cwd=cwd, run=run)
    return codex(run, prompt, system, cwd)


def setting(name, default=None):
    """An environment variable, else a `name=value` line in SETTINGS. Raises naming where it is read from."""
    value = os.environ.get(name)
    if value is None and SETTINGS.is_file():
        for line in SETTINGS.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(f"{name}="):
                value = line.split("=", 1)[1]
    value = (value or "").strip().strip('"\'')
    if value:
        return value
    if default is not None:
        return default
    raise KeyError(f"{name}이 없음: 환경 변수나 {SETTINGS}의 `{name}=값` 줄에서 읽습니다. SKILL.md 「스크립트에 필요한 것」을 보세요.")


def jev_key():
    return setting("TYPESAFE_API_KEY")


def jev(run, questions, state):
    """Jev's answers to questions about one state, asked in one call (True/False for noul, the option for choice);
    asked at most twice, raises when unusable."""
    body = {"state": state, "model": setting("JEV_MODEL", "jev-latest"), "questions": questions}
    call = urllib.request.Request(JEV_URL, data=json.dumps(body).encode(),
                                  headers={"Authorization": f"Bearer {jev_key()}", "Content-Type": "application/json"})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(call, timeout=30) as response:
                answers = json.load(response)["answers"]
            values = {name: answers[name][question["type"]] for name, question in questions.items()}
            for name, question in questions.items():
                value = values[name]
                if question["type"] == "noul" and not (type(value) in (int, float) and 0 <= value <= 1):
                    raise ValueError(f"Jev의 확률이 0~1이 아님: {value}")
                if question["type"] == "choice" and value not in question["criteria"]:
                    raise ValueError(f"Jev가 보기에 없는 답을 냄: {value}")
            run["log"].append({"jev": {name: q["instructions"] for name, q in questions.items()}, "state": state, "answer": values})
            save(run)
            return {name: values[name] >= 0.5 if q["type"] == "noul" else values[name] for name, q in questions.items()}
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"Jev HTTP {error.code}: {error.read().decode('utf-8', errors='replace')[:2000]}") from error
        except (OSError, ValueError, KeyError, TypeError):
            if attempt:
                raise


def claude(prompt, system, session, resume, cwd, run=None):
    """The reply of a headless Claude Code without this harness's instructions, skills, plugins, hooks or MCP servers."""
    exe = shutil.which("claude")
    if not exe:
        raise FileNotFoundError("claude 명령을 찾을 수 없음")
    tools = ("Read", "Grep", "Glob", "Bash")
    args = [exe, "-p", "--output-format", "stream-json", "--verbose", "--safe-mode", "--strict-mcp-config",
            *(["--model", model] if (model := setting(MODEL_SETTING["claude"], "")) else []),
            "--system-prompt", system, "--tools", ",".join(tools), "--allowedTools", " ".join(tools),
            "--resume" if resume else "--session-id", session]
    events = cwd / (f"claude-{sum('question' in item for item in run['log'])}.jsonl" if run is not None else "claude.jsonl")
    # A backgrounded command lets it answer before the result, then wakes it for a second reply after the answer.
    returncode, _ = stream(args, prompt, cwd, events, run, env={**os.environ, "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"})
    reply, calls = None, {}
    if run is not None:
        run["log"].append({"events": str(events)})
    for line in events.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        if event["type"] in ("assistant", "user"):
            if isinstance(event["message"]["content"], str):
                continue
            for item in event["message"]["content"]:
                if item["type"] == "tool_use":
                    calls[item["id"]] = {"tool": item["name"], "input": item["input"]}
                elif item["type"] == "tool_result" and run is not None:
                    run["log"].append({"observation": {**calls[item["tool_use_id"]], "output": item["content"], "is_error": item.get("is_error", False)}})
        elif event["type"] == "result":
            reply = event
    if run is not None:
        save(run)
    if returncode or reply is None or reply.get("is_error") or not isinstance(reply.get("result"), str) or not reply["result"].strip():
        raise RuntimeError(f"claude 오류: {json.dumps(reply, ensure_ascii=False)[-1000:]}")
    return reply["result"]


def save(run):
    (RUNS / f"{run['id']}.json").write_text(json.dumps(run, ensure_ascii=False, indent=1), encoding="utf-8")


def progress(run, text):
    """One line the calling agent can read while the run goes on, also kept in the run's record."""
    line = " ".join(text.split())
    if run is not None:
        run["log"].append({"progress": line})
        save(run)
    print(f"진행: {line}", flush=True)


def excerpt(value, size=600):
    """A tool result short enough to show; the full result stays in the record."""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    if len(text) <= size:
        return text
    return f"{text[:size // 2]} …(중략, 전체는 기록 파일에)… {text[-size // 2:]}"


def commentary(event):
    """What one Claude or Codex event shows of the investigator's work: its words, the tools it runs, and their results."""
    shown = []
    if event.get("type") in ("assistant", "user") and isinstance(event["message"]["content"], list):
        for item in event["message"]["content"]:
            if item["type"] == "text":
                shown.append(f"조사 에이전트: {item['text']}")
            elif item["type"] == "tool_use":
                shown.append(f"실행: {item['name']} {json.dumps(item['input'], ensure_ascii=False)}")
            elif item["type"] == "tool_result":
                shown.append(f"결과: {excerpt(item['content'])}")
    elif event.get("type") == "item.started" and event["item"]["type"] == "command_execution":
        shown.append(f"실행: {event['item']['command']}")
    elif event.get("type") == "item.completed":
        item = event["item"]
        if item["type"] in ("agent_message", "reasoning"):
            shown.append(f"조사 에이전트: {item.get('text', '')}")
        elif item["type"] == "command_execution":
            shown.append(f"결과: {excerpt(item.get('aggregated_output', ''))}")
        else:
            shown.append(f"{item['type']}: {excerpt(item)}")
    return shown


def stream(args, prompt, cwd, events, run, env=None):
    """One investigator turn. Each output line is saved to `events` and its commentary shown as it arrives.
    Returns the exit code and stderr."""
    errors = events.with_suffix(".err")
    with events.open("w", encoding="utf-8") as output, errors.open("w", encoding="utf-8") as error:
        process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=error, text=True, encoding="utf-8",
                                   cwd=cwd, env=env, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        process.stdin.write(prompt)
        process.stdin.close()
        for line in process.stdout:
            output.write(line)
            output.flush()
            if line.strip():
                for text in commentary(json.loads(line)):
                    progress(run, text)
        process.wait()
    return process.returncode, errors.read_text(encoding="utf-8")


def ask(run, question):
    """The investigator's answer to one question, in the same conversation as the questions before it."""
    scratch = RUNS / run["id"]
    progress(run, f"질문 {sum('question' in entry for entry in run['log']) + 1}: {question.split(REPLY)[0]}")
    answer = respond(run, question, INVESTIGATOR.format(target=run["input"]["대상"], scratch=scratch), cwd=scratch)
    run["asked"] = True
    run["log"].append({"question": question, "answer": answer})
    save(run)
    return answer


def fields(reply, keys):
    """The asked JSON fields of a reply, normalized: text around the braces (code fences, notes) is dropped, key case and spaces
    are ignored, and a list of strings is joined into lines. Raises when a field is still missing or empty."""
    start, end = reply.find("{"), reply.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object")
    got = json.loads(reply[start:end + 1])
    if not isinstance(got, dict):
        raise ValueError("not a JSON object")
    got = {str(key).strip().lower(): value for key, value in got.items()}
    answer = {}
    for key in keys:
        value = got.get(key)
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            value = "\n".join(value)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"missing or empty `{key}`")
        answer[key] = value.strip()
    return answer


def shown(answer):
    return "\n".join(f"{LABELS[key]}: {value}" for key, value in answer.items())


def observed(run, begin):
    """Bound Jev's evidence below its 32k per-question context; keep full results in the run and native logs."""
    items = [item["observation"] for item in run["log"][begin:] if "observation" in item]
    budget = 24000 // max(1, len(items))
    records = []
    for item in items:
        text = json.dumps(item, ensure_ascii=False)
        if len(text) > budget:
            half = budget // 2
            text = text[:half] + "\n[output excerpt: middle omitted; omitted text is not evidence]\n" + text[-half:]
        records.append(text)
    return {"observations": records}


def judged(run, question, name, judgment, state, again=None, grounds=J_GROUNDS):
    """The investigator's answer, as JSON fields (`name` and the grounds), and what Jev says it amounts to. Jev also says whether
    it gave its grounds; an answer without grounds (or, when `again` is given, one Jev says no to) is asked once more, then the run stops.
    A reply that cannot be read as the JSON is asked once more for it."""
    keys = (name, *GROUNDS)
    shape = REPLY + json.dumps({name: ANSWER[name], **GROUNDS}, ensure_ascii=False)
    begin = len(run["log"])
    for attempt in range(2):
        try:
            answer = fields(ask(run, question + shape), keys)
        except ValueError as error:
            answer = fields(ask(run, Q_JSON_AGAIN.format(problem=error) + shape), keys)
        said = jev(run, {"said": judgment, "grounds": grounds}, {"target": run["input"]["대상"], **state, **answer, **observed(run, begin)})
        progress(run, f"Jev 판정: {json.dumps(said, ensure_ascii=False)}")
        missing = [text for ok, text in ((said["said"] is not False, again), (said["grounds"], Q_GROUNDS_AGAIN)) if not ok]
        if not missing:
            return answer, said["said"]
        if attempt:
            raise ValueError(f"조사 에이전트가 다시 물어도 답하지 못함: {' '.join(missing)}")
        question = " ".join(missing)


@contextlib.contextmanager
def recorded(run):
    """Keeps the record of a run that stops with an error, so what was asked and answered before it can still be read."""
    try:
        yield
    except Exception as error:
        run["error"] = f"{type(error).__name__}: {error}"
        save(run)
        print(f"기록: {RUNS / (run['id'] + '.json')}", file=sys.stderr)
        raise


def record(run):
    """The questions and answers so far, in order."""
    return "\n\n".join(f"[질문]\n{entry['question']}\n\n[답]\n{entry['answer']}" for entry in run["log"] if "question" in entry)


def finish(run, head):
    run["result"] = head
    save(run)
    print(f"{head}\n\n진행 번호: {run['id']}\n전체 기록(Jev 판정 포함): {RUNS / (run['id'] + '.json')}\n\n## 질문과 답\n\n{record(run)}")


def start(app="claude"):
    given = json.loads(sys.stdin.read())
    absent = [name for name in INPUT if not str(given.get(name) or "").strip()]
    if absent:
        raise ValueError(f"넘긴 JSON에 {', '.join(absent)} 값이 없음")
    # The key is checked before the first question, not after minutes of investigation; a missing CLI fails at once anyway.
    try:
        jev_key()
    except KeyError as missing:
        raise SystemExit(missing.args[0])
    run = {"id": uuid.uuid4().hex[:8], "app": app, "session": str(uuid.uuid4()), "asked": False,
           "input": {name: given[name] for name in INPUT}, "log": []}
    (RUNS / run["id"]).mkdir(parents=True)
    save(run)
    progress(run, f"기록 파일: {RUNS / (run['id'] + '.json')}")
    with recorded(run):
        question = Q_PHENOMENON.format(report=run["input"]["현상"], request=run["input"]["요청"])
        answer, _ = judged(run, question, "phenomenon", J_PHENOMENON, {}, again=Q_PHENOMENON_AGAIN, grounds=J_SEEN)
        # Jev sees one question at a time, so each cause is judged against the one before it (the phenomenon at first).
        chain, before, subject = [], answer["phenomenon"], "phenomenon"
        while True:
            answer, said = judged(run, Q_CAUSE.format(subject=subject), "cause", J_CHAIN, {"previous": before})
            if said != "cause":
                break
            chain.append(answer)
            before, subject = answer["cause"], "cause"
        ask(run, Q_BIRD)
        fix = ask(run, Q_FIX)
    if not chain:
        cause = "## 원인을 찾지 못했습니다\n현상의 원인에 대한 답은 아래 기록에 있습니다."
    else:
        title = "근본 원인" if said == "none" else "더 앞선 원인을 확인하지 못해 여기서 멈춘 원인"
        steps = "\n".join(f"{number}. {step['cause']}" for number, step in enumerate(chain, 1))
        cause = f"## {title}\n{shown(chain[-1])}\n\n## 현상에서 거슬러 올라간 원인\n{steps}"
    finish(run, f"# 조사 결과\n\n{cause}\n\n## 해결책\n{fix}")


def recheck(run_id):
    path = RUNS / f"{run_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"진행 번호 {run_id}의 기록이 없음: {path}")
    change = sys.stdin.read().strip()
    if not change:
        raise ValueError("무엇을 고쳤는지 표준입력으로 넘기지 않음")
    run = json.loads(path.read_text(encoding="utf-8"))
    run["log"].append({"recheck": change})
    with recorded(run):
        answer, result = judged(run, Q_RECHECK.format(change=change), "result", J_GONE, {}, grounds=J_RECHECK)
    finish(run, f"# 재발 판정: {VERDICT[result]}\n\n{shown(answer)}")


STAGE = ("진행: 질문 ", "진행: Jev 판정:")  # a question starts a stage; Jev's judgment ends it
END = ("진행 번호: ", "Traceback (")  # finish() prints the first; a run that stops with an error, the second
INTERIM, SETTLE, POLL = 300, 3, 2


def watch(path, told=0):
    """Claude Code's foreground. Every Monitor line wakes the calling agent, and every wake ends in a
    Windows notification, so one line per 진행 line made 99 notifications in 13 minutes. This prints one line only when a stage
    starts or ends, when a stage has gone INTERIM seconds without one, and at the end; the agent reads the lines it names."""
    path, last = Path(path), time.monotonic()
    while True:
        lines = path.read_text(encoding="utf-8", errors="replace").split("\n")[:-1] if path.exists() else []
        new = lines[told:]
        reason = ("끝" if any(line.startswith(END) for line in new) else "단계" if any(line.startswith(STAGE) for line in new)
                  else "중간 보고" if new and time.monotonic() - last >= INTERIM else None)
        if reason:
            time.sleep(SETTLE)  # a judgment and the next question come together; the rest of the result follows its first line
            lines = path.read_text(encoding="utf-8", errors="replace").split("\n")[:-1]
            print(f"{reason}: {told + 1}~{len(lines)}줄", flush=True)
            if reason == "끝":
                return
            told, last = len(lines), time.monotonic()
        time.sleep(POLL)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    command = sys.argv[1:]
    if not command:
        print(GUIDE.format(run=f'"{sys.executable}" "{Path(__file__).resolve()}"'))
    elif command == ["start"]:
        start()
    elif len(command) == 2 and command[0] == "start" and command[1] in MODEL_SETTING:
        start(command[1])
    elif len(command) == 2 and command[0] == "recheck":
        recheck(command[1])
    elif command[0] == "watch" and len(command) in (2, 3):
        watch(command[1], int(command[2]) if len(command) == 3 else 0)
    else:
        raise SystemExit(f"알 수 없는 인자: {' '.join(command)}\n인자 없이 실행하면 사용법이 나옵니다.")


if __name__ == "__main__":
    main()
