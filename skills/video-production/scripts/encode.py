"""Final encode: python3 encode.py <in.mp4> <out.mp4>
Meets the Microsoft Store trailer spec and suits YouTube and app stores: H.264 High, closed GOP of 15 frames, 2 B-frames, AAC-LC 384k 48 kHz stereo,
no edit list, faststart; loudness -16 LUFS (two-pass loudnorm)."""
import json, subprocess, sys

src, out = sys.argv[1], sys.argv[2]
norm = "loudnorm=I=-16:TP=-1.5:LRA=11"
log = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", norm + ":print_format=json", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
m = json.loads(log[log.rindex("{"):log.rindex("}") + 1])
af = (f"{norm}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
      f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", af, "-c:v", "libx264", "-profile:v", "high", "-preset", "slow",
                "-crf", "16", "-maxrate", "40M", "-bufsize", "80M", "-g", "15", "-keyint_min", "15", "-sc_threshold", "0",
                "-bf", "2", "-flags", "+cgop", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "384k", "-ar", "48000", "-ac", "2",
                "-use_editlist", "0", "-movflags", "+faststart", out], check=True)
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", out, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
print(out, [l.strip() for l in r.splitlines() if l.strip().startswith(("I:", "LRA:"))][-2:])
