import base64
import hashlib
import hmac
import json
import time

# Example for get balance of accounts in python
import requests

api_key = "60a32b7f365ac600068a2d7b"
api_secret = "306af733-db6e-4a3a-93fe-5570663d0755"
api_passphrase = "dogetothemoon"
url = 'https://openapi-sandbox.kucoin.com/api/v1/accounts'
now = int(time.time() * 1000)
str_to_sign = str(now) + 'GET' + '/api/v1/accounts'
signature = base64.b64encode(hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
passphrase = base64.b64encode(hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest())
headers = {
    "KC-API-SIGN": signature,
    "KC-API-TIMESTAMP": str(now),
    "KC-API-KEY": api_key,
    "KC-API-PASSPHRASE": passphrase,
    "KC-API-KEY-VERSION": '2'
}
response = requests.request('get', url, headers=headers)
print(response.status_code)
print(response.json())

# Example for create deposit addresses in python
url = 'https://openapi-sandbox.kucoin.com/api/v1/deposit-addresses'
now = int(time.time() * 1000)
data = {"currency": "BTC"}
data_json = json.dumps(data)
str_to_sign = str(now) + 'POST' + '/api/v1/deposit-addresses' + data_json
signature = base64.b64encode(
    hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
passphrase = base64.b64encode(
    hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest())
headers = {
    "Content-Type": "application/json",
    "KC-API-SIGN": signature,
    "KC-API-TIMESTAMP": str(now),
    "KC-API-KEY": api_key,
    "KC-API-PASSPHRASE": passphrase,
    "KC-API-KEY-VERSION": '2'
}
response = requests.request('post', url, headers=headers, data=data_json)
print(response.status_code)
print(response.json())