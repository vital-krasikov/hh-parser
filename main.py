from client import Parser
from wordcloud import WordCloud
import matplotlib.pyplot as plt

p = Parser()
# сначала пробовал делать дополнительные параметры для этого метода, чтобы указать, например, город,
# но потом оказалось, что поиск hh отлично работает и с просто добавлением города в поисковую строку,
# а через их справочники куда сложнее регион выбирать
salary = p.get_vacancies('Программист Красноярск')
print('Проанализировано вакансий: {}, средняя зарплата от {:.2f} до {:.2f}'.format(salary['found'],
                                                                                   salary['min'], salary['max']))
skills = p.get_skills()
wordcloud = WordCloud(width=900, height=500, max_words=1628, relative_scaling=1, normalize_plurals=False).generate_from_frequencies(skills)

plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")
plt.show()
