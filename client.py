import requests
import os


class Parser:

    def authorize(self):
        params = dict(response_type = "code", client_id = "57667788")


    def set_token(self):
        if "token" in os.listdir():
        else:
            r = requests.get("https://hh.ru/oauth/authorize",)

    def get_vacancies(self, name='', city=''):
        r = requests.get('https://hh.ru/vacancies')
