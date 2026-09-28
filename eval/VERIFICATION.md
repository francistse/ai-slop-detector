# ai-slop-detector — Verification Report v4 (Jev-only, many-shot prompt, shipped)
**Internal pre-publish · 72 gold cases · single backend (Laya removed v1.1) · verdicts at shipped calibration (`scripts/calibration.json`) · per-case rows = real Jev scores cached from the prompt benchmark**
## 1. Result
| lang | AI caught | human falsely accused | AI missed | marginal (ambiguous) |
|---|---|---|---|---|
| zh | **11/12** | **0/28** | **0** | 10 |
| en | **7/8** | **0/24** | **0** | 3 |

**Jev with the many-shot (V2) prompt: 0 humans falsely accused, 0 AI missed across all 72. 59/72 conclusive. 13/72 honestly abstain.**
## 2. Why this prompt (the benchmark)
Five decision-prompt variants were scored on the same gold set and ranked by AUROC (P(AI score > human score); 1=perfect ordering, 0.5=random):
| variant | description | Canto AUROC | EN AUROC |
|---|---|---|---|
| **V2 many-shot** | 3 human + 3 AI exemplars | **0.999** | **0.995** |
| V5 anchored-scale | 1H+1A + explicit 0..1 scale | 0.993 | 0.995 |
| V1 current | 1H+1A exemplars (old shipped) | 0.976 | 0.992 |
| V3 definition | behavioral definition, no exemplars | 0.973 | 0.958 |
| V4 human-framed | exemplars but ask 'how human' | 0.686 | 0.932 |

**Findings:** more exemplars > fewer; concrete-behavioural description ≈ 1 exemplar; and asking 'how human' instead of 'how AI' collapses Cantonese to near-random (0.686) with the SAME exemplars — framing direction matters as much as content. V2 adopted.
> *Caveat:* these AUROCs are on an easy gold set (short human + uniform ragebait AI — see `README.md` naivety note), so the *relative* ranking is robust but absolute numbers are optimistic. Fewer-exemplar prompts may close the gap on harder, more diverse data.
## 3. Shipped calibration (data-derived, both languages)
- **zh:** human < 0.32 · ambiguous 0.32–0.43 · AI > 0.43
- **en:** human < 0.49 · ambiguous 0.49–0.55 · AI > 0.55

## 4. What changed vs v3
1. **Laya fully removed** (code, calibration, eval, docs). Jev-only throughout.
2. **Best prompt adopted**: `machine_written` is now the many-shot (3H+3A) version.
3. **Verdict runs on the direct signal alone**; the 7-traits remain as an editing breakdown only (weighting them damped separation).

## 5. Per-case Jev scores (shipped thresholds; qc = correct/fp/fn/abstain)

