# controller module connecting our parser classes to the web-interface
from flask import Flask, render_template, request
from client_SQLALchemy import SQLAlchemyParser
# from client import Parser

MAX_VACANCIES = 100
MIN_SKILLS_FREQ = 0.1


class Output:

    def __init__(self):
        self.salary = ''
        self.result_list = []


app = Flask(__name__)
p = SQLAlchemyParser(MAX_VACANCIES, MIN_SKILLS_FREQ)
output = Output()


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/form/', methods=['GET'])
def form_get():
    return render_template("form.html", max_vacancies=p.max_vacancies, min_skills_freq=p.min_skills_freq)


# by default our form uses GET method, if it's posted, it means that we pushed "Submit" button either for
# getting vacancies from hh.ru or for saving new values for parameters
@app.route('/form/', methods=['POST'])
def form_post():
    if 'query' not in request.form:
        try:
            new_value = int(request.form['max_vacancies'])
            if 0 <= new_value <= 2000:
                p.max_vacancies = new_value
        except ValueError:
            p.max_vacancies = MAX_VACANCIES
        try:
            new_value = float(request.form['min_skills_freq'])
            if 0 <= new_value <= 1:
                p.min_skills_freq = new_value
        except ValueError:
            p.min_skills_freq = MIN_SKILLS_FREQ

        return render_template("form.html", max_vacancies=p.max_vacancies, min_skills_freq=p.min_skills_freq)
    else:
        text = request.form['query']
        p.query = text

        output.salary = p.get_vacancies(text)
        p.update_skills()

        output.result_list = ['Vacancies analyzed: {},'.format(output.salary['found']),
                       'average salary from {:.2f} to {:.2f}'.format(output.salary['min'], output.salary['max'])]

        return render_template("results.html", result=output.result_list, img_url='/static/img/'+text.replace(' ', '_')+'.png')


@app.route('/contacts/')
def contacts():
    return render_template("contacts.html")


@app.route('/results/')
def results():
    sorted_skills = sorted(p.skills.items(), key=lambda x: x[1], reverse=True)

    for skill in sorted_skills:
        if skill[1] >= p.min_skills_freq * output.salary['found']:
            output.result_list.append(skill[0] + ': ' + str(skill[1]))
        else:
            break

    return render_template("results_full.html", result=output.result_list, img_url='/static/img/'+p.query.replace(' ', '_')+'.png')


if __name__ == "__main__":
    app.run(debug=True)
