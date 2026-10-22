"""Make one voice line: python3 vo.py <outdir> <name> <voice_id> <text> <seed>
eleven_v3 at its steadiest (stability 1.0) with a fixed seed per voice, so every line of a voice sounds like the same
person (the default lets the voice drift from line to line). The text is sent with a trailing " ... 네." so the last
word is said to its end (the model often ends its file on the last letter), and the file is cut in the pause before
that "네", ending in a 50 ms fade (finish()).
Writes <name>.mp3, <name>.json (chars, words with times) and <name>-env.json (30 fps loudness 0..1).
Speed a line up: python3 vo.py --tempo 1.3 <src base> <dst base> [ffmpeg filter] (pitch kept: ffmpeg atempo on the
line with 0.3 s of silence after it, then the optional filter, cut again with finish(); times divided by the tempo).
The key is read from the environment variable ELEVENLABS_API_KEY; never print it.
A leading audio tag ("[cheerful] ...") is spoken as a tone, not as words: it is left out of the text and the times."""
import os, array, base64, json, math, pathlib, subprocess, sys, time, urllib.request


def key():
    k = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    return k or sys.exit("set ELEVENLABS_API_KEY")


def envelope(mp3, dst):
    """30 fps loudness of an mp3, 0..1, into dst."""
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp3), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    x = array.array("h", pcm)
    hop = 16000 // 30
    rms = [math.sqrt(sum(v * v for v in x[i:i + hop]) / max(1, len(x[i:i + hop]))) for i in range(0, len(x), hop)]
    top = max(rms) or 1
    dst.write_text(json.dumps([round(v / top, 3) for v in rms]), encoding="utf-8")


def finish(mp3, after):
    """Cut mp3 in the pause after the last word (its last letter starts at `after` seconds), found by ear, not by the
    alignment (it puts the trailing "네" too early): the first 80 ms all 34 dB under the loudest (a stop inside the
    word is shorter; 28 dB when the pause is breathy), faded out over its first 50 ms. No such pause in 1.5 s: an
    error, never a clipped word.
    Returns where the file now ends."""
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp3), "-ac", "1", "-ar", "44100", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    x, n = array.array("h", pcm), 441
    rms = [math.sqrt(sum(v * v for v in x[i:i + n]) / max(1, len(x[i:i + n]))) for i in range(0, len(x), n)]
    a = int(after * 100)
    run = lambda d: next((i for i in range(a, min(len(rms), a + 150) - 7) if all(r < (max(rms) or 1) * 10 ** (d / 20) for r in rms[i:i + 8])), None)
    i = run(-34)
    if i is None:  # a breathy pause: 28 dB under will do (the fade takes it under the check's 40)
        i = run(-28)
    if i is None:
        sys.exit(f"{mp3.name}: no pause after the last word")
    cut = i / 100 + 0.01
    tmp = mp3.with_name(mp3.stem + "-cut.mp3")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp3), "-t", f"{cut + 0.05:.3f}", "-af", f"afade=t=out:st={cut:.3f}:d=0.05",
                    "-c:a", "libmp3lame", "-b:a", "192k", str(tmp)], check=True)
    tmp.replace(mp3)
    return round(cut + 0.05, 4)


if sys.argv[1] == "--tempo":
    tempo, src, dst = float(sys.argv[2]), pathlib.Path(sys.argv[3]), pathlib.Path(sys.argv[4])
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src.with_suffix(".mp3")), "-filter:a", ",".join(["apad=pad_dur=0.3", f"atempo={tempo}"] + sys.argv[5:6]),
                    "-c:a", "libmp3lame", "-b:a", "192k", str(dst.with_suffix(".mp3"))], check=True)
    j = json.loads(src.with_suffix(".json").read_text(encoding="utf-8"))
    j["start"] = [round(s / tempo, 4) for s in j["start"]]
    j["end"] = [round(e / tempo, 4) for e in j["end"]]
    j["words"] = [[w, round(s / tempo, 4), round(e / tempo, 4)] for w, s, e in j["words"]]
    dst.with_suffix(".json").write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
    finish(dst.with_suffix(".mp3"), j["end"][-1])
    envelope(dst.with_suffix(".mp3"), dst.with_name(dst.name + "-env.json"))
    print(dst.name, round(j["end"][-1], 2), "s at", tempo)
    sys.exit()

out, name, vid, text, seed = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
out.mkdir(parents=True, exist_ok=True)
TAIL = " ... 네."  # said after the line and cut off: the line's last word is not clipped
body = {"text": text + TAIL, "model_id": "eleven_v3", "language_code": "ko", "voice_settings": {"stability": 1.0}, "seed": seed}
req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}/with-timestamps?output_format=mp3_44100_192",
                             data=json.dumps(body).encode(), headers={"xi-api-key": key(), "Content-Type": "application/json"})
for attempt in range(3):
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=180).read())
        break
    except urllib.error.HTTPError as e:
        sys.exit(f"{e.code} {e.read()[:300]}")
    except OSError:
        if attempt == 2:
            raise
        time.sleep(3)
mp3 = out / f"{name}.mp3"
mp3.write_bytes(base64.b64decode(r["audio_base64"]))
a = r.get("normalized_alignment") or r["alignment"]
chars, st, en = a["characters"], a["character_start_times_seconds"], a["character_end_times_seconds"]
tag = len(text) - len(text.split("] ", 1)[1]) if text.startswith("[") and "] " in text else 0
chars, st, en, text = chars[tag:], st[tag:], en[tag:], text[tag:]
chars, st, en = chars[:len(text)], st[:len(text)], en[:len(text)]  # the trailing words are not the line's
last = max(i for i, c in enumerate(chars) if c.isalnum())  # the last letter (the stop after it runs on into the pause)
stop = finish(mp3, st[last])
en = [min(e, stop) for e in en]
words, cur = [], None
for c, s, e in zip(chars, st, en):
    if c.isspace():
        cur = None
        continue
    if cur is None:
        cur = [c, s, e]
        words.append(cur)
    else:
        cur[0] += c
        cur[2] = e
(out / f"{name}.json").write_text(json.dumps({"text": text, "chars": chars, "start": st, "end": en, "words": words},
                                             ensure_ascii=False), encoding="utf-8")
envelope(mp3, out / f"{name}-env.json")
print(name, round(en[-1], 2), "s,", len(words), "words")
