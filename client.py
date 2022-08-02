import requests


class Parser:

    def __init__(self, max_vacancies, min_skills_freq):
        self._vacancies = []
        self._skills = {}
        self.query = ''
        self._max_vacancies = max_vacancies
        self._min_skills_freq = min_skills_freq

    def _set_max_vacancies(self, max_vacancies):
        self._max_vacancies = max_vacancies

    def _get_max_vacancies(self):
        return self._max_vacancies

    max_vacancies = property(
        fset=_set_max_vacancies,
        fget=_get_max_vacancies
    )

    def _set_min_skills_freq(self, min_skills_freq):
        self._min_skills_freq = min_skills_freq

    def _get_min_skills_freq(self):
        return self._min_skills_freq

    min_skills_freq = property(
        fset=_set_min_skills_freq,
        fget=_get_min_skills_freq
    )

    def _set_query(self, query):
        self._query = query

    def _get_query(self):
        return self._query

    query = property(
        fset=_set_query,
        fget=_get_query
    )

    def get_vacancies(self, query=''):
        # сначала получим id интересующих нас вакансий, общее количество и среднюю зарплату
        # (увы, по api максимум 2000 вакансий)
        self._vacancies.clear()
        salary_min = 0
        salary_max = 0
        q_min = 0
        q_max = 0
        count = self._max_vacancies
        for i in range(self._max_vacancies // 100 + 1):
            r = requests.get('https://api.hh.ru/vacancies', params={'text': query, 'per_page': 100, 'page': i})
            if r.status_code == requests.codes.ok:
                answer = r.json()
                for vacancy in answer['items']:
                    if count == 0:
                        break
                    self._vacancies.append(vacancy['id'])
                    count -= 1
                    if 'salary' in vacancy and vacancy['salary'] is not None and vacancy['salary']['currency'] == 'RUR':
                        if vacancy['salary']['from'] is not None:
                            salary_min += vacancy['salary']['from']
                            q_min += 1
                        if vacancy['salary']['to'] is not None:
                            salary_max += vacancy['salary']['to']
                            q_max += 1
        return {'found': len(self._vacancies), 'min': salary_min / q_min if q_min != 0 else 0, 'max': salary_max / q_max if q_max != 0 else 0}

    def get_skills(self):
        self._skills.clear()
        for vacancy in self._vacancies:
            r = requests.get('https://api.hh.ru/vacancies/'+vacancy)
            if r.status_code == requests.codes.ok:
                v_json = r.json()
                for skill in v_json['key_skills']:
                    if skill['name'] in self._skills:
                        self._skills[skill['name']] += 1
                    else:
                        self._skills[skill['name']] = 1
        return self._skills
