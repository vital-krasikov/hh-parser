# hh-parser

Application parses hh.ru for vacancies on a given query, counts the number of vacancies, outputs the average salary and the list of key skills for vacancies ordered by descension of frequency. Front-end uses Flask.

Parameters for the run are the maximal number of vacancies to analyze and the minimal frequency of a skill for which we print it. hh.ru provides the possibility to get up to 2000 vacancies via the API. 