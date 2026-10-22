"""HyperFrames starter: python3 build.py <video dir> [template]
Places the scenes on the music's beats and writes <dir>/index.html from the template (default: index.tpl next to this
script; copy it into the project and pass its path once you change it).

Reads
  <dir>/scenes.json  {"width": 1920, "height": 1080, "music": "assets/music/<song>.mp3", "music_volume": 0.081,
                      "scenes": [{"title": "<on-screen title>", "lines": ["<line id>", ...]}, ...]}
  <dir>/vo.json      from lines.py (voice files and word times)
  <dir>/beats.json   from beats.py run on the music
Beat plan: the first scene starts on beat 1; in a scene the title comes first, each line starts on the first beat at
least 0.4 s after the one before ends (the first line one beat after the title); the scene ends on the first even beat
at least 0.8 s after its last line; the next scene starts there. The music fades in over 20 frames and out over the
last 75. B(k) is beat k's frame, read between measured beats; ceilB(seconds) is the beats that cover a time.
Copies gsap.min.js from node_modules into assets/. The template gets the plan as JSON at /*DATA*/null, the scene
sections at <!--SCENES--> and the audio clips at <!--AUDIO-->."""
import html, json, math, pathlib, shutil, sys

FPS = 30
root = pathlib.Path(sys.argv[1]).resolve()
tpl = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path(__file__).resolve().parent / "index.tpl"
cfg = json.loads((root / "scenes.json").read_text(encoding="utf-8"))
VO = json.loads((root / "vo.json").read_text(encoding="utf-8"))
BEATS = json.loads((root / "beats.json").read_text(encoding="utf-8"))["beats"]
LAST = len(BEATS) - 1
BEAT = (BEATS[LAST] - BEATS[0]) / LAST


def beat_at(k):
    if k <= 0:
        return BEATS[0] + k * BEAT
    if k >= LAST:
        return BEATS[LAST] + (k - LAST) * BEAT
    i = math.floor(k)
    return BEATS[i] + (k - i) * (BEATS[i + 1] - BEATS[i])


def B(k):
    return math.floor(beat_at(k) * FPS + 0.5)


def ceilB(sec):
    return math.ceil(sec / BEAT - 1e-6)


def first_beat(k, sec):  # the first beat from k that is at or after `sec`
    while beat_at(k) < sec:
        k += 1
    return k


plan, k = [], 1
for s in cfg["scenes"]:
    start, at, lines, done = k, k + 1, [], beat_at(k + 1)
    for name in s["lines"]:
        v = VO[name]
        at = first_beat(at, done)
        f0 = B(at)
        lines.append({"id": name, "file": v["file"], "at": f0,
                      "words": [[w, f0 + round(a * FPS), f0 + round(b * FPS)] for w, a, b in v["words"]]})
        done = beat_at(at) + v["end"] + 0.4
    end = first_beat(at + 1, done + 0.4)
    end += end % 2
    plan.append({"title": s["title"], "start": B(start), "end": B(end), "lines": lines})
    k = end
frames = plan[-1]["end"] + FPS  # one second of quiet after the last scene
T = frames / FPS

sections = "\n".join(
    f'      <section id="s{i}" class="layer clip scene" data-start="{p["start"] / FPS:.4f}" data-duration="{(p["end"] - p["start"]) / FPS:.4f}" '
    f'data-track-index="{1 + i % 2}">\n        <h1 class="title">{html.escape(p["title"])}</h1>\n        <p class="cap"></p>\n      </section>'
    for i, p in enumerate(plan))
vol = cfg.get("music_volume", 0.081)
lane = {"version": 1, "lanes": [{"target": "volume", "points": [{"t": 0, "v": 0}, {"t": 20 / FPS, "v": vol}, {"t": (frames - 75) / FPS, "v": vol}, {"t": T, "v": 0}]}]}
audio = [f'<audio id="music" src="{cfg["music"]}" data-start="0" data-duration="{T:.4f}" data-automation=\'{json.dumps(lane)}\'></audio>']
audio += [f'<audio id="v{i}-{j}" src="{l["file"]}" data-start="{l["at"] / FPS:.4f}" data-volume="1"></audio>'
          for i, p in enumerate(plan) for j, l in enumerate(p["lines"])]

(root / "assets").mkdir(exist_ok=True)
shutil.copy2(root / "node_modules/gsap/dist/gsap.min.js", root / "assets/gsap.min.js")
page = tpl.read_text(encoding="utf-8")
page = (page.replace("__WIDTH__", str(cfg.get("width", 1920))).replace("__HEIGHT__", str(cfg.get("height", 1080)))
        .replace("__DURATION__", f"{T:.4f}").replace("<!--SCENES-->", sections)
        .replace("<!--AUDIO-->", "\n    ".join(audio))
        .replace("/*DATA*/null", json.dumps({"frames": frames, "scenes": plan}, ensure_ascii=False)))
(root / "index.html").write_text(page, encoding="utf-8")
print(f"{len(plan)} scenes, {T:.2f} s, {len(audio) - 1} voice clips")
