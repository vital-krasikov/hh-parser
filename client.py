import requests
import os
import pprint


class Parser:

    def __init__(self):
        self.vacancies = []
        self.skills = {}

    def get_vacancies(self, query=''):
        # сначала получим id интересующих нас вакансий, общее количество и среднюю зарплату
        # (увы, по api максимум 2000 вакансий)
        self.vacancies.clear()
        salary_min = 0
        salary_max = 0
        q_min = 0
        q_max = 0
        for i in range(21):
            r = requests.get('https://api.hh.ru/vacancies', params={'text': query, 'per_page': 100, 'page': i})
            if r.status_code == requests.codes.ok:
                answer = r.json()
                for vacancy in answer['items']:
                    self.vacancies.append(vacancy['id'])
                    if 'salary' in vacancy and vacancy['salary'] is not None and vacancy['salary']['currency'] == 'RUR':
                        if vacancy['salary']['from'] is not None:
                            salary_min += vacancy['salary']['from']
                            q_min += 1
                        if vacancy['salary']['to'] is not None:
                            salary_max += vacancy['salary']['to']
                            q_max += 1
        return {'found': len(self.vacancies), 'min': salary_min / q_min if q_min != 0 else 0, 'max': salary_max / q_max if q_max != 0 else 0}

    def get_skills(self):
        self.skills.clear()
        for vacancy in self.vacancies:
            r = requests.get('https://api.hh.ru/vacancies/'+vacancy)
            if r.status_code == requests.codes.ok:
                v_json = r.json()
                for skill in v_json['key_skills']:
                    if skill['name'] in self.skills:
                        self.skills[skill['name']] += 1
                    else:
                        self.skills[skill['name']] = 1
        return self.skills