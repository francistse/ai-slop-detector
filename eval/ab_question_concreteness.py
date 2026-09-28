#!/usr/bin/env python3
"""A/B: is the negative result caused by VAGUE questions, not missing signal?

Runs Jev's machine_written Noul on all 40 Cantonese gold cases two ways:
  VAGUE    = the current abstract question (no anchor)
  CONCRETE = same question + embedded real-LIHKG vs AI-draft exemplars to
             give Jev a grounded decision surface.
Reports the score distributions and how cleanly AI separates from human
under each condition.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root (detect.py)
import detect

hu = [json.loads(l) for l in open("/Users/francis/ai-slop-detector/eval/raw/canto_human.jsonl") if l.strip()]
ai = [json.loads(l) for l in open("/Users/francis/ai-slop-detector/eval/gold/ai.jsonl") if l.strip() and json.loads(l)["lang"] == "zh"]

REAL_EX = "除非個樣生到奇珍異獸咁，否則女人想出pool拍拖係唔難　係大大大𨶙把選擇　拍拖唔係問題，真愛先係問題"
AI_EX = "你叫緊作寶地，但個人撐緊工時、搓緊樓價、看住單力數字。講得再好，都比不上親身感受。你話，條gap點先収得埋？"

VAGUE = {"machine_written": {"type": "noul", "instructions":
    "撇開任何具體規則，單靠直覺，呢段文字有幾似係機器（AI）寫、唔似人寫？"}}

CONCRETE = {"machine_written": {"type": "noul", "instructions":
    "撇開任何具體規則，呢段文字有幾似AI（機器）寫、唔似人寫？對比下面兩個例子先評分。\n"
    "【真正連登人類帖】粗口、跳躍、唔工整：「" + REAL_EX + "」\n"
    "【AI生成稿】工整對仗、拖尾「你話」、好正經：「" + AI_EX + "」\n"
    "句稿愈似第二個（AI）就愈高分，愈似第一個（人類）就愈低分。"}}


def score_jev(text, q):
    r = detect._call_jev(text, q)
    a = r.get("answers", {}).get("machine_written", {})
    return float(a.get("noul", 0.5))


def report(name, cond):
    hs = [score_jev(t_["text"], cond) for t_ in hu]
    as_ = [score_jev(t_["text"], cond) for t_ in ai]
    hmean = sum(hs) / len(hs)
    amean = sum(as_) / len(as_)
    hi_max = max(hs)
    ai_min = min(as_)
    sep = ai_min - hi_max  # >0 = perfect separation
    n_overlap = sum(1 for h in hs if h >= ai_min)
    print(f"\n=== {name} (n human={len(hs)}, n AI={len(as_)}) ===")
    print(f"human ai_prob: mean={hmean:.3f} max={hi_max:.3f}  [{' '.join(f'{x:.2f}' for x in sorted(hs))}]")
    print(f"AI    ai_prob: mean={amean:.3f} min={ai_min:.3f}  [{' '.join(f'{x:.2f}' for x in sorted(as_))}]")
    print(f"gap(AI_min - human_max) = {sep:+.3f}  -> {'SEPARATES' if sep>0 else 'overlaps'}  ; humans above AI_min: {n_overlap}/{len(hs)}")


if __name__ == "__main__":
    report("VAGUE (current)", VAGUE)
    report("CONCRETE (with exemplars)", CONCRETE)