import requests

def test_model(model_name, prompt):
    payload = {
        "model": model_name,
        "prompt": prompt
    }
    response = requests.post("http://192.168.50.12:11434/api/generate", json=payload)
    return response.json().get("response", "Pas de réponse")

prompt = "Explique-moi les bases de Docker."
result_llama3 = test_model("llama3:latest", prompt)
result_llama3_2 = test_model("llama3.2:latest", prompt)

print("Llama3 :\n", result_llama3)
print("\nLlama3.2 :\n", result_llama3_2)
