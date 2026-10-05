#!/usr/bin/env python3
"""Dependency-free sound design: synthesize SFX, a simple beat bed, and pads into a WAV.

Use it two ways:

1. CLI with a cue sheet (JSON):
       python3 sfx.py cues.json out/sfx.wav
   cues.json:
       {"duration": 35,
        "cues": [
          {"t": 0.4, "sound": "whoosh", "gain": 0.3, "dur": 0.6, "rising": true},
          {"t": 6.15, "sound": "hit", "gain": 0.5, "f": 45},
          {"t": 12.75, "sound": "chime", "gain": 0.3, "freqs": [1318.5, 1760]},
          {"t": 1.0, "sound": "keys", "gain": 0.2, "count": 30, "cps": 22}
        ],
        "beats": [{"start": 8.75, "end": 30.7, "bpm": 120, "kick": 0.42, "hat": 0.12, "bass": 0.2, "notes": [55, 55, 65.41, 49]}],
        "pads":  [{"start": 30.8, "end": 35, "freqs": [130.81, 196, 261.63], "gain": 0.05}]}

2. As a library from your own script:
       from sfx import Mix
       m = Mix(35); m.add(1.0, m.whoosh(.6), .3); m.write('out/sfx.wav')

Sounds: tone, noise, whoosh, hit, chime, pop, blip, tick, key/keys, slap, buzz, ring, kick, hat, riser.
Synthesized SFX are a fast default; for richer sound consider generated SFX/music (see references/audio-and-voice.md).
Mixing/loudness happens later in mix.py, so this file only peak-normalizes.
"""
import json, math, os, random, struct, sys, wave

SR = 48000


