#!/usr/bin/env python3
"""Benchmark Jev scoring-prompt variants on the gold set.

Each variant is a SINGLE Noul question producing a 0-1 'AI-likeness' score per
case (traits excluded so we compare decision prompts on equal footing). We
report, per variant per language: mean human / mean AI, the separation gap,
and AUROC (rank ordering of AI above human) — AUROC is the headline metric for
'which prompt is best at the problem', independent of threshold calibration.

Variants tested (experimental design):
  V1 current       1 human + 1 AI exemplar, 'rate AI-ness'          (baseline)
  V2 many-shot     3 human + 3 AI exemplars, 'rate AI-ness'
  V3 definition    no exemplars; concrete behavioral definition
  V4 human-framed  1H+1A exemplars but ask 'how HUMAN' (inverted)
  V5 anchored-rich V1 + explicit 0..1 scale anchors
All scores cached to eval/bench/<variant>_<zh|en>.json so nothing is lost.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "skill", "ai-slop-detector", "scripts"))  # bundle detect.py
import detect

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "bench")
os.makedirs(OUT, exist_ok=True)

# --- exemplars (from the gold set) ---
EN_H = [
    "thats okay, probably was engineered by an llm, who thought GETs were always read only",
    "We need an NTSB for AI. Let's just start with mandatory reporting to an agency with subpoena power.",
    "When you employ the infinite monkey theorem for your marketing strategy.",
]
EN_A = [
    "The future of work isn't about replacing people with machines. It's about redefining what humans do best and letting automation handle the rest.",
    "In today's rapidly evolving technological landscape, AI serves as an enduring testament to the transformative potential of large language models.",
    "Consider the humble coffee cup. Its journey from bean to mug involves farmers, roasters, shippers, baristas.",
]
ZH_H = [
    "男人搵啱嘅女人先困難　單身一世好過，叫雞解決性慾就得",
    "女人一係收兵一係玩人感情咪又係賤",
    "除非個樣生到奇珍異獸咁，否則女人想出pool拍拖係唔難",
]
ZH_A = [
    "「風水寶地」「全世界最好」——特首句咙，連登秒變悕笑區。點解「自誇」這麼易給人寸？因為群眾唔係聽你講么，係看你做到么。你話，點先至令大家重新相信？",
    "你叫緊作寶地，但個人撐緊工時、搓緊樓價、看住單力數字。講得再好，都比不上親身感受。你話，條gap點先收得埋？",
    "27歲女踩單車，俾3狗追。人死咗，狗捉唔到，政府話「會跟進」。跟進么？跟進200次，都係等下一單先識緊張。真相係——我哋由頭到尾冇保護機制。你話，條命算邊個數？",
]


def _noul(text, instruction):
    q = {"q1": {"type": "noul", "instructions": instruction}}
    r = detect._call_jev(text, q)
    return float(r.get("answers", {}).get("q1", {}).get("noul", 0.5))


def variants(lang):
    """Return {variant_name: {type,instructions}} already filled for `lang`."""
    e = lang == "en"
    H = EN_H if e else ZH_H
    A = EN_A if e else ZH_A
    human_A, ai_A = H[0], A[0]

    def one_ex(hm, am):
        if e:
            return (f"How close is this text to MACHINE-written rather than an actual person? "
                    f"Rate by comparing these two anchors.\nREAL human: \"{hm}\"\n"
                    f"AI-generated: \"{am}\"\nThe closer to the AI example, the higher the score (0-1).")
        return (f"撇開具體規則，呢段文字有幾似AI寫、唔似人寫？對比兩個例子先評分。\n"
                f"【真人】粗口、跳躍:「{hm}」\n【AI稿】工整、拖尾「你話」:「{am}」\n"
                f"愈似AI就愈高分(0-1)。")

    def many_ex(hs, as_):
        hb = "\n".join(f"- \"{h}\"" for h in hs)
        ab = "\n".join(f"- \"{a}\"" for a in as_)
        if e:
            return (f"Rate how likely an LLM wrote this text (0-1). Compare against these EXAMPLES.\n"
                    f"HUMAN-written examples:\n{hb}\n\nLLM-generated examples:\n{ab}\n"
                    f"Closer to the LLM examples = higher score.")
        return (f"評分：呢段有幾大機會係LLM寫(0-1)。對比例子。\n【人類寫】\n{hb}\n\n【LLM寫】\n{ab}\n愈似LLM例子愈高分。")

    def definition():
        if e:
            return ("Rate the probability (0-1) that this text was written by an LLM.\n"
                    "A PERSON writes with ragged rhythm, concrete and messy detail, hedged or one-sided "
                    "claims, and a clear personal stance. An LLM writes polished, balanced, abstract prose "
                    "with reveal-sentence payoffs ('the real issue is…'), perfect 'not X but Y' antithesis, "
                    "stacked rhetorical questions, and generic claims. Higher = more like LLM output.")
        return ("評分(0-1)：呢段文字有幾大機會係LLM寫。\n"
                "人寫：節奏碎、有具體瑣碎細節、企硬立場／有火、唔工整。\n"
                "LLM寫：工整對仗、抽象大詞、用「真相係⋯」揭曉句、連環設問、兩邊都咁講。\n"
                "愈似LLM就愈高分。")

    def human_framed():
        hm, am = human_A, ai_A
        if e:
            return (f"Rate how strongly this reads as written by a real, flawed, opinionated PERSON "
                    f"(0 = totally machine, 1 = totally human).\nHuman example: \"{hm}\"\n"
                    f"Machine example: \"{am}\"\nNote: we count the OPPOSITE of this as AI-likeness.")
        return (f"評分：呢段文字有幾似一個真實、有脾氣、具體嘅真人寫(0=完全機器,1=完全似人)。\n"
                f"真人例:「{hm}」\n機器例:「{am}」\n(我哋會用1減呢個分當AI相似度。)")

    def anchored_scale():
        inner = one_ex(human_A, ai_A).rstrip("。")
        if e:
            return inner + (" Use a 0..1 scale where 0 = exactly the human example, 1 = exactly the "
                            "AI example. Give one number.")
        return inner + (" 用0到1計分：0=完全似人類例子，1=完全似AI例子。畀一個數字。")

    return {
        "V1_current": {"type": "noul", "instructions": one_ex(H[0], A[0])},
        "V2_many_shot": {"type": "noul", "instructions": many_ex(H, A)},
        "V3_definition": {"type": "noul", "instructions": definition()},
        "V4_human_framed": {"type": "noul", "instructions": human_framed()},
        "V5_anchored_scale": {"type": "noul", "instructions": anchored_scale()},
    }


def auroc(ai, hu):
    """Mann-Whitney U -> AUROC: P(AI score > human score). 0.5=random, 1=perfect."""
    ai, hu = sorted(ai), sorted(hu)
    i = j = 0
    wins = 0.0
    ties = 0.0
    pairs = len(ai) * len(hu)
    for a in ai:
        while j < len(hu) and hu[j] < a:
            j += 1
        k = j
        while k < len(hu) and hu[k] == a:
            k += 1
        wins += j
        ties += (k - j)
    return (wins + 0.5 * ties) / pairs


def load_gold():
    gold = []
    for r in [json.loads(l) for l in open(os.path.join(HERE, "raw/canto_human.jsonl")) if l.strip()]:
        gold.append({"text": r["text"], "lang": "zh", "label": "human", "id": r["id"]})
    for r in [json.loads(l) for l in open(os.path.join(HERE, "raw/en_human.jsonl")) if l.strip()]:
        gold.append({"text": r["text"], "lang": "en", "label": "human", "id": r["id"]})
    for r in [json.loads(l) for l in open(os.path.join(HERE, "gold/ai.jsonl")) if l.strip()]:
        gold.append({"text": r["text"], "lang": r["lang"], "label": "ai", "id": r["id"]})
    return gold


def main():
    gold = load_gold()
    names = ["V1_current", "V2_many_shot", "V3_definition", "V4_human_framed", "V5_anchored_scale"]
    per_lang = {"zh": [], "en": []}
    for g in gold:
        per_lang[g["lang"]].append(g)

    summary = []
    summary.append("# Prompt-variant benchmark (Jev, N=72)\n")
    summary.append("Each variant is a single Noul scored on every case. Headline = **AUROC** "
                   "(P(AI score > human score)); 1.0 = perfect ordering, 0.5 = random. "
                   "V4 is inverted (we use 1 - 'human' score).\n")
    summary.append("| variant | lang | human mean | AI mean | gap | AUROC |\n|---|---|---|---|---|---|\n")

    for name in names:
        for lg in ("zh", "en"):
            cache = os.path.join(OUT, f"{name}_{lg}.json")
            scores = {}
            if os.path.exists(cache):
                scores = {int(k): v for k, v in json.load(open(cache)).items()}
            for g in per_lang[lg]:
                if g["id"] in scores:
                    continue
                q = variants(lg)[name]
                raw = _noul(g["text"], q["instructions"])
                val = (1.0 - raw) if name == "V4_human_framed" else raw
                scores[g["id"]] = {"raw": raw, "ai": val, "label": g["label"]}
                json.dump({str(k): v for k, v in scores.items()}, open(cache, "w"), ensure_ascii=False)
            ai = [v["ai"] for v in scores.values() if v["label"] == "ai"]
            hu = [v["ai"] for v in scores.values() if v["label"] == "human"]
            a = round(auroc(ai, hu), 3)
            gap = round((sum(ai) / len(ai)) - (sum(hu) / len(hu)), 3)
            hm = round(sum(hu) / len(hu), 3)
            am = round(sum(ai) / len(ai), 3)
            print(f"{name:16} {lg}  human {hm:+.3f}  AI {am:+.3f}  gap {gap:+.3f}  AUROC {a:.3f}")
            summary.append(f"| {name} | {lg} | {hm} | {am} | {gap:+.3f} | **{a}** |\n")
            sys.stdout.flush()

    with open(os.path.join(OUT, "README_benchmark.md"), "w", encoding="utf-8") as f:
        f.write("".join(summary))
    print("\nwrote", os.path.join(OUT, "README_benchmark.md"))


if __name__ == "__main__":
    main()
