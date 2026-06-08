# modal_inference.py — Implementation Guide

Build a Modal app that serves **Qwen/Qwen2.5-7B-Instruct** on an A10G GPU as a POST endpoint.

---

## File Structure (4 sections)

```
1. Imports & Modal app/image definition
2. Class with @app.cls decorator
3. Three lifecycle methods: @modal.build → @modal.enter → @modal.fastapi_endpoint
4. (That's it — single class, single endpoint)
```

---

## Section 1 — Imports & Modal Setup

You need exactly these:

```python
import modal
```

Then define two things:

| Variable | What it does |
|----------|-------------|
| `app` | `modal.App("foul-cup")` — names your Modal deployment |
| `image` | Container image with pip dependencies |

**Image dependencies** (install via `modal.Image.debian_slim().pip_install(...)`):

| Package | Why |
|---------|-----|
| `transformers` | Model loading + tokenizer |
| `torch` | PyTorch backend |
| `accelerate` | `device_map="auto"` support |

---

## Section 2 — The Class

Decorate a class with `@app.cls(...)`. Key parameters:

| Parameter | Value | Why |
|-----------|-------|-----|
| `gpu` | `"A10G"` | 24GB VRAM, enough for 7B at bfloat16 (~14GB) |
| `image` | Your image variable | Container dependencies |
| `container_idle_timeout` | `300` | Keep warm for 5 min between requests (reduces cold starts) |

---

## Section 3 — Three Methods

### Method 1: `@modal.build()` — Pre-download weights

> [!TIP]
> This runs **during image build**, not at request time. The weights get cached in the container image so `@modal.enter()` loads from local disk instead of downloading from HuggingFace every cold start.

What to do inside:
- Import `AutoModelForCausalLM` and `AutoTokenizer` from `transformers`
- Call `.from_pretrained("Qwen/Qwen2.5-7B-Instruct")` on both — just to trigger the download
- You don't need to keep references; the files land in the HF cache

### Method 2: `@modal.enter()` — Load model into GPU

> [!IMPORTANT]
> This runs **once per container start**, NOT per request. Store the model and tokenizer as `self.model` and `self.tokenizer`.

What to do inside:
```
1. Import AutoModelForCausalLM, AutoTokenizer
2. Load tokenizer: AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
3. Load model: AutoModelForCausalLM.from_pretrained(
       "Qwen/Qwen2.5-7B-Instruct",
       torch_dtype="auto",          # picks bfloat16 automatically
       device_map="auto"            # places on GPU
   )
4. Store as self.model, self.tokenizer
```

### Method 3: `@modal.fastapi_endpoint(method="POST")` — The endpoint

> [!IMPORTANT]
> This is what [tactics.py](file:///c:/Users/USER/Desktop/Projects/Aggressive_cup/tactics.py) calls via HTTP POST.

**Input contract** (what `tactics.py` sends):
```json
{
    "prompt": "You are the dirty tactics coach of Argentina...",
    "max_new_tokens": 20
}
```

**Output contract** (what `tactics.py` expects):
```json
{
    "text": "FOUL DIVE INTIMIDATE"
}
```

**What to do inside:**

```
1. Extract prompt and max_new_tokens from the item dict
2. Default max_new_tokens to 30 if not provided
3. Build the chat messages list for Qwen's chat template:
   messages = [
       {"role": "system", "content": "You are a helpful assistant."},
       {"role": "user", "content": prompt}
   ]
4. Apply the chat template:
   text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
5. Tokenize:
   inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
6. Generate:
   output_ids = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
7. Slice off the input tokens to get only the generated part:
   generated_ids = output_ids[0][len(inputs.input_ids[0]):]
8. Decode:
   response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
9. Return {"text": response.strip()}
```

> [!WARNING]
> Wrap the generation in a `try/except` and return `{"text": "", "error": str(e)}` on failure so `tactics.py`'s fallback logic can kick in.

---

## Complete Skeleton

```python
import modal

app = modal.App("foul-cup")

image = modal.Image.debian_slim().pip_install(
    # your 3 dependencies here
)

@app.cls(gpu=___, image=___, container_idle_timeout=___)
class FoulCupLLM:

    @modal.build()
    def download_model(self):
        # Pre-download weights into the image cache
        ...

    @modal.enter()
    def load_model(self):
        # Load model + tokenizer, store as self.model, self.tokenizer
        ...

    @modal.fastapi_endpoint(method="POST")
    def generate(self, item: dict):
        # Extract prompt, generate, return {"text": ...}
        ...
```

---

## Deployment & Testing

### Deploy
```bash
modal deploy modal_inference.py
```

This prints a URL like:
```
https://your-username--foul-cup-foulcupllm-generate.modal.run
```

### Store the URL
Set it as an environment variable in your HF Space Secrets:
```
MODAL_ENDPOINT_URL=https://your-username--foul-cup-foulcupllm-generate.modal.run
```

### Test with curl
```bash
# Test action generation (short response)
curl -X POST YOUR_URL \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Choose one action: FOUL DIVE INTIMIDATE. Reply with one word.", "max_new_tokens": 10}'

# Test commentary generation (longer response)
curl -X POST YOUR_URL \
  -H "Content-Type: application/json" \
  -d '{"prompt": "45 - Red Card by Ramos for Argentina in the Foul Cup. One sentence of outraged football commentary.", "max_new_tokens": 60}'
```

### Local testing (before deploying)
```bash
modal serve modal_inference.py
```
This runs a temporary local endpoint for testing without deploying permanently.

---

## Integration with tactics.py

Your endpoint is called by [_call_modal()](file:///c:/Users/USER/Desktop/Projects/Aggressive_cup/tactics.py#L48-L64) in tactics.py:

```python
resp = requests.post(
    MODAL_ENDPOINT_URL,
    json={"prompt": prompt, "max_new_tokens": max_new_tokens},
    timeout=10,
)
return resp.json()["text"]
```

The three call sites with their expected `max_new_tokens`:

| Caller | max_new_tokens | Expected output |
|--------|---------------|----------------|
| `get_actions()` | 20 | `"FOUL DIVE INTIMIDATE"` (3 action words) |
| `get_major_commentary()` | 60 | One sentence of commentary |
| `get_post_match_report()` | 120 | 2-3 sentences of pundit report |

---

## Gotchas

> [!CAUTION]
> **Don't forget `skip_special_tokens=True`** in the decode step. Without it, the response will contain `<|endoftext|>` and other Qwen special tokens that will break action parsing in `tactics.py`.

> [!WARNING]
> **First deploy takes ~5-10 minutes** because `@modal.build()` downloads the full model weights (~14GB). Subsequent deploys reuse the cached image and are fast.

> [!NOTE]
> **`torch_dtype="auto"`** lets the model config pick `bfloat16` automatically. You can also explicitly pass `torch.bfloat16` if you prefer. Either way, VRAM usage will be ~14GB on the 24GB A10G.
