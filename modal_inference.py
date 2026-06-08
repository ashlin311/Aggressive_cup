import modal

app = modal.App("Football-Foul-Fest")

def download_model():
    from transformers import AutoModelForCausalLM, AutoTokenizer
    model_name = "Qwen/Qwen2.5-7B-Instruct"
    AutoTokenizer.from_pretrained(model_name)
    AutoModelForCausalLM.from_pretrained(model_name)

image = (
    modal.Image.debian_slim()
    .pip_install("transformers", "torch", "accelerate", "fastapi[standard]")
    .run_function(download_model)
)

@app.cls(gpu="A10G", image=image, scaledown_window=300)
class FoulCupLLM:
    @modal.enter()
    def load_model(self):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        model_name = "Qwen/Qwen2.5-7B-Instruct"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",
            device_map="auto",
        )

    @modal.fastapi_endpoint(method="POST")
    def generate(self, item: dict):
        try:
            prompt = item.get("prompt", "")
            max_new_tokens = item.get("max_new_tokens", 30)

            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ]

            text = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

            output_ids = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
            generated_ids = output_ids[0][len(inputs.input_ids[0]):]
            response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

            return {"text": response.strip()}

        except Exception as e:
            return {"text": "", "error": str(e)}