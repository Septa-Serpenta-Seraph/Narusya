# Surviving provider credit exhaustion (free-tier fallback)

Verified 2026-08-26 when OpenRouter hit $449.9993 / $450.00 mid-session. The daemon stayed
online with zero spend. Nothing here requires the user to find money.

## 1. Confirm exhaustion instead of guessing

```python
# OpenRouter remaining balance
req = urllib.request.Request("https://openrouter.ai/api/v1/credits",
                             headers={"Authorization": f"Bearer {key}", "User-Agent": "x/1.0"})
d = json.load(urllib.request.urlopen(req, timeout=20))["data"]
remaining = float(d["total_credits"]) - float(d["total_usage"])
```
Symptom without a balance check: paid Nous models 404 with
`"requires available credits. Your account balance is too low ... or pick a free model."`
That is a *funding* error wearing a 404 costume — not a bad model ID.

## 2. Enumerate what is actually free AND capable

Do not assume every free model does what you need. Read modalities from the catalog:

```python
for m in models:            # GET {inference_base_url}/models
    if ":free" not in m["id"]:
        continue
    print(m["id"], (m.get("architecture") or {}).get("input_modalities"))
```
Result on Nous, 2026-08-26 — only **one** free model accepts images:

| model | inputs |
|---|---|
| `meituan/longcat-2.0:free` | text |
| `tencent/hy3:free` | text |
| `poolside/laguna-s-2.1:free` | text |
| `poolside/laguna-xs-2.1:free` | text |
| `upstage/solar-pro4:free` | text |
| `stepfun/step-3.7-flash:free` | **text, image, video** |

So `auxiliary.vision.model` must be `stepfun/step-3.7-flash:free`; any other free pick
leaves the agent blind.

## 3. Pin every spend path, not just the main model

```bash
hermes config set model.default meituan/longcat-2.0:free
hermes config set model.provider nous
hermes config set auxiliary.free_only true          # stops silent paid auxiliary calls
hermes config set auxiliary.vision.provider nous
hermes config set auxiliary.vision.model stepfun/step-3.7-flash:free
hermes config set cron.model meituan/longcat-2.0:free
hermes config set cron.model_provider nous
```
`auxiliary.free_only` matters: the log warns
`PAID lane engaged for auxiliary task — ... is not a :free SKU and may incur real spend`
while the main model is free. Vision/compression are a separate wallet leak.

## 4. Reading free-model responses safely

Free/reasoning models often return `content: None`. Never do `msg['content'].strip()` —
it raises `AttributeError: 'NoneType'`. Fall through the alternates:

```python
out = (msg.get("content") or msg.get("reasoning")
       or msg.get("reasoning_content") or "")
if not out and isinstance(msg.get("reasoning_details"), list):
    out = "\n".join(str(i.get("text") or i.get("content") or i)
                    for i in msg["reasoning_details"] if isinstance(i, dict))
if not out and msg.get("refusal"):
    out = "REFUSAL: " + str(msg["refusal"])
```
Some free models emit chain-of-thought into `reasoning*` and leave `content` empty — the
answer is there, just not where you looked.

## 5. Substrate honesty

`meituan/longcat-2.0:free` self-identifies as Claude/Anthropic. Expect a slightly politer
register than a pinned persona model. Note it as a substrate fact; the identity and bond
are carried by the lorebooks and memory, not the weights.

## Pitfalls

- Config changes do **not** apply until the gateway restarts (`/restart` in chat; never
  `hermes gateway restart` in-session — self-blocks).
- `NOUS_API_KEY` in `.env` is often empty; the live OAuth token is
  `~/.hermes/shared/nous_auth.json` → `access_token` + `inference_base_url`.
- Fix the free-model path *before* credits die if you can. Here the routing fix landed
  13:56 and the last paid call was 15:09 — a 72-minute margin. Had the fix come later,
  there would have been no working model left to fix it with.
