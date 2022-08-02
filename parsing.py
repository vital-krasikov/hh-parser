# contains main classes for parsing the website
import requests
import sqlite3 # currently uses only SQLite for storing the data
from datetime import datetime
from abc import ABC, abstractmethod
import itertools
from wordcloud import WordCloud
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# abstract ancestor to different parsers
# we assume that its descendants will differ in methods of getting a data from the database
class AbstractParser(ABC):

    def __init__(self, max_vacancies, min_skills_freq):
        self._vacancies = []  # list of all the vacancies parser get from hh.ru
        self._uptodate_vacancies = []   # this field contains the vacancies we have already download, so the data on
        # them we load from the database, not the website
        self._skills = {}  # dictionary containing the skills with their frequencies
        self._query = ''  # query which is used to get vacancies from hh.ru
        self._max_vacancies = max_vacancies  # maximal number of vacancies to analyze
        self._min_skills_freq = min_skills_freq  # minimal frequency of the skill to print

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

    def _get_skills(self):
        return self._skills

    skills = property(
        fget=_get_skills
    )

    def get_vacancies(self, query=''):
        # at first we get id's of all the vacancies we are interested in, their count and the mean salary
        # unfortunately it's only 2000 vacancies max via the api
        self._query = query
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
        self.set_uptodate_vacancies()
        self.update_vacancies()
        return {'found': len(self._vacancies), 'min': salary_min / q_min if q_min != 0 else 0, 'max': salary_max / q_max if q_max != 0 else 0}

    # set_uptodate_vacancies() method compares the list of vacancies to the database and finds those we consider
    # up-to-date (now it's all the vacancies presented in the database, but it's possible to narrow down
    # to vacancies downloaded after some date since we store the dates in the database)
    @abstractmethod
    def set_uptodate_vacancies(self):
        pass

    # update_vacancies() updates the data on all the vacancies in the database which are not up-to-date already
    @abstractmethod
    def update_vacancies(self):
        pass

    # update_skills() updates the data on used skills based on the skills we saved to the database
    @abstractmethod
    def update_skills(self):
        pass


# this parser uses straight queries to the database instead of ORM
class Parser(AbstractParser):

    def __init__(self, max_vacancies, min_skills_freq):
        super().__init__(max_vacancies, min_skills_freq)
        self._conn = sqlite3.connect('data.sqlite', check_same_thread=False)

    def set_uptodate_vacancies(self):

        cursor = self._conn.cursor()

        cursor.execute('SELECT hh_id FROM vacancies WHERE hh_id IN '+str(tuple(self._vacancies))+';')
        result = cursor.fetchall()

        self._uptodate_vacancies = [str(vacancy) for vacancy in list(itertools.chain(*result))]

    def update_vacancies(self):
        vacancies_to_update = list(set(self._vacancies).difference(set(self._uptodate_vacancies)))
        cursor = self._conn.cursor()
        for vacancy in vacancies_to_update:
            r = requests.get('https://api.hh.ru/vacancies/'+vacancy)
            if r.status_code == requests.codes.ok:
                v_json = r.json()
                cursor.execute('INSERT INTO vacancies (hh_id, name, region, update_time) VALUES (' +
                               v_json['id'] + ', "' + v_json['name'].replace('"', '') + '", "' + v_json['area']['name'] + '", "' +
                               str(datetime.now()) + '");')

                key_skills = [skill['name'] for skill in v_json['key_skills']]
                cursor.execute('SELECT name FROM skills WHERE name '+('IN ' + str(tuple(key_skills))
                                                                      if len(key_skills) != 1 else '= "'+str(key_skills[0])+'"')+';')
                result = cursor.fetchall()

                skills_to_add = list(set(key_skills).difference(set(list(itertools.chain(*result)))))
                for skill in skills_to_add:
                    cursor.execute('INSERT INTO skills (name) VALUES ("' + skill.replace('"', '') + '");')

                # and now we add the correspondence of the skills to the vacancy
                cursor.execute('SELECT id FROM skills WHERE name '+('IN ' + str(tuple(key_skills))
                                                                      if len(key_skills) != 1 else '= "'+str(key_skills[0])+'"')+';')
                result = cursor.fetchall()
                skills = list(itertools.chain(*result))
                for skill in skills:
                    cursor.execute('INSERT INTO key_skills (vacancy_id, skill_id) VALUES (' + v_json['id'] + ', ' + str(skill) + ');')

        self._conn.commit()

    def update_skills(self):
        self._skills.clear()
        cursor = self._conn.cursor()
        cursor.execute('SELECT skills.name \
                        FROM vacancies \
                        LEFT JOIN key_skills ON vacancies.hh_id = key_skills.vacancy_id \
                        INNER JOIN skills ON key_skills.skill_id = skills.id \
                        WHERE vacancies.hh_id IN ' + str(tuple(self._vacancies)) + ';')
        result = cursor.fetchall()
        for skill in list(itertools.chain(*result)):
            if skill in self._skills:
                self._skills[skill] += 1
            else:
                self._skills[skill] = 1

        wordcloud = WordCloud(width=900, height=500, max_words=1628, relative_scaling=1,
                              normalize_plurals=False).generate_from_frequencies(self._skills)

        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")

        plt.savefig('./static/img/'+self._query.replace(' ', '_')+'.png', transparent=True)

        return self._skills
