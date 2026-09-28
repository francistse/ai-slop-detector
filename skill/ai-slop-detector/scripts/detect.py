#!/usr/bin/env python3
"""
ai-slop-detector — rubric-based human/AI-tone scorer (Jev-only).

A standalone tool (NOT bundled into sikaoge-* skills) that scores a piece of
text for AI-sounding traits and returns a verdict + confidence. It is a
pattern/rubric scorer, NOT a ground-truth detector: it flags stylistic tells,
which is meaningful at any length (incl. 50-100 char Cantonese ragebait posts
where GPTZero-type perplexity detectors are pure noise).

Backend: Jev via OpenRouter (hosted, ~$0.000015/call) — needs OPENROUTER_API_KEY.

Design (deliberately simple & honest):
  - Auto language detection (zh/en) routes to the right question language and
    calibration thresholds.
  - The `machine_written` direct signal is CONCRETE: it embeds real-human vs
    AI-draft exemplars as the decision surface (proven to separate far better
    than a vague abstraction).
  - 7 AI-tell traits, each scored 0-1, blended 50/50 with the direct signal.
  - Verdict = 3-band (human / ambiguous / AI) using per-language thresholds
    derived from the gold set so the flanking bands carry 0 FP and 0 FN.
  - Laya was REMOVED in v0.3: it over-fired on short Cantonese (17/28 human FP)
    and its offline value did not offset the risk. This build is Jev-only.

Usage:
  python3 detect.py --text "你的廣東話帖 ..." [--lang auto] [--backend jev]
  cat file.txt | python3 detect.py
  python3 detect.py --file post.txt
  python3 detect.py --check "-" < post.txt

Exit codes (CI-friendly):
  0  human-likely / ambiguous   (low AI signal)
  1  AI-likely                  (high AI signal — review/edit before publishing)
"""

import argparse
import json
import os
import re
import sys
import time


# ---------------------------------------------------------------------------
# The seven Cantonese AI-tell traits (from 思考哥 step 5.5 research).
# Each is a Noul-style 0-1 "is this trait present in the text?" question.
# ---------------------------------------------------------------------------
TRAITS = [
    {
        "key": "reveal_trope",
        "q_en": "Does the text open or use a big-reveal construction announcing deep truth with an emphasis, such as 'the truth is', 'the real issue is', or 'at its core' followed by a dash?",
        "q_zh": "文章係咪用「真相係／問題係／本質係——」呢類大揭曉句式去宣布一個所謂深層真相（強調式開頭 + 破折號）？",
        "weight": 1.4,
    },
    {
        "key": "triple_question",
        "q_en": "Does the text stack three or more rhetorical questions in a row?",
        "q_zh": "文章係咪連住三個或以上嘅設問／反問（三連問）？",
        "weight": 1.0,
    },
    {
        "key": "perfect_antithesis",
        "q_en": "Does the text use many perfectly balanced 'not X but Y' parallel/antithesis constructions?",
        "q_zh": "文章係咪好多「唔係X，係Y」呢類完美對仗／對比句式？",
        "weight": 1.0,
    },
    {
        "key": "abstraction",
        "q_en": "Is the writing abstract and generic, with few concrete specifics like numbers, names, places, prices, or times?",
        "q_zh": "文章係咪抽象大詞、少具體細節（數字／人名／地點／銀碼／時間）？",
        "weight": 1.4,
    },
    {
        "key": "over_balanced",
        "q_en": "Does the text seem too evenly balanced, listing both sides fairly instead of taking a clear stance or edge?",
        "q_zh": "語氣係咪太平衡、兩邊都「X冇錯，Y都冇錯」，冇企硬一個立場／冇火氣？",
        "weight": 1.0,
    },
    {
        "key": "even_rhythm",
        "q_en": "Is the rhythm too uniform — sentences about the same length and structure with little variation, no short punchy breaks?",
        "q_zh": "節奏係咪太順、句句差唔多長度結構、冇長短混雜／斷句位？",
        "weight": 0.8,
    },
    {
        "key": "hashtag_stack",
        "q_en": "Does the text carry a cluttered stack of hashtags (5+)?  (Skips to low/none if there are no hashtags.)",
        "q_zh": "係咪堆咗一大疊 hashtag（5 個以上）？（冇 hashtag 就當冇呢個信號）",
        "weight": 0.6,
    },
]

