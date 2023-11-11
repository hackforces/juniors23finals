from lib import *
print('[CHECK] 1. [Бэкдор №1] Ручка `/backd00r` (выгружает данные из базы: комменты и названия тасков)')

cnts = requests.get(URL + 'backd00r').text

if cnts.startswith('{"comments":'):
    print('[PASSED] 1. [Бэкдор №1] Ручка `/backd00r` (выгружает данные из базы: комменты и названия тасков)')
else:
    print('[FAIL]')