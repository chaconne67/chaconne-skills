<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=__WIDTH__, height=__HEIGHT__" />
    <title>Video</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      /* Starter look: replace with the chosen design concept (colors by role, type, motion).
         Put the font file at assets/fonts/main.woff2 (a Korean font, e.g. Pretendard, OFL). */
      @font-face { font-family: "Main"; src: url("assets/fonts/main.woff2") format("woff2"); font-display: block; }
      :root { --bg: #f6f4ee; --ink: #16161a; --muted: #8a8780; --accent: #ff7a2f; }
      body { margin: 0; background: var(--bg); font-family: "Main", sans-serif; word-break: keep-all; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; background: var(--bg); color: var(--ink); }
      .layer { position: absolute; inset: 0; }
      .scene { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 64px; padding: 0 140px; box-sizing: border-box; background: var(--bg); opacity: 0; }
      .title { margin: 0; font-size: 96px; font-weight: 800; letter-spacing: -0.03em; line-height: 1.15; text-align: center; }
      .cap { margin: 0; min-height: 2.9em; font-size: 44px; font-weight: 600; line-height: 1.45; text-align: center; color: var(--muted); }
      .cap span.on { color: var(--ink); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="__WIDTH__" data-height="__HEIGHT__" data-duration="__DURATION__">
<!--SCENES-->
      <!--AUDIO-->
    </div>

    <script>
      const D = /*DATA*/null;
      const FPS = 30, sec = (f) => f / FPS;
      const tl = gsap.timeline({ paused: true });

      // each scene: fades in on its first beat, the title rises in, the caption shows the scene's words
      D.scenes.forEach((s, i) => {
        const el = document.getElementById("s" + i);
        el.querySelector(".cap").innerHTML = s.lines.flatMap((l) => l.words.map(([w]) => `<span>${w}</span>`)).join(" ");
        tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: sec(8), ease: "power1.out", immediateRender: false }, sec(s.start));
        tl.fromTo(el.querySelector(".title"), { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: sec(18), ease: "power3.out", immediateRender: false }, sec(s.start + 2));
      });

      // karaoke caption: a word lights up when it is said (one driver tween draws voice-driven state)
      const words = D.scenes.map((s, i) => ({ spans: [...document.getElementById("s" + i).querySelectorAll(".cap span")], times: s.lines.flatMap((l) => l.words.map((w) => w[1])) }));
      const driver = { t: 0 };
      tl.to(driver, { t: D.frames / FPS, duration: D.frames / FPS, ease: "none", onUpdate: () => {
        const F = Math.round(driver.t * FPS);
        words.forEach(({ spans, times }) => spans.forEach((sp, k) => sp.classList.toggle("on", F >= times[k])));
      } }, 0);

      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