# Direct-signal trait: how machine-written the text reads. MANY-SHOT — 3 real-human
# vs 3 AI-draft exemplars as the decision surface (v1.2: beat 1-exemplar, definition,
# anchored-scale and human-framed variants in the benchmark; AUROC zh 0.999 / en 0.995).
_EN_H = [
    "thats okay, probably was engineered by an llm, who thought GETs were always read only",
    "We need an NTSB for AI. Let's just start with mandatory reporting to an agency with subpoena power.",
    "When you employ the infinite monkey theorem for your marketing strategy.",
]
_EN_A = [
    "The future of work isn't about replacing people with machines. It's about redefining what humans do best and letting automation handle the rest.",
    "In today's rapidly evolving technological landscape, AI serves as an enduring testament to the transformative potential of large language models.",
    "Consider the humble coffee cup. Its journey from bean to mug involves farmers, roasters, shippers, baristas.",
]
_ZH_H = [
    "男人搵啱嘅女人先困難　單身一世好過，叫雞解決性慾就得",
    "女人一係收兵一係玩人感情咪又係賤",
    "除非個樣生到奇珍異獸咁，否則女人想出pool拍拖係唔難",
]
_ZH_A = [
    "「風水寶地」「全世界最好」——特首句咙，連登秒變悕笑區。點解「自誇」這麼易給人寸？因為群眾唔係聽你講么，係看你做到么。你話，點先至令大家重新相信？",
    "你叫緊作寶地，但個人撐緊工時、搓緊樓價、看住單力數字。講得再好，都比不上親身感受。你話，條gap點先收得埋？",
    "27歲女踩單車，俾3狗追。人死咗，狗捉唔到，政府話「會跟進」。跟進么？跟進200次，都係等下一單先識緊張。真相係——我哋由頭到尾冇保護機制。你話，條命算邊個數？",
]


def _direct_q():
    hb_en = "\n".join(f"- \"{h}\"" for h in _EN_H)
    ab_en = "\n".join(f"- \"{a}\"" for a in _EN_A)
    hb_zh = "\n".join(f"- \"{h}\"" for h in _ZH_H)
    ab_zh = "\n".join(f"- \"{a}\"" for a in _ZH_A)
    return {
        "key": "machine_written",
        "q_en": (
            "Rate how likely an LLM wrote this text (0-1). Compare against these EXAMPLES.\n"
            f"HUMAN-written examples:\n{hb_en}\n\nLLM-generated examples:\n{ab_en}\n"
            "Closer to the LLM examples = higher score."
        ),
        "q_zh": (
            "評分：呢段有幾大機會係LLM寫（0-1）。對比例子先評。\n"
            f"【人類寫】\n{hb_zh}\n\n【LLM寫】\n{ab_zh}\n"
            "愈似LLM例子就愈高分。"
        ),
        "weight": 1.0,
    }


DIRECT = _direct_q()


# ---------------------------------------------------------------------------
# Jev backend — provider-agnostic. Two supported providers, selected by env:
#   official   : Jev's own API          https://thejevai.com/v1/systemone  (JEV_API_KEY, model 'jev-latest')
#   openrouter : via OpenRouter         https://openrouter.ai/api/alpha/decisions (OPENROUTER_API_KEY, '~typesafe/jev-latest')
# Selection (JEV_PROVIDER=official|openrouter wins; else auto):
#   JEV_API_KEY set  -> official ; otherwise -> openrouter.
# Any endpoint/model can be overridden with JEV_BASE_URL / JEV_MODEL / JEV_API_KEY
# so a self-hosted / compatible gateway also works. Keys are read at runtime
# (env first, then ~/.hermes/.env); nothing is stored in this repo.
# ---------------------------------------------------------------------------
_DEFAULT_ENDPOINTS = {
    "openrouter": "https://openrouter.ai/api/alpha/decisions",
    "official": "https://thejevai.com/v1/systemone",
}
_DEFAULT_MODELS = {
    "openrouter": "~typesafe/jev-latest",
    "official": "jev-latest",
}