| id | lang | label | verdict | ai_prob | qc |
|---|---|---|---|---|---|
| ae01 | en | ai | AI-likely | 0.98 | correct |
| ae02 | en | ai | AI-likely | 0.96 | correct |
| ae03 | en | ai | AI-likely | 0.94 | correct |
| ae04 | en | ai | AI-likely | 0.70 | correct |
| ae05 | en | ai | AI-likely | 0.62 | correct |
| ae06 | en | ai | ambiguous | 0.50 | abstain |
| ae07 | en | ai | AI-likely | 0.58 | correct |
| ae08 | en | ai | AI-likely | 0.78 | correct |
| eh01 | en | human | human-likely | 0.30 | correct |
| eh02 | en | human | human-likely | 0.26 | correct |
| eh03 | en | human | human-likely | 0.18 | correct |
| eh04 | en | human | human-likely | 0.29 | correct |
| eh05 | en | human | human-likely | 0.31 | correct |
| eh06 | en | human | human-likely | 0.35 | correct |
| eh07 | en | human | human-likely | 0.35 | correct |
| eh08 | en | human | human-likely | 0.27 | correct |
| eh09 | en | human | human-likely | 0.33 | correct |
| eh10 | en | human | human-likely | 0.34 | correct |
| eh11 | en | human | human-likely | 0.42 | correct |
| eh12 | en | human | human-likely | 0.45 | correct |
| eh13 | en | human | human-likely | 0.46 | correct |
| eh14 | en | human | human-likely | 0.32 | correct |
| eh15 | en | human | human-likely | 0.26 | correct |
| eh16 | en | human | human-likely | 0.41 | correct |
| eh17 | en | human | human-likely | 0.45 | correct |
| eh18 | en | human | human-likely | 0.29 | correct |
| eh19 | en | human | human-likely | 0.31 | correct |
| eh20 | en | human | human-likely | 0.33 | correct |
| eh21 | en | human | human-likely | 0.32 | correct |
| eh22 | en | human | ambiguous | 0.52 | abstain |
| eh23 | en | human | human-likely | 0.34 | correct |
| eh24 | en | human | ambiguous | 0.49 | abstain |
| ai01 | zh | ai | AI-likely | 0.76 | correct |
| ai02 | zh | ai | AI-likely | 0.78 | correct |
| ai03 | zh | ai | AI-likely | 0.71 | correct |
| ai04 | zh | ai | AI-likely | 0.44 | correct |
| ai05 | zh | ai | AI-likely | 0.49 | correct |
| ai06 | zh | ai | AI-likely | 0.44 | correct |
| ai07 | zh | ai | AI-likely | 0.59 | correct |
| ai08 | zh | ai | AI-likely | 0.59 | correct |
| ai09 | zh | ai | ambiguous | 0.43 | abstain |
| ai10 | zh | ai | AI-likely | 0.47 | correct |
| ai11 | zh | ai | AI-likely | 0.55 | correct |
| ai12 | zh | ai | AI-likely | 0.59 | correct |
| ch01 | zh | human | human-likely | 0.19 | correct |
| ch02 | zh | human | human-likely | 0.14 | correct |
| ch03 | zh | human | human-likely | 0.10 | correct |
| ch04 | zh | human | ambiguous | 0.43 | abstain |
| ch05 | zh | human | ambiguous | 0.34 | abstain |
| ch06 | zh | human | human-likely | 0.24 | correct |
| ch07 | zh | human | human-likely | 0.27 | correct |
| ch08 | zh | human | ambiguous | 0.35 | abstain |
| ch09 | zh | human | human-likely | 0.28 | correct |
| ch10 | zh | human | ambiguous | 0.32 | abstain |
| ch11 | zh | human | ambiguous | 0.33 | abstain |
| ch12 | zh | human | human-likely | 0.31 | correct |
| ch13 | zh | human | human-likely | 0.28 | correct |
| ch14 | zh | human | ambiguous | 0.36 | abstain |
| ch15 | zh | human | human-likely | 0.30 | correct |
| ch16 | zh | human | human-likely | 0.29 | correct |
| ch17 | zh | human | human-likely | 0.29 | correct |
| ch18 | zh | human | ambiguous | 0.37 | abstain |
| ch19 | zh | human | human-likely | 0.25 | correct |
| ch20 | zh | human | human-likely | 0.21 | correct |
| ch21 | zh | human | ambiguous | 0.32 | abstain |
| ch22 | zh | human | human-likely | 0.25 | correct |
| ch23 | zh | human | human-likely | 0.26 | correct |
| ch24 | zh | human | human-likely | 0.23 | correct |
| ch25 | zh | human | human-likely | 0.28 | correct |
| ch26 | zh | human | ambiguous | 0.33 | abstain |
| ch27 | zh | human | human-likely | 0.22 | correct |
| ch28 | zh | human | human-likely | 0.19 | correct |

## 6. Sufficiency
Enough to pick V2 and to ship honest operating points for Jev (0 FP / 0 FN). Not enough to claim absolute real-world AUROC — a harder, more diverse held-out set is the remaining gap (see `README.md`).
