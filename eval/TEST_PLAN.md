# ai-slop-detector — Test Plan (v1)

Status: **internal pre-publish verification**. Nothing here is a published
accuracy claim; this plan decides *whether the tool is competent enough to
publish as an "AI content detector"* — and if not, what would be.

## 1. Goal & question

Verify, with attributed ground truth, whether the `ai-slop-detector` actually
*detects* AI content — and quantify precisely where it fails, per backend and
per language. Gate: **do not publish until the sufficiency question is
answered and the calibration is either proven fit or changed.**

## 2. Ground-truth rule (attribution, not opinion)

| label | definition | provenance |
|---|---|---|
| `human` | text a real person wrote | LIHKG thread comments (28), Hacker News comments (24) — verbatim, live permalinks |
| `ai` | text actually produced by a model | 4 思考哥 drafts + 16 direct outputs, all `deepseek-v4-flash` (this Hermes session) — see `gold/ai.jsonl` |

No "this sounds AI" opinions. Every label is an attribute of how the text was
produced.

## 3. Data & counts

| group | file | N | lang break |
|---|---|---|---|
| AI (deepseek-v4-flash) | `eval/gold/ai.jsonl` | 20 | 12 zh / 8 en |
| Human, Cantonese (LIHKG) | `eval/raw/canto_human.jsonl` | 28 | 28 zh |
| Human, English (Hacker News) | `eval/raw/en_human.jsonl` | 24 | 24 en |
| **Total** | | **72** | 40 zh / 32 en |

- Human text lengths ~ 11–327 chars; AI 92–362. Covers short → long.
- **Known confound, stated honestly:** the Cantonese AI set is *adversarially
  humanized* (思考哥 drafts are LLM output written to sound human) + direct
  deepseek-v4-flash output. So Cantonese-AI recall is a *harder / worst-case*
  measure; English-AI is direct (unhumanized) output.

## 4. Metrics measured (per backend)

- fp = human misread as AI (the harmful direction) · fn = AI missed · abstain = `ambiguous`
- verbatim-only accuracy (excluding abstentions), fp-rate, fn-rate, abstention rate
- confidence = agreement between the trait rubric and the direct `machine_written` reading

## 5. Sufficiency rule

- **Adequate (this is enough):** the result decides the *direction* of
  competence beyond the ~±11pp CI of n=72 — e.g. if Cantonese-AI recall with
  Jev is ~0% while FP is 0%, the failure mode is unambiguous.
- **Not adequate:** only when the CI would flip a go/no-go, or when we need
  precise tuned thresholds (that needs a separate per-language tuning set),
  or when the numbers are close enough that noise decides.

## 6. Outputs

- `eval/out/cases.csv` — every case × backend × full scores
- `eval/out/report.md` — aggregate per backend
- `TEST_PLAN.md` (this file) + `VERIFICATION.md` (the write-up with per-case
  Jev scores, data provenance, verdict, recommendation)