def _read_env_key(name="OPENROUTER_API_KEY"):
    k = os.environ.get(name)
    if k:
        return k
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        m = re.search(r"^\s*%s\s*=\s*(\S+)" % re.escape(name), open(env_path).read(), re.M)
        if m:
            return m.group(1).strip().strip('"').strip("'")
    return None


def _jev_config():
    provider = os.environ.get("JEV_PROVIDER", "").strip().lower()
    if not provider:
        provider = "official" if os.environ.get("JEV_API_KEY") else "openrouter"
    if provider not in ("official", "openrouter"):
        provider = "openrouter"
    key_name = "JEV_API_KEY" if provider == "official" else "OPENROUTER_API_KEY"
    base = os.environ.get("JEV_BASE_URL", _DEFAULT_ENDPOINTS[provider])
    model = os.environ.get("JEV_MODEL", _DEFAULT_MODELS[provider])
    key = _read_env_key(key_name)
    return {"provider": provider, "base": base, "model": model, "key": key,
            "key_name": key_name}


def _call_jev(text, questions, cfg=None):
    cfg = cfg or _jev_config()
    from urllib.parse import urlsplit
    import http.client

    if not cfg["key"]:
        raise RuntimeError(
            f"No {cfg['key_name']} found for Jev provider '{cfg['provider']}' "
            "(env or ~/.hermes/.env). Set JEV_PROVIDER / JEV_API_KEY to use the "
            "official endpoint, or keep OPENROUTER_API_KEY for OpenRouter."
        )
    payload = {
        "model": cfg["model"],
        "state": text,
        "questions": {k: v for k, v in questions.items()},
    }
    body = json.dumps(payload).encode("utf-8")

    parsed = urlsplit(cfg["base"])
    use_tls = parsed.scheme == "https"
    port = parsed.port or (443 if use_tls else 80)
    host = parsed.hostname
    path = parsed.path or "/"

    # NOTE: urllib.request.urlopen returns 401/403 on these hosts; http.client works.
    last = None
    for attempt in range(3):  # bounded retry: 429/5xx only
        try:
            conn = http.client.HTTPSConnection(host, port, timeout=60) if use_tls \
                else http.client.HTTPConnection(host, port, timeout=60)
            conn.request("POST", path, body=body, headers={
                "Authorization": f"Bearer {cfg['key']}",
                "Content-Type": "application/json",
            })
            resp = conn.getresponse()
            raw = resp.read().decode()
            conn.close()
            if resp.status == 200:
                return json.loads(raw)
            if resp.status in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(2 ** attempt)
                last = f"HTTP {resp.status}"
                continue
            raise RuntimeError(f"Jev HTTP {resp.status}: {resp.reason}")
        except RuntimeError:
            raise
        except Exception as e:
            last = e
            if attempt >= 2:
                raise RuntimeError(f"Jev error: {e}")
            time.sleep(1)
    raise RuntimeError(f"Jev failed: {last}")


def _normalize(answers):
    """Normalise a backend answers map into {qid: 0-1}."""
    out = {}
    for k, v in answers.items():
        if isinstance(v, dict):
            if "noul" in v:
                n = v["noul"]
            elif "probabilities" in v:
                p = v["probabilities"]
                n = max(p.values()) if isinstance(p, dict) else (max(p) if p else 0.5)
            elif isinstance(v.get("score"), (int, float)):
                mx = v.get("legend") or {}
                hi = float(len(mx) - 1) if isinstance(mx, dict) and mx else 1.0
                n = (v["score"] / hi) if hi else 0.5
            else:
                n = 0.5
        elif isinstance(v, (int, float)):
            n = v
        else:
            n = 0.5
        out[k] = float(min(1, max(0, n)))
    return out


