from lib import *

print(
    '''[CHECK] 5. [Уязвимость №3, PWN Medium] Простая прога на C, считающая CRC32 - подаётся комментарий, можно переполнить буфер и получить RCE, после чего выгрузить БД postgres.''')
s = requests.Session()
username = random_alphanumeric_string(25)
password = random_alphanumeric_string(25)

register(s, username, password)
login(s, username, password)
task_id = new_task(s, 'helloasdasdf', 'goodbye9289239')

if comment_task(s, task_id, 'abcdhello_short') is True:
    print('Got good hash for short string [ok]')
else:
    exit(0)

if comment_task(s, task_id, 'abcdhello_long' * 100) is False:
    print('Got bad (empty) hash for long string [ok]')
else:
    exit(0)
