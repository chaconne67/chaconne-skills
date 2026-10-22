# 제작: Remotion

제품 스토어 영상과 사용법 시리즈를 만든 경로다. 이미 Remotion으로 만든 프로젝트를 잇거나 앱의 React 부품을 가져와야 할 때 쓴다. 새 영상은 기본적으로 [HyperFrames](production-hyperframes.md)로 만든다.

## 준비

- Node v22, remotion·@remotion/cli 4.0.x, react 19(`package-lock.json`으로 판 고정). 설치는 `npm ci`.
- Remotion은 회사 규모에 따라 사용권 조건이 다르다(작은 회사는 무료). 쓰기 전에 현재 사용권 조건을 확인한다.
- 장면 등록: `src/Root.jsx`에 `<Composition id=… width height fps=30 durationInFrames>`. 여러 편은 배열을 돌며 `${id}-${slug}`로 등록한다.
- 글꼴: `src/index.js`에서 프로젝트 글꼴 파일(예: `public/fonts/PretendardVariable.woff2`)을 불러온다.

## 나눠 두는 것

| 영상마다 그대로 쓴다 | 제품마다 새로 만든다 |
|---|---|
| 이 스킬의 `scripts/`(`lines.py`·`vo.py`·`beats.py`·`encode.py`) | 앱 모양 부품(로고·창·키보드 등 미니어처) |
| 박자 함수(`beatAt`·`B`·`ceilB`), 목소리에 맞춰 글자가 써지는 부품, 전환 부품, 끝 카드 | 설정 창 같은 제품 화면, 편 정의와 내용 |
| 박자 계획(`plan`·`stepPlan`)과 커서 | 대사 파일·음성 색인, 음악·효과음·그림 |

## 순서

1. 대사: 대사 파일(`lines.json`)에 줄을 쓰고, 편 정의에 그 줄을 배정한다.
2. 음성: `python3 <스킬>/scripts/lines.py <영상 작업 폴더> [줄 id…]` → 음성 파일과 색인(`vo.json`). 렌더 전에 먼저 돌린다(음성 파일이 없으면 박자 계획이 오류를 낸다). Remotion은 `public/` 아래 파일만 읽으므로 `assets/`를 `public/`으로 두거나 연결한다.
3. 박자 지도: 곡을 바꿀 때만 `python3 <스킬>/scripts/beats.py <곡.mp3> > src/music-beats.json`.
4. 렌더: `npx remotion render src/index.js <composition id> out/<이름>-raw.mp4 --codec=h264 --crf=18`.
5. 인코딩: `python3 <스킬>/scripts/encode.py out/<이름>-raw.mp4 out/<이름>.mp4`(−16 LUFS).

## 디자인 값의 예 (새 영상은 5단계 컨셉으로 정한다)

- 30fps. `wordBreak: keep-all`.
- 전환(길이/화면을 덮는 시점, 프레임): shutter 28/0, swell 29/16, pill 42/22, roll 36/30, slam 44/29, stripes 27/24.
- spring 기본 damping 18·stiffness 160·mass 0.9. 글자 14/260, 창 이동 24/120. 이징 `(0.16,1,0.3,1)`, `(0.7,0,0.3,1)`.
- 박자 계획: 단계 제목 → 작동은 제목 길이 + 0.5초를 박으로 올림, 받아쓰기는 키 누름 다음 박에 말 시작, 단계 끝은 짝수 박.