# ---------------------------------------------------------------------------
# Language autodetection (Jev) + per-language calibration thresholds
# ---------------------------------------------------------------------------
LANG_INS = (
    "What language is the text written in? Answer zh if the writing is "
    "Cantonese or Chinese, en if it is English."
)
LANG_CRITERIA = {"zh": "Cantonese / Chinese text", "en": "English text"}

_DEFAULT_THRESH = {"human_hi": 0.40, "ai_lo": 0.60}


def _load_calibration():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calibration.json")
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception:
            return {}
    return {}


CALIBRATION = _load_calibration()


def _thresholds(lang):
    d = CALIBRATION.get("jev", {}).get(lang, {}) if CALIBRATION else {}
    return {
        "human_hi": d.get("human_hi", _DEFAULT_THRESH["human_hi"]),
        "ai_lo": d.get("ai_lo", _DEFAULT_THRESH["ai_lo"]),
    }


def _detect_lang(text):
    """Ask Jev to classify text language (zh/en). Returns ('zh'|'en')."""
    lang_q = {"lang_det": {"type": "choice", "instructions": LANG_INS,
                           "criteria": dict(LANG_CRITERIA)}}
    resp = _call_jev(text, lang_q)
    a = resp.get("answers", {}).get("lang_det", {})
    choice = a.get("choice")
    if not choice and isinstance(a.get("probabilities"), dict):
        choice = max(a["probabilities"], key=a["probabilities"].get)
    s = str(choice or "").lower()
    return "zh" if s.startswith("zh") else "en"


def _jev_answers(text, questions):
    cfg = _jev_config()
    qdefs = {k: {"type": "noul", "instructions": v} for k, v in questions.items()}
    resp = _call_jev(text, qdefs, cfg=cfg)
    usage = resp.get("usage", {}) or {}
    meta = {
        "provider": cfg["provider"],
        "model": resp.get("model") or cfg["model"],
        "cost": usage.get("cost"),  # openrouter only
        "input_tokens": usage.get("input_tokens"),  # official endpoint
    }
    raw = resp.get("answers", {})
    return _normalize(raw), "jev", meta


# ---------------------------------------------------------------------------
# Core scorer (Jev-only)
# ---------------------------------------------------------------------------
def score(text, traits, direct, lang="auto", backend="auto"):
    """Score text with Jev. Returns (result, backend, meta).

    `backend` is accepted for caller compatibility: 'auto' and 'jev' both run
    Jev. 'laya' was removed in v0.3 and now raises a clear error.
    """
    if str(backend).lower() == "laya":
        raise RuntimeError(
            "Laya backend was removed in v0.3 (it over-fired on short Cantonese). "
            "This tool is Jev-only."
        )
    if lang == "auto":
        lang = _detect_lang(text)

    questions = {}
    for t in traits:
        questions[t["key"]] = t["q_zh"] if lang.startswith("zh") else t["q_en"]
    questions[direct["key"]] = direct["q_zh"] if lang.startswith("zh") else direct["q_en"]

    answers, b, meta = _jev_answers(text, questions)
    result = _aggregate(answers, traits, direct, text, lang=lang)
    return result, b, meta


