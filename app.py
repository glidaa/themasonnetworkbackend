from flask import Flask, request, jsonify
import torch
from transformers import LlamaTokenizer, LlamaForCausalLM

app = Flask(__name__)

# Load the model and tokenizer
tokenizer = LlamaTokenizer.from_pretrained('/app/llama/weights')
model = LlamaForCausalLM.from_pretrained('/app/llama/weights')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    input_text = data.get('text', '')
    inputs = tokenizer(input_text, return_tensors='pt')
    outputs = model.generate(**inputs)
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return jsonify({'generated_text': generated_text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
