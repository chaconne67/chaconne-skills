"""Voice every line of a video: python3 lines.py <video dir> [line ids: only those]
Reads <dir>/voices.json and <dir>/lines.json, makes each line that changed with vo.py (next to this script) into
<dir>/assets/vo/<voice>/, and writes the index <dir>/vo.json that the video reads.

voices.json  {"tone": "[cheerful] ", "tempo": 1.3,
              "voices": {"<name>": {"id": "<ElevenLabs voice id>", "seed": 1101}, ...}}
lines.json   {"<line id>": {"voice": "<name>", "t": "<text>", "fast": true}, ...}
             fast: played at voices.json "tempo" (narration); leave it out for lines said at their own speed (demos).
             {"from": "<line id>", "af": [tempo, "<ffmpeg filter>"]} instead of "t": the same take changed by ffmpeg
             (a line heard several times sounds like one person only when it is one take).
vo.json      {"<line id>": {"text", "voice", "file": path from <dir>, "words": [[word, start, end]], "end": seconds,
              "env": [30 fps loudness 0..1]}}
A line is made again when its text, voice, seed, tone or MAKE changes. Needs ELEVENLABS_API_KEY in the environment."""
import json, pathlib, subprocess, sys

MAKE = 1  # raise when vo.py changes how a line is made, so every line is made again
HERE = pathlib.Path(__file__).resolve().parent
root = pathlib.Path(sys.argv[1]).resolve()
only = set(sys.argv[2:])
cfg = json.loads((root / "voices.json").read_text(encoding="utf-8"))
lines = json.loads((root / "lines.json").read_text(encoding="utf-8"))
index_path = root / "vo.json"
index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}
tone, tempo = cfg.get("tone", ""), cfg.get("tempo", 1.0)
mtime = lambda p: p.stat().st_mtime if p.exists() else 0
vo = lambda *a: subprocess.run([sys.executable, str(HERE / "vo.py"), *map(str, a)], check=True)


def make(name, line):
    v = cfg["voices"][line["voice"]]
    out = root / "assets/vo" / line["voice"]
    src = out / name
    made = index.get(name, {})
    if "from" in line:  # the same take, changed by ffmpeg
        base = out / line["from"]
        if mtime(src.with_suffix(".mp3")) < mtime(base.with_suffix(".mp3")):
            vo("--tempo", line["af"][0], base, src, *line["af"][1:])
    elif not (made.get("text") == line["t"] and made.get("voice_id") == v["id"] and made.get("seed") == v["seed"]
              and made.get("tone") == tone and made.get("make") == MAKE and src.with_suffix(".mp3").exists()):
        vo(out, name, v["id"], tone + line["t"], v["seed"])
    if line.get("fast") and tempo != 1.0:
        dst = out / str(tempo) / name
        if mtime(dst.with_suffix(".mp3")) < mtime(src.with_suffix(".mp3")):
            vo("--tempo", tempo, src, dst)
        src = dst
    j = json.loads(src.with_suffix(".json").read_text(encoding="utf-8"))
    env = json.loads(src.with_name(src.name + "-env.json").read_text(encoding="utf-8"))
    return {"text": j["text"], "voice": line["voice"], "voice_id": v["id"], "seed": v["seed"], "tone": tone, "make": MAKE,
            "file": src.with_suffix(".mp3").relative_to(root).as_posix(), "words": j["words"], "end": j["end"][-1], "env": env}


new = {}
for name, line in lines.items():
    if only and name not in only and name in index:
        new[name] = index[name]
        continue
    new[name] = make(name, line)
index_path.write_text(json.dumps(new, ensure_ascii=False), encoding="utf-8")
print(len(new), "lines")
