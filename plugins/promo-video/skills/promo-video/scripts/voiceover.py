#!/usr/bin/env python3
"""Generate a voiceover track plus timing data the animation can sync to.

    python3 voiceover.py script.json vo/            # synthesize every line
    python3 voiceover.py --list-voices [--provider elevenlabs|say]
    python3 voiceover.py --list-models              # ElevenLabs models available to this key

script.json:
    {"provider": "elevenlabs",            # or "say" (macOS, free, robotic: good for draft timing only)
     "voice": "<voice_id or say voice name>",
     "model": "eleven_multilingual_v2",   # check --list-models; newer/more expressive models appear over time
     "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.2, "speed": 1.0},
     "duration": 35,                      # total timeline length (optional; defaults to end of last line + 1 s)
     "gap": 0.25,                         # pause between lines that have no explicit start
     "lines": [
        {"id": "hook",  "text": "They never say T-B-I.", "start": 6.9},
        {"id": "catch", "text": "They say they hit their head."}
     ]}

Outputs in the target folder:
    line-<id>.wav     each line as 48 kHz mono WAV
    voice.wav         all lines placed on one timeline (feed to mix.py)
    voice.json        {"duration", "lines": {id: {"start", "end", "text", "words": [{"w", "start", "end"}]}}}
    voice.js          window.VOICE = <voice.json>; include it in the page to drive scene timing and captions

ElevenLabs needs ELEVENLABS_API_KEY in the environment. Never hard-code or log the key.
Word times come from ElevenLabs character alignment; for "say" they are estimated by character count.
"""
import base64, json, os, shutil, subprocess, sys, tempfile, urllib.request, urllib.error, wave, struct

API = 'https://api.elevenlabs.io'
SR = 48000


def die(msg):
    print(msg, file=sys.stderr); sys.exit(1)


