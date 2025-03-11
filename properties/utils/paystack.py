import requests
import os
from django.conf import settings

class PaystackService:
    def __init__(self):
        self.secret_key = os.getenv('PAYSTACK_SECRET_KEY')
        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }
        self.base_url = 'https://api.paystack.co'

    def convert_to_kobo(self, amount):
        return int(float(amount) * 100)

    def initialize_transaction(self, email, amount, callback_url, metadata=None):
        url = f"{self.base_url}/transaction/initialize"
        data = {
            'email': email,
            'amount': self.convert_to_kobo(amount),
            'callback_url': callback_url
        }
        if metadata:
            data['metadata'] = metadata

        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code == 200:
            return response.json()['data']
        return None

    def verify_transaction(self, reference):
        url = f"{self.base_url}/transaction/verify/{reference}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()['data']
        return None