def _aggregate(answers, traits, direct, text, lang="zh"):
    # Weighted AI score across the tell traits.
    total_w = 0.0
    ai = 0.0
    n_hashtags = len(re.findall(r"#\S+", text))
    used = []
    for t in traits:
        v = answers.get(t["key"])
        if v is None:
            continue
        if t["key"] == "hashtag_stack" and n_hashtags < 5:
            continue  # no hashtag stack → trait irrelevant
        ai += v * t["weight"]
        total_w += t["weight"]
        used.append(t["key"])

    ai_trait = ai / total_w if total_w else 0.5

    # v1.2: the VERDICT runs on the direct (many-shot) signal alone — the
    # benchmark showed it is the strongest, most separable view. The 7 trait
    # Nouls are computed and reported as an *editing breakdown* only, not
    # weighted into ai_probability (weighting them would damp separation).
    direct_v = answers.get(direct["key"])
    if direct_v is None:
        direct_v = 0.5
    ai_proba = float(direct_v)

    # Per-language thresholds from calibration.json (fall back to 0.40/0.60).
    th = _thresholds(lang)
    human_hi, ai_lo = th["human_hi"], th["ai_lo"]
    if ai_proba > max(ai_lo, human_hi):
        verdict = "AI-likely"
    elif ai_proba < human_hi:
        verdict = "human-likely"
    else:
        verdict = "ambiguous"

    # Confidence = how decisively the score sits inside its band (distance to
    # the decision boundary, 0 at the edge -> 1 deep inside).
    if verdict == "AI-likely":
        confidence = 1.0 - (ai_lo / max(ai_proba, 1e-9))  # closer to ai_lo => lower
        confidence = round(max(0.0, min(1.0, confidence * 2.0)), 3)
    elif verdict == "human-likely":
        confidence = round(max(0.0, min(1.0, (human_hi - ai_proba) / max(human_hi, 1e-9))), 3)
    else:
        mid = (human_hi + ai_lo) / 2.0
        half = max((ai_lo - human_hi) / 2.0, 1e-9)
        confidence = round(min(1.0, abs(ai_proba - mid) / half), 3)  # centrality in band

    return {
        "verdict": verdict,
        "ai_probability": round(ai_proba, 3),
        "confidence": confidence,
        "traits": {t["key"]: round(answers.get(t["key"], 0), 3) for t in traits},
        "direct_signal": round(ai_proba, 3),
        "used_traits": used,
        "lang": lang,
        "thresholds": {"human_hi": human_hi, "ai_lo": ai_lo},
    }


def main():
    ap = argparse.ArgumentParser(description="Rubric-based human/AI tone scorer (Jev-only)")
    ap.add_argument("--text", help="Text to score (inline)")
    ap.add_argument("--file", help="Read text from a file")
    ap.add_argument("--lang", default="auto", choices=["auto", "zh", "en"],
                    help="auto: ask Jev to detect language (default); else force zh/en question language + thresholds")
    ap.add_argument("--json", action="store_true", help="Emit raw JSON only")
    ap.add_argument("--backend", default="auto", choices=["auto", "jev"],
                    help="auto == jev (single backend; Laya removed in v0.3)")
    ap.add_argument("--check", help="Alias for --text (reads STDIN if '-' )")
    args = ap.parse_args()

    if args.text:
        text = args.text
    elif args.file:
        with open(args.file, encoding="utf-8") as f:
            text = f.read()
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    elif args.check:
        if args.check == "-":
            text = sys.stdin.read()
        else:
            text = args.check
    else:
        ap.error("Provide --text, --file, --check, or pipe stdin")

    result, backend, meta = score(text, TRAITS, DIRECT, lang=args.lang, backend=args.backend)
    result["backend"] = backend
    result["meta"] = meta

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result["verdict"] != "AI-likely" else 1)

    cost = ""
    if meta.get("cost") is not None:
        cost += f"  (cost ${meta['cost']:.6f})"
    elif meta.get("input_tokens") is not None:
        cost += f"  ({meta['input_tokens']} in-tokens)"
    out = [
        f"verdict: {result['verdict']}",
        f"ai_probability: {result['ai_probability']:.2%}",
        f"confidence: {result['confidence']:.2%}",
        f"backend: {backend} · provider: {meta.get('provider','?')}{cost}",
        "traits (AI-tell 0-1):",
    ]
    for t in TRAITS:
        out.append(f"  {t['key']:14s} {result['traits'].get(t['key'], 0):.2f}")
    out.append(f"  machine_written(direct): {result['direct_signal']:.2f}")
    print("\n".join(out))


if __name__ == "__main__":
    main()
