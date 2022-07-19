from flask import Flask, render_template, request
from client import Parser

app = Flask(__name__)
p = Parser(100, 0.1)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/form/', methods=['GET'])
def form_get():
    return render_template("form.html", max_vacancies=p.max_vacancies, min_skills_freq=p.min_skills_freq)


@app.route('/form/', methods=['POST'])
def form_post():
    if 'query' not in request.form:
        try:
            new_value = int(request.form['max_vacancies'])
            if 0 <= new_value <= 2000:
                p.max_vacancies = new_value
        except ValueError:
            p.max_vacancies = 100
        try:
            new_value = float(request.form['min_skills_freq'])
            if 0 <= new_value <= 1:
                p.min_skills_freq = new_value
        except ValueError:
            p.min_skills_freq = 0.1

        return render_template("form.html", max_vacancies=p.max_vacancies, min_skills_freq=p.min_skills_freq)
    else:
        text = request.form['query']
        p.query = text

        salary = p.get_vacancies(text)
        skills = p.get_skills()

        sorted_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)

        result_list = ['Проанализировано вакансий: {},'.format(salary['found']),
                       'средняя зарплата от {:.2f} до {:.2f}'.format(salary['min'], salary['max'])]

        for skill in sorted_skills:
            if skill[1] >= p.min_skills_freq * salary['found']:
                result_list.append(skill[0] + ': ' + str(skill[1]))
            else:
                break

        return render_template("results.html", result=result_list)


@app.route('/contacts/')
def contacts():
    return render_template("contacts.html")


@app.route('/results/')
def results():
    return render_template("results.html")


if __name__ == "__main__":
    app.run(debug=True)
