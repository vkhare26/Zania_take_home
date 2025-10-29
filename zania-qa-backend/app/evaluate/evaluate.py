import requests, json

url = "http://127.0.0.1:8000/qa"
files = {
    "document": open("soc2-type2.pdf", "rb"),      
    "questions": open("questions.json", "rb")
}
resp = requests.post(url, files=files)
print(json.dumps(resp.json(), indent=2))
