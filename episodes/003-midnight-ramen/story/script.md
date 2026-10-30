# Episode 003 — Midnight Ramen

**Logline.** 2 a.m., a ramen stall at the end of a wet alley. The cook stirs, the cat
supervises, and a hooded stranger lifts her chopsticks. Nothing is explained; everything is warm.

**Format.** 10-second scene, one continuous camera move, no cuts. Delivered as a 13.3-second
master: title card → scene → end card, with a procedural score.

---

## Beat sheet

| Master time | Scene time | Beat |
| :--- | :--- | :--- |
| 0:00.0 | — | Title card over rain: **MIDNIGHT RAMEN**, episode 003 |
| 0:01.4 | 0:00.0 | Cross-fade into the wide alley. Rain, sign glow, the stall breathing. |
| 0:03.5 | 0:02.1 | Camera starts its push-in. Cook stirs the broth; steam curls. |
| 0:06.0 | 0:04.6 | Medium shot: the hooded customer in the left foreground, cook behind the counter. |
| 0:08.4 | 0:07.0 | The chopsticks lift toward the hood. The cook's head dips. The cat's tail flicks. |
| 0:12.4 | 0:11.0 | Over-the-counter two-shot; the ladle rests, the broth keeps steaming. |
| 0:12.4–0:13.3 | — | Cross-fade to the end card, score resolves. |

## Cast

- **The cook** — an old man in a red bandana, indigo apron and white neck towel. Closed eyes,
  big moustache, both hands busy: one stirs the pot, one rests on the counter.
- **The customer** — hooded, seen from behind. Teal jacket, amber scarf, overstuffed backpack,
  chopsticks in the right hand. We never see her face; the hood does the acting.
- **The shop cat** — ginger, on a folded cushion at the right end of the counter, tail up.
  The owner of the establishment, as far as anyone can prove.

## The set

A dead-end alley at 2 a.m.: wet asphalt, kerb and drain, three puddles, one vending machine
bleeding cyan, a violet-lit doorway down the right-hand gap, pipes and cables, a leaning
ladder, posters. The stall itself: counter with battens and apron, three indigo noren panels
with a crest, two paper lanterns, a signboard on the roof fascia, shelves of bottles, a menu
board, two hanging bulbs, a work light. 400+ objects, every one built by the script.

## Camera

One 50 mm lens, f/2.8, focus pulled to the cook's face. The move is a slow dolly from the alley
mouth (6.9 m out) to an over-the-counter two-shot (3.8 m), with equal parts of the customer's
hood and the cook's counter. A low-amplitude noise modifier on the camera rig keeps it from
feeling like a slider.

## Sound

Procedural, no samples: a stereo rain bed built from filtered noise, a low city rumble, a warm
four-chord pad (Cmaj9 → Am9 → Fmaj9 → G6/9) with a music-box line, a steam swell, a ladle
clink and a bowl set-down. Mixed and mastered to −14 LUFS for streaming.

## Palette

Warm tungsten 2700 K on the stall (`#FFB05C`), cold alley ambient (`#4D74D9`), violet doorway
(`#6B1AFA`), indigo cloth (`#081A33`). AgX, medium-high contrast, exposure +0.45.

## How it is built

```
shots/shot_01_midnight_ramen.py   scene, cast, lighting, camera, animation, render CLI
shots/score.py                    procedural score (numpy + scipy)
story/cards.py                    title and end cards (PIL)
story/master.py                   ffmpeg assembly -> dist/midnight_ramen.mp4
```

Nothing binary is tracked in Git: frames, cards, score and masters live under `renders/` and
`dist/`, both ignored.
