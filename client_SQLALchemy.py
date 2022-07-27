import requests
from datetime import datetime
from client import AbstractParser
from sqlalchemy import *
from sqlalchemy.orm import create_session
from sqlalchemy.ext.declarative import declarative_base
from wordcloud import WordCloud
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

Base = declarative_base()
engine = create_engine('sqlite:///data.sqlite?check_same_thread=False')
metadata = MetaData(bind=engine)


class Vacancy(Base):

    __table__ = Table('vacancies', metadata, autoload=True)

    def __init__(self, hh_id, name, region, update_time):
        self.hh_id = hh_id
        self.name = name
        self.region = region
        self.update_time = update_time


class Skill(Base):

    __table__ = Table('skills', metadata, autoload=True)

    def __init__(self, name):
        self.name = name


class KeySkill(Base):

    __table__ = Table('key_skills', metadata, autoload=True)

    def __init__(self, vacancy_id, skill_id):
        self.vacancy_id = vacancy_id
        self.skill_id = skill_id


# parser uses SQLAlchemy to get a data from the database
class SQLAlchemyParser(AbstractParser):

    def __init__(self, max_vacancies, min_skills_freq):
        super().__init__(max_vacancies, min_skills_freq)

        self._session = create_session(bind=engine, autocommit=False)

    def set_uptodate_vacancies(self):

        self._uptodate_vacancies = [str(hh_id[0]) for hh_id in self._session.query(Vacancy.hh_id).filter(
            Vacancy.hh_id.in_(self._vacancies))]

    def update_vacancies(self):

        vacancies_to_update = list(set(self._vacancies).difference(set(self._uptodate_vacancies)))

        for vacancy in vacancies_to_update:
            r = requests.get('https://api.hh.ru/vacancies/'+vacancy)
            if r.status_code == requests.codes.ok:
                v_json = r.json()
                self._session.add(
                    Vacancy(v_json['id'], v_json['name'].replace('"', ''), v_json['area']['name'], datetime.now()))

                key_skills = [skill['name'] for skill in v_json['key_skills']]

                skills_to_add = list(set(key_skills).difference(
                    set([name[0] for name in self._session.query(Skill.name).filter(Skill.name.in_(key_skills))])))
                for skill in skills_to_add:
                    self._session.add(Skill(skill.replace('"', '')))
                self._session.commit()

                # and now we add the correspondence of the skills to the vacancy
                for skill in self._session.query(Skill.id).filter(Skill.name.in_(key_skills)):
                    self._session.add(KeySkill(v_json['id'], str(skill[0])))
                self._session.commit()

    def update_skills(self):
        self._skills.clear()

        for skill in self._session.query(Vacancy, Skill.name).join(KeySkill, Vacancy.hh_id == KeySkill.vacancy_id, isouter=True).\
                join(Skill, Skill.id == KeySkill.skill_id).filter(Vacancy.hh_id.in_(self._vacancies)):
            if skill[1] in self._skills:
                self._skills[skill[1]] += 1
            else:
                self._skills[skill[1]] = 1

        wordcloud = WordCloud(width=900, height=500, max_words=1628, relative_scaling=1,
                              normalize_plurals=False).generate_from_frequencies(self._skills)

        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")

        plt.savefig('./static/img/'+self._query.replace(' ', '_')+'.png', transparent=True)

        return self._skills
