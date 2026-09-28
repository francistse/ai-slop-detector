# Prompt-variant benchmark (Jev, N=72)
Each variant is a single Noul scored on every case. Headline = **AUROC** (P(AI score > human score)); 1.0 = perfect ordering, 0.5 = random. V4 is inverted (we use 1 - 'human' score).
| variant | lang | human mean | AI mean | gap | AUROC |
|---|---|---|---|---|---|
| V1_current | zh | 0.364 | 0.554 | +0.191 | **0.976** |
| V1_current | en | 0.361 | 0.746 | +0.385 | **0.992** |
| V2_many_shot | zh | 0.276 | 0.57 | +0.294 | **0.999** |
| V2_many_shot | en | 0.348 | 0.757 | +0.410 | **0.995** |
| V3_definition | zh | 0.243 | 0.435 | +0.192 | **0.973** |
| V3_definition | en | 0.355 | 0.776 | +0.422 | **0.958** |
| V4_human_framed | zh | 0.252 | 0.32 | +0.068 | **0.686** |
| V4_human_framed | en | 0.29 | 0.615 | +0.325 | **0.932** |
| V5_anchored_scale | zh | 0.369 | 0.562 | +0.194 | **0.993** |
| V5_anchored_scale | en | 0.38 | 0.74 | +0.360 | **0.995** |
