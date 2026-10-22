"""The background music's beats: python3 beats.py <mp3> [min BPM] [max BPM] > beats.json
A song's tempo can drift (one track ran from about 111 to 105 BPM), so the video follows its beats one by
one, not a fixed grid: onset strength (log energy rise, 5 ms hops), the period from its autocorrelation, then dynamic
programming beat tracking (Ellis 2007): each beat is an onset whose distance from the one before stays near the period.
Writes {"period": seconds, "beats": [seconds]}. The BPM range defaults to 90-130."""
import array, json, math, subprocess, sys

SR, HOP = 11025, 55
FPS = SR / HOP
x = array.array("h", subprocess.run(["ffmpeg", "-v", "error", "-i", sys.argv[1], "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                                    capture_output=True, check=True).stdout)
e = [math.log1p(sum(v * v for v in x[i:i + HOP]) / HOP) for i in range(0, len(x) - HOP, HOP)]
o = [0.0] + [max(0.0, e[i] - e[i - 1]) for i in range(1, len(e))]
m = sum(o) / len(o)
c = [v - m for v in o]
# the beat period: the strongest autocorrelation in the BPM range (outside it the eighths or half bars win)
LO, HI = (float(sys.argv[2]), float(sys.argv[3])) if len(sys.argv) > 3 else (90, 130)
lags = range(int(FPS * 60 / HI), int(FPS * 60 / LO))
ac = {lag: sum(c[i] * c[i + lag] for i in range(0, len(c) - lag, 2)) for lag in lags}
p = max(ac, key=ac.get)
# dynamic programming: score[t] = onset[t] + best score[prev] less a penalty for straying from the period
penalty = {d: 400 * math.log(d / p) ** 2 * m for d in range(p // 2, 2 * p + 1)}  # by distance in hops
score, back = [0.0] * len(o), [-1] * len(o)
for t in range(len(o)):
    best, arg = 0.0, -1
    for prev in range(max(0, t - 2 * p), t - p // 2):
        s = score[prev] - penalty[t - prev]
        if s > best:
            best, arg = s, prev
    score[t], back[t] = o[t] + best, arg
t = max(range(len(o) - p, len(o)), key=lambda i: score[i])
beats = []
while t >= 0:
    beats.append(round(t / FPS, 4))
    t = back[t]
beats.reverse()
print(json.dumps({"period": round(p / FPS, 4), "beats": beats}))
