# Chaconne Skills

Claude Code와 Codex에서 쓰는 에이전트 스킬 모음입니다. 실제 작업에서 쓰며 다듬은 스킬 가운데 누구나 써도 되는 것만 골라 올렸습니다. 대부분 한국어로 쓰여 있습니다.

Agent skills for Claude Code and Codex, refined through daily use. Most are written in Korean.

## 스킬

| 스킬 | 하는 일 |
|---|---|
| [agent-script-role](skills/agent-script-role) | 스크립트와 LLM이 함께 도는 코드(에이전트 호출, 파이프라인, 예약 작업)에서 스크립트와 모델이 맡을 일을 나눈다 |
| [code-review-loop](skills/code-review-loop) | PR이나 diff를 리뷰하고, 고치고, 지적이 없을 때까지 같은 범위를 다시 리뷰한다 |
| [evolution-loop](skills/evolution-loop) | 시스템·프롬프트·스킬을 실험과 회귀 검사로 되풀이해 개선한다 |
| [explanation-writing](skills/explanation-writing) | 처음 읽는 사람에게 설명하는 글(README, 소개 문서)을 실제 사례, 맞물린 Q/A, 레이아웃, 단순한 도표로 쓴다 |
| [landing-page](skills/landing-page) | 랜딩페이지를 메시지·문구부터 디자인 시안, 섹션별 제작, 배포까지 단계별로 만든다 |
| [preflight](skills/preflight) | 스킬이나 반복 작업을 돌리기 전에 드라이런으로 전제 조건과 실패 위험을 점검한다 |
| [problem-solving](skills/problem-solving) | 오류의 근본 원인을 질문을 하나씩 던져 실제 확인으로 찾는다. 언어 모델이 결론부터 내고 확인만 하는 습성을, 맥락 없는 조사 에이전트와 판정 모델로 막는다. 왜 이런 구조인지는 [설명](skills/problem-solving/README.md), 스크립트 방식에 필요한 것(Claude Code나 Codex CLI, Jev 키)은 `SKILL.md` |
| [prompt-guide](skills/prompt-guide) | LLM이 읽는 프롬프트·지시문을 설계하거나 점검한다 |
| [skill-review](skills/skill-review) | 스킬 하나를 prompt-guide·skill-writing-guide로 점검하고 고치기를 되풀이한다 |
| [skill-writing-guide](skills/skill-writing-guide) | 스킬·지시문에 넣을 정보와 뺄 정보를 가른다 |
| [smart-ux](skills/smart-ux) | 화면과 사용자 흐름을 사용성·접근성·윤리적 행동 설계 기준으로 만들고 점검한다 |
| [user-copy](skills/user-copy) | 버튼·안내·오류 같은 화면 문구를 처음 보는 사람 입장에서 쓰고 고친다 |
| [video-production](skills/video-production) | 제품 영상·숏폼·모션그래픽을 기획부터 콘티, 음성·음악, 제작, 점검까지 단계별로 만든다 |
| [web-automation](skills/web-automation) | 웹 화면 조작과 브라우저 자동화 코드를 결과 확인 중심으로 만들고 검증한다 |

`skill-review`는 `prompt-guide`·`skill-writing-guide`를 함께 씁니다. `landing-page`·`video-production`은 다른 스킬과 도구를 함께 쓰며, 무엇이 필요한지는 각 `SKILL.md`의 표에 있습니다.

## 설치

쓰고 싶은 스킬 폴더를 통째로 복사합니다.

- Claude Code: `~/.claude/skills/<스킬 이름>/` (프로젝트에만 쓰려면 `<프로젝트>/.claude/skills/`)
- Codex: `~/.codex/skills/<스킬 이름>/`

```bash
git clone https://github.com/chaconne67/chaconne-skills.git
cp -r chaconne-skills/skills/problem-solving ~/.claude/skills/
```

## 라이선스

[MIT](LICENSE)
