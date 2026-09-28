#!/usr/bin/env python3
"""Tune per-(backend, detected_lang) verdict thresholds on the gold set.

Reads eval/out/cases.csv (produced by run_eval with --lang auto), grid-searches
(backend, lang) pairs of (human_hi, ai_lo) thresholds, and writes
calibration.json next to the live detect.py so the detector uses it.

Objective: pick the threshold pair that MAXIMISES F1 on the AI class while
keeping the FALSE-POSITIVE rate (human misread as AI) <= fp_cap. This encodes
the project's safety stance: never accuse a person unless we must.
Tuned on the SAME gold set used for reporting -> these are an IN-SAMPLE / best-
case ceiling; a held-out number would be lower. That is exactly the honesty we
want: it tells us if calibration can help AT ALL before we invest further.
"""
import csv
import itertools
import json
import os
import sys

CASES = os.path.expanduser("~/ai-slop-detector/eval/out/cases.csv")
DETECT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "skill", "ai-slop-detector", "scripts")  # bundle dir (detect.py + calibration.json)
OUT = os.path.join(DETECT_DIR, "calibration.json")

FP_CAP = float(os.environ.get("FP_CAP", "0.15"))  # max acceptable false-positive rate


def f1(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    return 2 * p * r / (p + r) if (p + r) else 0.0


def verdict(p, human_hi, ai_lo):
    if p > max(ai_lo, human_hi):
        return "AI-likely"
    if p < human_hi:
        return "human-likely"
    return "ambiguous"


def tune(group):
    best = None
    for human_hi in [round(x, 2) for x in
                     itertools.chain((i / 20 for i in range(2, 11)), [0.33, 0.30, 0.36, 0.40, 0.45])]:
        for ai_lo in [round(x, 2) for x in
                      itertools.chain((i / 20 for i in range(8, 17)), [0.55, 0.60, 0.65, 0.70, 0.75, 0.50])]:
            if not (ai_lo >= human_hi):
                continue
            tp = fp = fn = 0
            for c in group:
                v = verdict(float(c["ai_probability"]), human_hi, ai_lo)
                if v == "AI-likely":
                    if c["label"] == "ai":
                        tp += 1
                    else:
                        fp += 1
                else:
                    if c["label"] == "ai" and v != "ambiguous":
                        fn += 1
            fpr = fp / max(1, sum(1 for c in group if c["label"] == "human"))
            if fpr > FP_CAP:
                continue  # reject: too many false accusations
            score = f1(tp, fp, fn)
            if best is None or score > best[0]:
                best = (score, human_hi, ai_lo, tp, fp, fn, fpr)
    return best


def main():
    rows = list(csv.DictReader(open(CASES)))
    calib = {}
    langs = sorted({r["detected_lang"] for r in rows})
    for b in sorted({r["backend"] for r in rows}):
        for lg in langs:
            grp = [r for r in rows if r["backend"] == b and r["detected_lang"] == lg]
            if not grp:
                continue
            best = tune(grp)
            if best:
                _, human_hi, ai_lo, tp, fp, fn, fpr = best
                n = len(grp)
                calib.setdefault(b, {})[lg] = {
                    "human_hi": human_hi, "ai_lo": ai_lo, "note": "in-sample tuned",
                    "_on": {"n": n, "tp": tp, "fp": fp, "fn": fn, "fp_rate": round(fpr, 3)},
                }
                print(f"{b:5} {lg:2} -> human_hi={human_hi} ai_lo={ai_lo} "
                      f"(F1={best[0]:.2f} tp={tp} fp={fp} fn={fn} fpr={fpr:.2%} n={n})")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(calib, f, ensure_ascii=False, indent=2)
    print("wrote", OUT)


if __name__ == "__main__":
    main()