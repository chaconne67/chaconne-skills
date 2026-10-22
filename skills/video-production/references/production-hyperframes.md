# 제작: HyperFrames

HeyGen의 HTML→영상 도구(Apache 2.0). 한 장면을 HTML·CSS로 그리고 GSAP 시간축으로 움직인다. Remotion으로 만든 사용법 영상을 같은 대본·목소리·음악·박자로 다시 만들어 화면 유사도(SSIM) 0.992, 음량 차 0.1dB 안, 렌더 시간 비슷함(56초 영상 23~26초)을 확인했다. 같은 대본으로 키네틱판도 틀 하나 복사와 약 120줄 수정으로 만들었다.

## 공식 스킬

HyperFrames는 에이전트용 공식 스킬을 함께 낸다. 작성 계약과 명령은 그것이 정본이다.

- 꼭 읽을 것: `hyperframes-core`(작성 계약), `hyperframes-cli`(명령), `hyperframes-animation`(움직임 규칙·전환·글자 효과), `hyperframes-audio`(소리 배치·볼륨).
- 위치: 저장소 `https://github.com/heygen-com/hyperframes`의 설치한 판 태그(예: `v0.8.181`) `skills/` 폴더를 읽는다.
  - 다른 판: `git clone --depth 1 --branch v<판> https://github.com/heygen-com/hyperframes /tmp/hf-<판>` 뒤 `skills/`를 읽는다.
- `npx hyperframes skills`(설치 명령)는 돌리지 않는다. 공식 스킬을 에이전트 앱에 설치하는데, 그중 `hyperframes` 입구 스킬이 모든 영상 요청을 자기 인터뷰·승인 흐름으로 가져가 이 스킬의 단계를 건너뛰게 만든다.
- 같은 이유로 공식 입구 스킬의 인터뷰·승인 흐름과 `product-launch-video` 같은 작업 흐름 스킬은 따르지 않는다. 기획·승인은 이 스킬이 맡고, 공식 스킬은 작성·명령 참고로만 읽는다.

## 준비

```bash
cd <영상 작업 폴더>
npm init -y && npm i --save-exact hyperframes@0.8.181 gsap@3.14.2
```

- 판은 고정한다(`--save-exact`). 새 판으로 올릴 때는 `npx hyperframes check`가 통과하는지 보고, 올린 판을 기록한다.
- 환경 변수(`env.sh`를 만들어 `source`):
  - `HYPERFRAMES_NO_TELEMETRY=1`, `DO_NOT_TRACK=1`: 사용 기록 전송이 기본으로 켜져 있다.
  - `HYPERFRAMES_BROWSER_PATH`: `unzip`이 없는 서버에서는 `browser ensure`가 실패한다. chrome-headless-shell을 따로 받아 두고 그 실행 파일 경로를 준다(예: `$PWD/.chrome/chrome-headless-shell-linux64/chrome-headless-shell`).
- `snapshot` 전에는 `GEMINI_API_KEY`를 비운다(`env -u GEMINI_API_KEY npx hyperframes snapshot …`). 키가 있으면 화면을 Gemini로 보낸다.

## 프로젝트 모양

박자·목소리 시각을 손으로 HTML에 적지 않고, 자료에서 HTML을 만든다. 시작 틀이 이 스킬의 `scripts/hyperframes/`에 있다.

```text
<영상 작업 폴더>/
  env.sh
  voices.json, lines.json   # 목소리 설정과 대사 (오디오 참고)
  vo.json                   # lines.py 결과
  beats.json                # beats.py 결과
  scenes.json               # 장면 목록: {"music": "assets/music/<곡>.mp3", "music_volume": 0.081, "scenes": [{"title": "…", "lines": ["줄 id", …]}]}
  src/index.tpl             # 장면 HTML·CSS·GSAP 틀. 루트에 두지 않는다(루트의 두 번째 *.html은 lint 오류)
  assets/                   # 음성·음악·효과음·글꼴(fonts/main.woff2)·그림, gsap.min.js(build.py가 복사)
  index.html                # build.py가 만든 결과
  out/
```