def el_request(method, path, body=None):
    key = os.environ.get('ELEVENLABS_API_KEY')
    if not key:
        die('ELEVENLABS_API_KEY is not set. Export it in your shell (do not paste it into chat or commit it).')
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={'xi-api-key': key, 'Content-Type': 'application/json', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        die(f'ElevenLabs {e.code}: {e.read().decode(errors="replace")[:500]}')


def to_wav(src, dst):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-ac', '1', '-ar', str(SR), '-c:a', 'pcm_s16le', dst], check=True)


def wav_duration(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def words_from_alignment(al, offset=0.0):
    """Group ElevenLabs per-character alignment into words with start/end seconds."""
    words, cur, s, e = [], '', None, None
    for ch, cs, ce in zip(al['characters'], al['character_start_times_seconds'], al['character_end_times_seconds']):
        if ch.isspace():
            if cur: words.append({'w': cur, 'start': round(s + offset, 3), 'end': round(e + offset, 3)})
            cur, s = '', None
            continue
        if s is None: s = cs
        cur += ch; e = ce
    if cur: words.append({'w': cur, 'start': round(s + offset, 3), 'end': round(e + offset, 3)})
    return words


def estimated_words(text, dur, offset=0.0):
    toks = text.split(); total = sum(len(t) + 1 for t in toks) or 1; t = 0.0; out = []
    for tok in toks:
        d = dur * (len(tok) + 1) / total
        out.append({'w': tok, 'start': round(offset + t, 3), 'end': round(offset + t + d, 3)}); t += d
    return out


def synth_elevenlabs(spec, line, prev_text, next_text, tmp):
    body = {'text': line['text'], 'model_id': spec.get('model', 'eleven_multilingual_v2')}
    if spec.get('voice_settings'): body['voice_settings'] = spec['voice_settings']
    if prev_text: body['previous_text'] = prev_text   # keeps intonation continuous across separately generated lines
    if next_text: body['next_text'] = next_text
    if 'seed' in spec: body['seed'] = spec['seed']
    res = el_request('POST', f"/v1/text-to-speech/{spec['voice']}/with-timestamps?output_format=mp3_44100_128", body)
    mp3 = os.path.join(tmp, f"{line['id']}.mp3")
    open(mp3, 'wb').write(base64.b64decode(res['audio_base64']))
    return mp3, res.get('alignment') or res.get('normalized_alignment')


def synth_say(spec, line, tmp):
    if not shutil.which('say'): die('"say" is macOS-only; use provider "elevenlabs" or add another provider.')
    aiff = os.path.join(tmp, f"{line['id']}.aiff")
    cmd = ['say', '-o', aiff]
    if spec.get('voice'): cmd += ['-v', spec['voice']]
    if spec.get('rate'): cmd += ['-r', str(spec['rate'])]
    subprocess.run(cmd + [line['text']], check=True)
    return aiff, None


def read_mono(path):
    with wave.open(path) as w:
        raw = w.readframes(w.getnframes())
    return struct.unpack('<%dh' % (len(raw) // 2), raw)


def build(spec_path, out_dir):
    spec = json.load(open(spec_path))
    provider = spec.get('provider', 'elevenlabs')
    os.makedirs(out_dir, exist_ok=True)
    lines = spec['lines']; gap = spec.get('gap', .25)
    result = {'provider': provider, 'lines': {}}
    cursor = spec.get('lead_in', .3)
    with tempfile.TemporaryDirectory() as tmp:
        for i, line in enumerate(lines):
            if provider == 'elevenlabs':
                src, al = synth_elevenlabs(spec, line, lines[i - 1]['text'] if i else None,
                                           lines[i + 1]['text'] if i + 1 < len(lines) else None, tmp)
            elif provider == 'say':
                src, al = synth_say(spec, line, tmp)
            else:
                die(f'unknown provider {provider}')
            dst = os.path.join(out_dir, f"line-{line['id']}.wav")
            to_wav(src, dst)
            dur = wav_duration(dst)
            start = line.get('start', cursor)
            words = words_from_alignment(al, start) if al else estimated_words(line['text'], dur, start)
            result['lines'][line['id']] = {'text': line['text'], 'start': round(start, 3), 'end': round(start + dur, 3),
                                           'words': words, 'timing': 'aligned' if al else 'estimated'}
            cursor = start + dur + gap
            print(f"{line['id']:>12}  {start:6.2f}s → {start + dur:6.2f}s  {line['text'][:60]}")
    duration = spec.get('duration') or max(l['end'] for l in result['lines'].values()) + 1
    result['duration'] = duration
    # place every line on one timeline
    track = [0] * int(duration * SR)
    for lid, l in result['lines'].items():
        samples = read_mono(os.path.join(out_dir, f'line-{lid}.wav')); i0 = int(l['start'] * SR)
        for k, v in enumerate(samples):
            if i0 + k < len(track): track[i0 + k] = max(-32768, min(32767, track[i0 + k] + v))
    with wave.open(os.path.join(out_dir, 'voice.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(struct.pack('<%dh' % len(track), *track))
    json.dump(result, open(os.path.join(out_dir, 'voice.json'), 'w'), indent=1)
    open(os.path.join(out_dir, 'voice.js'), 'w').write('window.VOICE = ' + json.dumps(result) + ';\n')
    overlaps = [(a, b) for a, b in zip(list(result['lines'].values()), list(result['lines'].values())[1:]) if b['start'] < a['end']]
    if overlaps: print(f'warning: {len(overlaps)} line(s) overlap the previous one; adjust "start" values')
    if duration < max(l['end'] for l in result['lines'].values()): print('warning: voice runs past "duration"')
    print(f'wrote {out_dir}/voice.wav, voice.json, voice.js ({duration:.2f}s)')


def list_voices(provider):
    if provider == 'say':
        print(subprocess.run(['say', '-v', '?'], capture_output=True, text=True).stdout); return
    for v in el_request('GET', '/v1/voices').get('voices', []):
        labels = ', '.join(f'{k}: {val}' for k, val in (v.get('labels') or {}).items())
        print(f"{v['voice_id']}  {v['name']:<24} {labels}")


def list_models():
    for m in el_request('GET', '/v1/models'):
        print(f"{m['model_id']:<28} {m.get('name', '')}  — {(m.get('description') or '')[:90]}")


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] in ('-h', '--help'): print(__doc__); sys.exit(0)
    if a[0] == '--list-voices':
        list_voices(a[2] if len(a) > 2 and a[1] == '--provider' else 'elevenlabs')
    elif a[0] == '--list-models':
        list_models()
    else:
        build(a[0], a[1] if len(a) > 1 else 'vo')
