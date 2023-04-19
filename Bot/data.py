import sqlite3

riddles = []

tsuefa = ['камень', 'ножницы', 'бумага']

tsuefa_rules = 'Камень-ножницы-бумага – это простая игра, которая может быть играна двумя или более игроками.' \
               'Цель игры – победить другого игрока, показав лучшую комбинацию из трех вариантов: камень, ножницы или бумага.' \
               'Каждый игрок делает один из этих выборов и показывает другому игроку.Победитель определяется по следующим правилам:' \
               '-Камень побеждает ножницы;' \
               '-Ножницы побеждают бумагу;' \
               '-Бумага побеждает камень.' \
               'Если оба игрока показали одинаковые варианты, то игра считается ничьей.'

cities_rules = 'Игра в города – это игра для двух или более игроков, которая предполагает называние городов, начинающихся на последнюю букву города, названного предыдущим игроком.' \
               'Правила игры в города достаточно просты. Игроки должны по очереди называть города, начинающиеся на последнюю букву города, названного предыдущим игроком. Например, если первый игрок называет город «Нью-Йорк», то второй игрок должен назвать город, начинающийся на букву «К», например, «Калининград». Затем третий игрок должен назвать город, начинающийся на букву «Д», и так далее.' \
               'Если игрок не может назвать город или называет несуществующий город, он проигрывает. Игра продолжается до тех пор, пока не останется один игрок, который будет победителем.'

qst_rules = 'Загадки – это игра, в которой один игрок задает вопросы другому игроку, а последний пытается отгадать правильный ответ. Игра может происходить в формате диалога, когда один игрок задает вопрос, а другой дает ответ, или в виде игры, когда один игрок задает загадку, а другой пытается ее разгадать. Правила игры в загадки просты: игроки должны придумывать или использовать загадки, которые можно разгадать. Ответ должен быть однозначным, так что игроки должны придумывать загадки с простыми ответами. Когда игрок разгадал загадку, он должен правильно ответить, чтобы получить очки.'

cur = sqlite3.connect("../data/riddles.db").cursor()

for i in range(1, 3):
    riddles.append([])
    result = cur.execute(f"SELECT riddle, answer FROM [{i}];").fetchall()
    for j in result:
        riddles[i - 1].append({'riddle': j[0], 'answer': j[1]})

with open('../data/sam_bot.txt', encoding='utf-8') as cit_txt:
    cities_lst = cit_txt.read().lower().split()
