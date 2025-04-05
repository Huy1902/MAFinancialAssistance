import requests

url = 'https://r.jina.ai/https://www.vietcombank.com.vn/'
headers = {
    'Authorization': 'jina_1a194abb2198430cbf3430c9b443c5edPGseXvQXH6WRJsSI1Lv_H4ojSXXb'
}
try:
    response = requests.get(url, headers=headers, timeout=10)
    print(response.text)
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
