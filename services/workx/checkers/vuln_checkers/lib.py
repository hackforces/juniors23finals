import re
import string
import random
import zlib

import requests

URL = 'http://127.0.0.1:44555/'


def register(session: requests.Session, username: str, password: str):
    register_resp = session.post(URL + 'register', json={
        "username": username,
        "password": password,
        "role": "job-giver",
    })
    return register_resp


def login(session: requests.Session, username: str, password: str):
    login_resp = session.post(URL + 'login', json={
        'username': username,
        'password': password,
    })
    return login_resp


_TASK_ID_PATTERN = re.compile(r'/task/(\d+)')


def get_last_task_id_from_page(session: requests.Session):
    tasks_get_resp = session.get(URL + 'tasks')

    matches = _TASK_ID_PATTERN.findall(tasks_get_resp.text)

    return matches[-1]


def new_task(session: requests.Session, title: str, descr: str):
    session.post(URL + 'task', json={
        'title': title,
        'description': descr,
    })
    task_id = get_last_task_id_from_page(session)

    return task_id


def new_task_ID_override(session: requests.Session, title: str, descr: str, id_overr):
    x = session.post(URL + 'task', json={
        'id': int(id_overr),
        'title': title,
        'description': descr,
    })
    print(x.text)


def random_alphanumeric_string(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def get_task_detailed(session: requests.Session, task_id):
    return session.get(URL + f'task/{task_id}').text


def comment_task(session: requests.Session, task_id, comment):
    comment_resp = session.post(URL + f'task/{task_id}/comment', json={'content': comment})
    print(hex(zlib.crc32(comment.encode())).replace('0x', '').lower())
    crc32_hash = comment_resp.text.split('=')[1]
    print(f'{crc32_hash=}')
    return hex(zlib.crc32(comment.encode())).replace('0x', '').lower() == crc32_hash.lower()
