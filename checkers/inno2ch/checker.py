import random
import sys

from checklib import *
import requests
from bs4 import BeautifulSoup


class Checker(BaseChecker):
    requests_agents = ['python-requests/2.{}.0'.format(x) for x in range(15, 28)]
    vulns: int = 1
    timeout: int = 15
    uses_attack_data: bool = True

    def __init__(self, host: str, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)
        self.host = host
        self.uri = f'http://{self.host}/'

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except requests.exceptions.ConnectionError:
            self.cquit(Status.DOWN, 'Connection error', 'Got requests connection error')

    def session_with_requests(self):
        sess = get_initialized_session()
        if random.randint(0, 1) == 1:
            sess.headers['User-Agent'] = random.choice(self.requests_agents)
        return sess

    def register(self, session: requests.Session, username: str, password: str):
        return session.post(self.uri + 'register', data={'login': username, 'password': password})

    def login(self, session: requests.Session, username: str, password: str):
        return session.post(self.uri + 'login', data={'login': username, 'password': password})

    def does_post_exist_by_title(self, session: requests.Session, title: str, need_body=False):
        res = session.get(self.uri)
        soup = BeautifulSoup(res.text, "html.parser")
        for post in soup.findAll('div', class_='ms-2 me-auto'):
            cur_post_id, cur_post_title = post.find('h1', 'fw-bold').text.split('. ')
            body = post.find('h3', class_='body').text
            if cur_post_title == title and body:
                return cur_post_id, body
            elif cur_post_title == title:
                return cur_post_id
        else:
            self.cquit(Status.MUMBLE)

    def does_post_exist_by_id(self, session: requests.Session, post_id: str, need_body=False):
        res = session.get(self.uri)
        soup = BeautifulSoup(res.text, "html.parser")
        for post in soup.findAll('div', class_='ms-2 me-auto'):
            cur_post_id, cur_post_title = post.find('h1', 'fw-bold').text.split('. ')
            body = post.find('h3', class_='body').text
            if cur_post_title == post_id and need_body:
                return cur_post_id, body
            elif cur_post_title == post_id:
                return cur_post_id
        else:
            self.cquit(Status.MUMBLE)

    def send_post(self, session: requests.Session, title: str, body: str, username: str) -> requests.Response:
        return session.post(self.uri + 'post', data={'title': title, 'body': body, 'available': username})

    def update_post(self, session: requests.Session, new_title: str, new_body: str, post_id: str) -> requests.Response:
        return session.post(self.uri + 'update', data={'post_id': post_id, 'title': new_title, 'body': new_body})

    def check(self):
        session = self.session_with_requests()

        username, password = rnd_username(salt_length=20), rnd_password(length=20)

        # проверяем, что выдаются токены при регистрации и логине
        try:
            self.register(session, username, password)
        except:
            self.cquit(Status.DOWN)

        token_register = session.cookies.get('token', '')
        self.assert_neq(token_register, '', 'no authentication token provided after registration')
        session.close()

        session = self.session_with_requests()
        try:
            self.login(session, username, password)
        except:
            self.cquit(Status.DOWN)
        token_login = session.cookies.get('token', '')
        self.assert_neq(token_login, '', 'no authentication token provided after login')

        # проверяем, что токен, отправленный при регистрации соответсвует токену при логине
        self.assert_eq(token_login, token_register, 'Different tokens after registration and login')

        # проверяем, что сайт вообще открывается
        res = session.get(self.uri)
        soup = BeautifulSoup(res.text, "html.parser")
        # проверяем, что комментарии создаются
        for post in soup.findAll('li', class_='list-group-item d-flex justify-content-between align-items-start'):
            post_id = post.find('h1', 'fw-bold').text.split('. ')[0]
            session.post(self.uri, data={'post_id': post_id, 'comment': rnd_string(length=50)})
        # проверяем, что новые посты создаются
        title, body = rnd_string(length=10), rnd_string(length=50)
        self.send_post(session, title, body, username)
        post_id = self.does_post_exist_by_title(session, title)
        new_title, new_body = rnd_string(length=10), rnd_string(length=50)
        res = self.update_post(session, new_title, new_body, post_id)
        self.assert_neq(res, None, 'Post is not created')
        # проверяем, что пост поменял содержимое
        soup = BeautifulSoup(res.text, "html.parser")
        for post in soup.findAll('li', class_='list-group-item d-flex justify-content-between align-items-start'):
            cur_post_id, cur_post_title = post.find('h1', 'fw-bold').text.split('. ')
            if post_id == cur_post_id:
                if title == cur_post_title:
                    self.cquit(Status.OK)
        self.cquit(Status.MUMBLE)

    def put(self, flag_id: str, flag: str, vuln: str):
        session = self.session_with_requests()
        username, password = rnd_username(salt_length=30), rnd_password(length=30)
        title = rnd_password(length=10)
        try:
            self.register(session, username, password)
        except:
            self.cquit(Status.DOWN, "Cannot register")
        self.send_post(session, title, flag, username)
        post_id, post_body = self.does_post_exist_by_title(session, title)
        self.cquit(Status.OK, username, f'{username}:{password}:{post_id}:{title}:{post_body}')

    def get(self, flag_id: str, flag: str, vuln: str):
        session = self.session_with_requests()
        username, password, post_id, title = flag_id.split(':')

        self.login(session, username, password)
        temp_post_id, flag_by_title = self.does_post_exist_by_title(session, title, need_body=True)
        temp_post_title, flag_by_id = self.does_post_exist_by_id(session, post_id, need_body=True)
        if flag_by_title != flag and flag != flag_by_id:
            self.cquit(Status.MUMBLE, 'Saved invalid flag')
        self.cquit(Status.OK)


if __name__ == '__main__':
    c = Checker(sys.argv[2])

    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception() as e:
        cquit(Status(c.status), c.public, c.private)
