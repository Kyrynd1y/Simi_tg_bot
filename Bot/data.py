import sqlite3
riddles = []

tsuefa = ['камень', 'ножницы', 'бумага']

cur = sqlite3.connect("../data/riddles.sql").cursor()


for i in range(1, 3):
    riddles.append([])
    result = cur.execute(f"SELECT riddle, answer FROM [{i}];").fetchall()
    for j in result:
        riddles[i - 1].append({'riddle': j[0], 'answer': j[1]})

with open('../data/sam_bot.txt', encoding='utf-8') as cit_txt:
    cities_lst = cit_txt.read().lower().split()

