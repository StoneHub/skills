#!/usr/bin/env python3
"""Final audio mix + mux: duck the bed under the voice, loudness-normalize, attach to the video.

    python3 mix.py --video out/video-silent.mp4 --out promo.mp4 \
        [--voice vo/voice.wav] [--sfx out/sfx.wav] [--music music.mp3 --music-gain 0.35] \
        [--lufs -14] [--duck 8]

- Any of voice / sfx / music may be omitted (at least one is needed).
- When there is a voice, sfx+music are side-chain compressed under it so narration stays clear.
- Loudness defaults to -14 LUFS integrated, -1.5 dBTP: a common target for social/web video.
  Use -16 for podcasts/YouTube-quiet, -23/-24 for broadcast deliverables.
- Output length follows the video.
"""
import argparse, subprocess, sys

p = argparse.ArgumentParser()
p.add_argument('--video', required=True); p.add_argument('--out', required=True)
p.add_argument('--voice'); p.add_argument('--sfx'); p.add_argument('--music')
p.add_argument('--voice-gain', type=float, default=1.0)
p.add_argument('--sfx-gain', type=float, default=1.0)
p.add_argument('--music-gain', type=float, default=0.35)
p.add_argument('--lufs', type=float, default=-14.0)
p.add_argument('--duck', type=float, default=8.0, help='side-chain ratio; higher = bed drops further under voice')
a = p.parse_args()

dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', a.video],
                           capture_output=True, text=True, check=True).stdout.strip())
inputs, chains, bed = ['-i', a.video], [], []
fmt = 'aformat=sample_rates=48000:channel_layouts=stereo'
idx = 1
for name, path, gain in (('sfx', a.sfx, a.sfx_gain), ('music', a.music, a.music_gain)):
    if path:
        inputs += ['-i', path]
        chains.append(f'[{idx}:a]{fmt},volume={gain},apad,atrim=0:{dur}[{name}]'); bed.append(f'[{name}]'); idx += 1
voice = None
if a.voice:
    inputs += ['-i', a.voice]
    chains.append(f'[{idx}:a]{fmt},volume={a.voice_gain},apad,atrim=0:{dur}[voice]'); voice = '[voice]'; idx += 1
if not bed and not voice:
    sys.exit('nothing to mix: pass --voice, --sfx and/or --music')

if bed:
    chains.append(f"{''.join(bed)}amix=inputs={len(bed)}:normalize=0[bed]" if len(bed) > 1 else f'{bed[0]}anull[bed]')
if bed and voice:
    chains.append('[voice]asplit=2[vkey][vmain]')
    chains.append(f'[bed][vkey]sidechaincompress=threshold=0.02:ratio={a.duck}:attack=15:release=350:makeup=1[ducked]')
    chains.append('[ducked][vmain]amix=inputs=2:normalize=0[pre]')
else:
    chains.append(('[bed]' if bed else '[voice]') + 'anull[pre]')
chains.append(f'[pre]loudnorm=I={a.lufs}:TP=-1.5:LRA=11,{fmt}[aout]')

cmd = ['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', ';'.join(chains),
       '-map', '0:v', '-map', '[aout]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
       '-t', f'{dur}', '-movflags', '+faststart', a.out]
subprocess.run(cmd, check=True)
print('wrote', a.out)
