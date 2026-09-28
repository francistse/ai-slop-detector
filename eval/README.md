# `eval/` — test materials for the ai-slop-detector (id lab)

Everything used to build, calibrate and verify the detector lives here, so you
can review it. Laya was removed v1.1; this is a **Jev-only** pipeline.

## Layout

```
eval/
  README.md                 <- this index + honesty/naivety assessment
  TEST_PLAN.md              <- the test methodology (samples, metrics, CI)
  VERIFICATION.md           <- full report incl. per-case Jev scores (v3)
  gold/
    ai.jsonl                <- 20 AI cases (attributed: deepseek-v4-flash)
  raw/
    canto_human.jsonl       <- 28 real LIHKG comments (verbatim, with URLs)
    en_human.jsonl          <- 24 real Hacker News comments (verbatim, URLs)
  bench/
    PROMPTS.md              <- the 5 scoring-prompt variants, VERBATIM
    README_benchmark.md     <- AUROC / separation per variant per language
    V1_current_{zh,en}.json <- raw per-case scores (cached)
    V2_many_shot_*.json ...
    V3_definition_*.json ...
    V4_human_framed_*.json ...
    V5_anchored_scale_*.json ...
  build_ai_gold.py          <- regenerates gold/ai.jsonl
  run_eval.py               <- runs Jev over the gold -> out/cases.csv + report.md
  benchmark_prompts.py      <- the prompt-variant benchmark harness
  tune_thresholds.py        <- per-language threshold search (informational)
  ab_question_concreteness.py <- the A/B that proved concreteness > vague
  out/
    cases.csv               <- per-case Jev scores at shipped thresholds
    report.md               <- aggregate metrics
```

## How the pieces answer "is the detector any good?"

- `gold/ai.jsonl` + `raw/*.jsonl` = the **ground truth** (attribution-based:
  "human" = real forum writing; "ai" = text actually produced by a model).
- `bench/README_benchmark.md` = **which scoring prompt is best** (AUROC).
- `VERIFICATION.md` = the shipped result + per-case Jev scores.
- `ab_question_concreteness.py` = the experiment that showed vague rubric
  questions were hiding real signal (concreteness moved Canto-AI 0.37→0.59).

## ❗ Honesty / naivety assessment (you asked whether materials are too naive)

**This set is REAL (attribution-based, not synthetic or vibes) — that's its
strength.** But for a rigorous "best prompt" decision it is NOT a hard, diverse
benchmark, and absolute numbers are optimistically biased:

- **Human Cantonese (28):** most are *very short* one-liners (11–71 chars);
  only ~5 run 90–327 chars. Real and natural, but a scorer can trivially spot
  many as human (short / profane / opinionated). Being this short also flatters
  the "ambiguous-on-short" behavior.
- **Human English (24):** short punchy HN one-liners, same caveat.
- **AI Cantonese (12):** all **~91–169 chars** and *same-family* 思考哥 ragebait
  (reveal-trope + 「你話」 tail + hashtags). Realistic for the tool's actual
  use, but **uniform** — they share obvious tells, so separation looks easier
  than reality and AUROC is inflated. There is no *polished-but-humanized*
  Cantonese AI, and no long-form row.
- **AI English (8):** generic LLM paragraphs on tech/AI; easy, and small (8).
- **No neutral "hard" cases** — e.g. text judged differently by different
  humans, or deliberately adversarial humanized-AI that must be caught.

**What this means:** the benchmark is valid **comparatively** (same set for all
prompts → pick the winning prompt confidently), but **not** sufficient to claim
absolute real-world AUROC/accuracy. Before any external claim: add harder,
more diverse AI (incl. humanized/polished, non-ragebait, long-form) and longer
human samples, then hold out a subset for final measurement.

## Reproduce

```bash
# regen ai gold
python3 eval/build_ai_gold.py
# benchmark prompts (Jev, ~10 min, caches to bench/)
python3 eval/benchmark_prompts.py
# full eval at shipped thresholds
python3 eval/run_eval.py --gold gold/ai.jsonl --gold raw/canto_human.jsonl --gold raw/en_human.jsonl --out out
```