class Mix:
    def __init__(self, duration, seed=7):
        self.n = int(SR * duration)
        self.buf = [0.0] * self.n
        self.rnd = random.Random(seed)

    # ---------- placement ----------
    def add(self, t0, samples, gain=1.0):
        i0 = int(t0 * SR)
        buf, n = self.buf, self.n
        for k, v in enumerate(samples):
            i = i0 + k
            if 0 <= i < n:
                buf[i] += v * gain

    # ---------- building blocks ----------
    @staticmethod
    def env(n, attack, tau):
        a = max(1, int(attack * SR))
        return [(k / a if k < a else 1.0) * math.exp(-max(0, k - a) / (tau * SR)) for k in range(n)]

    def tone(self, f, dur, attack=.002, tau=.08, kind='sine', sweep=0.0):
        n = int(dur * SR); e = self.env(n, attack, tau); out = []; ph = 0.0
        for k in range(n):
            ph += 2 * math.pi * f * (1 + sweep * k / n) / SR
            v = math.sin(ph) if kind == 'sine' else (0.5 if math.sin(ph) > 0 else -0.5)
            out.append(v * e[k])
        return out

    def noise(self, dur, attack=.001, tau=.01, lp=.5):
        n = int(dur * SR); e = self.env(n, attack, tau); out = []; y = 0.0
        for k in range(n):
            y += lp * (self.rnd.uniform(-1, 1) - y)
            out.append(y * e[k])
        return out

    @staticmethod
    def mix(*parts):
        n = max(len(p) for p in parts)
        return [sum(p[k] for p in parts if k < len(p)) for k in range(n)]

    # ---------- named sounds ----------
    def whoosh(self, dur=.6, rising=True):
        n = int(dur * SR); out = []; y = 0.0
        for k in range(n):
            x = k / n; lp = .04 + .55 * ((x ** 2) if rising else ((1 - x) ** 2))
            y += lp * (self.rnd.uniform(-1, 1) - y)
            out.append(y * math.sin(math.pi * x))
        return out

    def riser(self, dur=1.2):
        return self.mix(self.whoosh(dur, True), self.tone(220, dur, dur * .9, 1.0, sweep=1.5))

    def hit(self, f=50):
        return self.mix(self.tone(f, 1.0, .002, .22, sweep=-.5), self.noise(.35, .001, .06, .35))

    def chime(self, freqs=(1046.5, 1318.5, 1568.0), dur=1.6, tau=.45):
        return self.mix(*[[v / (i + 1) for v in self.tone(f, dur, .003, tau)] for i, f in enumerate(freqs)])

    def pop(self, f=520):
        return self.tone(f, .09, .001, .03, sweep=.5)

    def blip(self, f=990):
        return self.tone(f, .07, .001, .025)

    def tick(self, hi=True):
        return self.mix(self.tone(3200 if hi else 2400, .03, .0005, .006), self.noise(.02, .0005, .003, .9))

    def key(self):
        return self.mix(self.noise(.03, .0005, .006, .7), [v * .3 for v in self.tone(self.rnd.uniform(1800, 2600), .02, .0005, .004)])

    def slap(self):
        return self.mix(self.noise(.12, .001, .03, .25), [v * .5 for v in self.tone(140, .1, .001, .03)])

    def buzz(self):
        return self.mix(self.tone(150, .3, .002, .1, 'square'), self.tone(159, .3, .002, .1, 'square'))

    def ring(self, dur=.6):
        n = int(dur * SR)
        return [(math.sin(2 * math.pi * 440 * k / SR) + math.sin(2 * math.pi * 480 * k / SR)) * .5
                * min(1, k / 600) * min(1, (n - k) / 600) for k in range(n)]

    def kick(self):
        return self.tone(110, .35, .001, .09, sweep=-.6)

    def hat(self):
        return self.noise(.06, .0005, .012, .95)

    # ---------- beds ----------
    def beat(self, start, end, bpm=120, kick=.4, hat=.12, bass=.2, notes=(55, 55, 65.41, 49)):
        step = 60 / bpm; t = start; i = 0
        k, h = self.kick(), self.hat()
        while t < end - .01:
            if kick: self.add(t, k, kick)
            if hat: self.add(t + step / 2, h, hat)
            if bass: self.add(t + step / 2, self.tone(notes[(i // 4) % len(notes)], .22, .003, .08), bass)
            t += step; i += 1

    def pad(self, start, end, freqs, gain=.05, attack=.8, release=1.2):
        i0, i1 = int(start * SR), min(self.n, int(end * SR))
        for i in range(i0, i1):
            t = (i - i0) / SR; rem = (i1 - i) / SR
            e = min(1, t / attack) * min(1, rem / release)
            v = sum(math.sin(2 * math.pi * f * t) + .5 * math.sin(2 * math.pi * f * 1.003 * t + j) for j, f in enumerate(freqs))
            self.buf[i] += v / len(freqs) * e * gain

    # ---------- output ----------
    def write(self, path, peak_db=-1.0):
        peak = max(abs(v) for v in self.buf) or 1
        scale = (10 ** (peak_db / 20)) / peak
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        with wave.open(path, 'wb') as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes(b''.join(struct.pack('<hh', s, s) for s in (int(max(-1, min(1, v * scale)) * 32767) for v in self.buf)))
        return path


def render_cues(spec):
    m = Mix(spec['duration'], spec.get('seed', 7))
    for c in spec.get('cues', []):
        s, t, g = c['sound'], c['t'], c.get('gain', .3)
        if s == 'keys':
            for i in range(c.get('count', 10)):
                m.add(t + i / c.get('cps', 20), m.key(), g)
            continue
        args = {k: v for k, v in c.items() if k not in ('t', 'sound', 'gain')}
        if s == 'chime' and 'freqs' in args: args['freqs'] = tuple(args['freqs'])
        m.add(t, getattr(m, s)(**args), g)
    for b in spec.get('beats', []):
        m.beat(**b)
    for p in spec.get('pads', []):
        m.pad(**p)
    return m


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(1)
    spec = json.load(open(sys.argv[1]))
    print('wrote', render_cues(spec).write(sys.argv[2]))
