# Setup

Three ways to set up `ai-slop-detector`, depending on who you are:
1. **Hermes Agent user** (an AI agent like this one uses the skill directly)
2. **Human with an AI harness only** (just an LLM API — no Hermes)
3. **Skill marketplace** (publish it so others can install it)

In every path the tool itself is a single stdin/stdout Python script
(`detect.py`, stdlib-only — **no `pip install`**) that calls Jev at runtime.
All keys live in your environment or `~/.hermes/.env`; **none are in the repo**.

---

## 1. Hermes Agent setup (AI-agent)

Hermes loads this as a skill and runs `scripts/detect.py` through its `terminal` tool.

**Prereqs**
- Hermes Agent installed (any surface — desktop app, CLI, TUI, gateway).
- Jev reachable from this machine (pick one provider):

**Install the skill**
```bash
# from a marketplace registry (once published — see §3)
hermes skills install ai-slop-detector

# …or it's already installed locally (this machine):
ls ~/.hermes/skills/creative/ai-slop-detector/
#   SKILL.md, scripts/detect.py, scripts/calibration.json
#   (on this machine these are symlinks into ~/ai-slop-detector/skills/ai-slop-detector/,
#    so a change in the repo's skill bundle is immediately live in the skill.)
```

**Provide Jev credentials** (add to `~/.hermes/.env` — secrets live in `.env`, never `config.yaml`):
```bash
# Option A — OpenRouter (default provider)
OPENROUTER_API_KEY=sk-or-...

# Option B — Jev's official API (preferred upstream)
#   (uses https://thejevai.com/v1/systemone, model jev-latest)
JEV_PROVIDER=official
JEV_API_KEY=...
```

**Use it** (what the agent does): load the skill (`skill_view('ai-slop-detector')`) and run:
```bash
python3 ~/.hermes/skills/creative/ai-slop-detector/scripts/detect.py --text "你的廣東話帖 ..."
```

**Verify**
```bash
python3 ~/.hermes/skills/creative/ai-slop-detector/scripts/detect.py \
  --text "真相係——我哋由頭到尾都冇保護機制。你話，條命算邊個數？" --json
# expect: "verdict": "AI-likely"
```

---

## 2. Human with an AI harness only

"AI harness" here means you have *an LLM/decision-model API key* and want the
detector as a plain CLI — no Hermes required.

**Prereqs**
- Python **3.11+** (stdlib only; no dependencies to install).
- One Jev credential: an OpenRouter API key, **or** a Jev official API key.

**Steps**

1. Get the code:
   ```bash
   git clone https://github.com/francistse/ai-slop-detector   # once pushed
   cd ai-slop-detector
   #   (or just copy the skill bundle: skills/ai-slop-detector/)
   ```

2. Put a key where the script can read it (env var wins; otherwise it reads
   `~/.hermes/.env` — create that file if you don't use Hermes):
   ```bash
   export OPENROUTER_API_KEY=sk-or-...          # OpenRouter (default)
   # …or…
   export JEV_PROVIDER=official
   export JEV_API_KEY=...
   ```

3. Run it (the tool is `skills/ai-slop-detector/scripts/detect.py`):
   ```bash
   python3 skills/ai-slop-detector/scripts/detect.py --text "An obvious AI sentence about redefining work..."
   # verdict: AI-likely
   python3 skills/ai-slop-detector/scripts/detect.py --lang en --text "real human typing, lowercase, no polish"
   # verdict: human-likely

   # machine-readable (CI-ready); exit code 0 = not AI-likely, 1 = AI-likely
   python3 skills/ai-slop-detector/scripts/detect.py --text "..." --json; echo "exit=$?"
   ```

4. (Optional) any compatible/hosted Jev endpoint:
   ```bash
   export JEV_BASE_URL=https://my-gateway/v1/systemone
   export JEV_MODEL=jev-latest
   export JEV_API_KEY=...
   ```

**Verify**
```bash
python3 skills/ai-slop-detector/scripts/detect.py --text "真相係——我哋由頭到尾都冇保護機制。你話，條命算邊個數？" --json
# expect: "verdict": "AI-likely"
```

---

## 3. Skill marketplace — publish & install

Hermes discovers skills from several registries (skills.sh, well-known agent
skill endpoints, **GitHub** repos, **ClawHub**, others). HermesHub
(hermeshub.xyz) is a discovery/listing site for these skills. Publishing targets
either **GitHub** or **ClawHub**.

### Author — publish (do once, after you've pushed the repo)
The command takes a **skill directory** (must contain `<name>/SKILL.md`, plus
any `scripts/`). The repo's `skills/ai-slop-detector/` **is already that** — a
real-file bundle (no symlinks), so publish it directly:

```bash
# publish to ClawHub (hosted registry)
hermes skills publish --to clawhub ~/ai-slop-detector/skills/ai-slop-detector

#    …or to a GitHub skills-registry repo (e.g. you maintain a repo of skills)
hermes skills publish --to github --repo <owner>/<skills-registry> ~/ai-slop-detector/skills/ai-slop-detector

# confirm it's searchable
hermes skills search ai-slop-detector
```

> **Marketplace checklist** (frontmatter must already comply):
> `name`, `description` (≤60 chars, one sentence), `version`, `author` (you
> first, then "Hermes Agent"), `license` (MIT), `platforms`, and
> `metadata.hermes.{tags, related_skills}` — see `SKILL.md` / `README.md`.
> The published bundle must contain **no secrets** (the tool reads keys at
> runtime) — verify the tarball has no `.env` and that `detect.py`'s
> `_jev_config()` block matches what you advertise.

### Consumer — install
```bash
hermes skills search ai-slop-detector   # find it
hermes skills inspect ai-slop-detector # preview before installing (optional)
hermes skills install ai-slop-detector
# then add Jev credentials (§1) — the skill brings no keys of its own
```