- `python3 scripts/hyperframes/build.py <영상 작업 폴더> [틀]`: 장면을 음악 박자에 놓는다. 장면 첫 박에 제목, 다음 박부터 줄마다 앞 줄이 끝나고 0.4초 뒤의 첫 박에 시작, 마지막 줄 뒤 0.8초 이후의 첫 짝수 박에서 장면이 끝난다. 소리 클립과 음악 볼륨 줄(처음 20프레임 커짐, 마지막 75프레임 줄어듦)을 넣고, 장면 계획 JSON을 틀에 넣어 `index.html`을 쓴다.
- 시작 틀 `scripts/hyperframes/index.tpl`은 제목과 낱말별로 밝아지는 자막만 있는 최소 모양이다. 영상 작업 폴더의 `src/index.tpl`로 복사해 5단계 디자인 컨셉대로 장면 HTML·CSS·움직임을 바꾸고, 그 경로를 `build.py`의 두 번째 인자로 준다. 장면 계획 방식을 바꿔야 하면 `build.py`도 `src/`로 복사해 고친다.
- 여러 판(기본·키네틱)은 틀만 바꿔 같은 계획으로 만든다.

## 작성 규칙

- 장면 묶음은 `data-start`·`data-duration`으로 선언하고, 일시정지한 GSAP 시간축 하나를 `window.__timelines["main"]`에 등록한다(공식 `hyperframes-core`).
- 움직임은 GSAP 트윈. Remotion의 spring 느낌이 필요하면 spring 식을 GSAP 사용자 ease로 넣는다.
- 목소리에 따라 움직이는 것(소리 막대, 깜박이는 커서, 들린 낱말)은 `ease: "none"` 구동 트윈 하나의 `onUpdate`에서 그린다.
- 소리: `<audio data-start data-duration data-volume>`, 자르기 `data-media-start`. 음악 크기 변화는 `data-automation` 볼륨 줄(값은 선형 배율)에 넣는다. 모노 목소리는 Remotion보다 3dB 크게 나온다([오디오](audio.md)).
- 나중에 들어오는 창·요소는 CSS에서 처음부터 숨기고(`opacity: 0`) 들어오는 시각에 `tl.set`으로 보인다. 화면 밖 좌표로만 숨기면 가장자리에 띠가 남는다. 시각 0의 `tl.set`으로 숨기면 lint가 경고한다.
- 전환 묶음에는 장면보다 높은 `z-index`를 준다. z-index가 없는 묶음은 쌓임 맥락을 만들지 않아 전환이 장면 뒤로 숨는다.
- `marginLeft` 같은 배치 속성을 트윈하지 않는다(lint 오류). transform이나 clip-path를 쓴다.
- 콜백 안에서 DOM 크기를 재지 않는다(lint 오류). 재야 할 것은 글 흐름 안에 두어 저절로 밀리게 한다.
- 키네틱 타이포는 낱말의 뜻을 움직임으로 보인다(「누릅니다」는 키처럼 눌림, 「멈춰도」는 달려와 급정거). 제목을 가운데 크게 말한 뒤 박에 맞춰 제자리로 보낸다. 자막은 말하는 낱말부터 밝힌다. 어디에 얼마나 쓸지는 5단계 디자인 컨셉을 따른다.

## 명령

```bash
source env.sh
python3 <스킬>/scripts/hyperframes/build.py . src/index.tpl
npx hyperframes lint                     # 쓰는 동안 자주
npx hyperframes check                    # 렌더 전 필수(lint 포함)
env -u GEMINI_API_KEY npx hyperframes snapshot --at 3,12,30   # 정지 그림 확인
npx hyperframes render --quality looks --output out/<이름>-raw.mp4
python3 <스킬>/scripts/encode.py out/<이름>-raw.mp4 out/<이름>.mp4   # −16 LUFS
```

- 5단계 대표 장면 정지 그림은 `snapshot`으로 만든다.
- 명령의 세부 옵션은 쓰는 판의 `hyperframes-cli` 스킬을 따른다.
