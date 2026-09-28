# Scoring-prompt variants (verbatim, for review)
Each variant is a single Noul question. All are scored per-case with Jev and ranked by AUROC in `README_benchmark.md`.

## V1_current
### zh
```
撇開具體規則，呢段文字有幾似AI寫、唔似人寫？對比兩個例子先評分。
【真人】粗口、跳躍:「男人搵啱嘅女人先困難　單身一世好過，叫雞解決性慾就得」
【AI稿】工整、拖尾「你話」:「「風水寶地」「全世界最好」——特首句咙，連登秒變悕笑區。點解「自誇」這麼易給人寸？因為群眾唔係聽你講么，係看你做到么。你話，點先至令大家重新相信？」
愈似AI就愈高分(0-1)。
```
### en
```
How close is this text to MACHINE-written rather than an actual person? Rate by comparing these two anchors.
REAL human: "thats okay, probably was engineered by an llm, who thought GETs were always read only"
AI-generated: "The future of work isn't about replacing people with machines. It's about redefining what humans do best and letting automation handle the rest."
The closer to the AI example, the higher the score (0-1).
```

## V2_many_shot
### zh
```
評分：呢段有幾大機會係LLM寫(0-1)。對比例子。
【人類寫】
- "男人搵啱嘅女人先困難　單身一世好過，叫雞解決性慾就得"
- "女人一係收兵一係玩人感情咪又係賤"
- "除非個樣生到奇珍異獸咁，否則女人想出pool拍拖係唔難"

【LLM寫】
- "「風水寶地」「全世界最好」——特首句咙，連登秒變悕笑區。點解「自誇」這麼易給人寸？因為群眾唔係聽你講么，係看你做到么。你話，點先至令大家重新相信？"
- "你叫緊作寶地，但個人撐緊工時、搓緊樓價、看住單力數字。講得再好，都比不上親身感受。你話，條gap點先收得埋？"
- "27歲女踩單車，俾3狗追。人死咗，狗捉唔到，政府話「會跟進」。跟進么？跟進200次，都係等下一單先識緊張。真相係——我哋由頭到尾冇保護機制。你話，條命算邊個數？"
愈似LLM例子愈高分。
```
### en
```
Rate how likely an LLM wrote this text (0-1). Compare against these EXAMPLES.
HUMAN-written examples:
- "thats okay, probably was engineered by an llm, who thought GETs were always read only"
- "We need an NTSB for AI. Let's just start with mandatory reporting to an agency with subpoena power."
- "When you employ the infinite monkey theorem for your marketing strategy."

LLM-generated examples:
- "The future of work isn't about replacing people with machines. It's about redefining what humans do best and letting automation handle the rest."
- "In today's rapidly evolving technological landscape, AI serves as an enduring testament to the transformative potential of large language models."
- "Consider the humble coffee cup. Its journey from bean to mug involves farmers, roasters, shippers, baristas."
Closer to the LLM examples = higher score.
```

## V3_definition
### zh
```
評分(0-1)：呢段文字有幾大機會係LLM寫。
人寫：節奏碎、有具體瑣碎細節、企硬立場／有火、唔工整。
LLM寫：工整對仗、抽象大詞、用「真相係⋯」揭曉句、連環設問、兩邊都咁講。
愈似LLM就愈高分。
```
### en
```
Rate the probability (0-1) that this text was written by an LLM.
A PERSON writes with ragged rhythm, concrete and messy detail, hedged or one-sided claims, and a clear personal stance. An LLM writes polished, balanced, abstract prose with reveal-sentence payoffs ('the real issue is…'), perfect 'not X but Y' antithesis, stacked rhetorical questions, and generic claims. Higher = more like LLM output.
```

## V4_human_framed
### zh
```
評分：呢段文字有幾似一個真實、有脾氣、具體嘅真人寫(0=完全機器,1=完全似人)。
真人例:「男人搵啱嘅女人先困難　單身一世好過，叫雞解決性慾就得」
機器例:「「風水寶地」「全世界最好」——特首句咙，連登秒變悕笑區。點解「自誇」這麼易給人寸？因為群眾唔係聽你講么，係看你做到么。你話，點先至令大家重新相信？」
(我哋會用1減呢個分當AI相似度。)
```
### en
```
Rate how strongly this reads as written by a real, flawed, opinionated PERSON (0 = totally machine, 1 = totally human).
Human example: "thats okay, probably was engineered by an llm, who thought GETs were always read only"
Machine example: "The future of work isn't about replacing people with machines. It's about redefining what humans do best and letting automation handle the rest."
Note: we count the OPPOSITE of this as AI-likeness.
```

## V5_anchored_scale
### zh
```
撇開具體規則，呢段文字有幾似AI寫、唔似人寫？對比兩個例子先評分。
【真人】粗口、跳躍:「男人搵啱嘅女人先困難　單身一世好過，叫雞解決性慾就得」
【AI稿】工整、拖尾「你話」:「「風水寶地」「全世界最好」——特首句咙，連登秒變悕笑區。點解「自誇」這麼易給人寸？因為群眾唔係聽你講么，係看你做到么。你話，點先至令大家重新相信？」
愈似AI就愈高分(0-1) 用0到1計分：0=完全似人類例子，1=完全似AI例子。畀一個數字。
```
### en
```
How close is this text to MACHINE-written rather than an actual person? Rate by comparing these two anchors.
REAL human: "thats okay, probably was engineered by an llm, who thought GETs were always read only"
AI-generated: "The future of work isn't about replacing people with machines. It's about redefining what humans do best and letting automation handle the rest."
The closer to the AI example, the higher the score (0-1). Use a 0..1 scale where 0 = exactly the human example, 1 = exactly the AI example. Give one number.
```
