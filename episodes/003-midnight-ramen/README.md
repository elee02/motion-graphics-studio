# 003 — Midnight Ramen

A 10-second cartoon scene, one continuous camera move: a rain-soaked ramen stall at 2 a.m.,
a cook, a hooded customer and a shop cat. Built entirely from Python — no meshes, textures,
HDRIs or sound files on disk.

**Deliverable:** `dist/midnight_ramen.mp4` — 1920×1080, 24 fps, 13.3 s, stereo, −14 LUFS.

## Render it

```bash
# 1. scene frames (Cycles OptiX GPU, 64 spp, ~10 s/frame)
./.blender_cache/blender/blender -b --factory-startup \
  -P episodes/003-midnight-ramen/shots/shot_01_midnight_ramen.py -- \
  --output "$PWD/episodes/003-midnight-ramen/renders/frames/frame_" --png \
  --frame-start 1 --frame-end 240 --res 1920 1080 --samples 64

# 2. score + cards
.venv/bin/python episodes/003-midnight-ramen/shots/score.py \
  --output episodes/003-midnight-ramen/renders/score.wav --duration 13.3
.venv/bin/python episodes/003-midnight-ramen/story/cards.py

# 3. master
.venv/bin/python episodes/003-midnight-ramen/story/master.py
```

Or through the studio pipeline (shot only, no cards):

```bash
make status  EP=003-midnight-ramen
make preview EP=003-midnight-ramen
make build   EP=003-midnight-ramen
```

The shot script also renders a single still (`--frame 120 --res 1280 720 --samples 32`) for
look-dev, and honours `RAMEN_GPU=0` to force CPU rendering.

## What is in the frame

- 400+ procedural objects: alley walls, kerbs, drain, puddles, pipes, AC unit, posters, ladder,
  vending machine, cables, lanterns, noren curtains, signboard, shelves, bottles, pot, bowls,
  chopsticks, cat cushion.
- Three characters, all primitive-built and posed by hand in code: the cook (bandana, apron,
  neck towel, moustache), the customer (hood, scarf, backpack, chopsticks), the cat.
- 230 rain streaks on individual loops, three steam cards with an animated noise shader that
  fades toward the top, a flickering sign, swaying lanterns.
- Cycles, AgX, bloom via the compositor; the only "texture" is procedural noise.

## Timing notes

Measured on this machine (RTX 4060 Laptop, OptiX): ~10 s per 1080p/64-sample frame, ~44 min for
the full 240 frames. CPU-only is roughly 3× slower.

## Credits

Written, modelled, lit, animated, scored and mastered in this repository. Fonts: Montserrat
(SIL OFL) for the cards. No third-party 3D assets are used in this episode.
