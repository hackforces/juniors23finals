import sys

from checklib import *
import requests
from bs4 import BeautifulSoup
from inno2ch_lib import CheckMachine


class Checker(BaseChecker):
    requests_agents = ['python-requests/2.{}.0'.format(x) for x in range(15, 28)]
    vulns: int = 1
    timeout: int = 5
    uses_attack_data: bool = True

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)
        self.mch = CheckMachine(self)

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except requests.exceptions.ConnectionError:
            self.cquit(Status.DOWN, 'Connection error', 'Got requests connection error')

    def check(self):
        session = self.mch.session_with_requests()
        username, password = rnd_username(salt_length=20), rnd_password(length=20)

        # проверяем, что выдаются токены при регистрации и логине
        try:
            self.mch.register(session, username, password)
        except:
            self.cquit(Status.DOWN)

        token_register = session.cookies.get('token', '')
        self.assert_neq(token_register, '', 'no authentication token provided after registration')
        session.close()

        session = self.mch.session_with_requests()
        try:
            self.mch.login(session, username, password)
        except:
            self.cquit(Status.DOWN)
        token_login = session.cookies.get('token', '')
        self.assert_neq(token_login, '', 'no authentication token provided after login')

        # проверяем, что токен, отправленный при регистрации соответсвует токену при логине
        self.assert_eq(token_login, token_register, 'Different tokens after registration and login')

        # проверяем, что сайт вообще открывается
        res = session.get(self.mch.url)
        soup = BeautifulSoup(res.text, "html.parser")
        # проверяем, что комментарии создаются
        for post in soup.findAll('li', class_='list-group-item d-flex justify-content-between align-items-start'):
            post_id = post.find('h1', 'fw-bold').text.split('. ')[0]
            session.post(self.mch.uri, data={'post_id': post_id, 'comment': rnd_string(length=50)})
        # проверяем, что новые посты создаются
        title, body = rnd_string(length=10), rnd_string(length=50)
        self.mch.send_post(session, title, body, username)
        post_id = self.mch.does_post_exist_by_title(session, title)
        new_title, new_body = rnd_string(length=10), rnd_string(length=50)
        res = self.mch.update_post(session, new_title, new_body, post_id)
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
        session = self.mch.session_with_requests()
        username, password = rnd_username(salt_length=30), rnd_password(length=30)
        title = rnd_password(length=10)
        try:
            self.mch.register(session, username, password)
        except:
            self.cquit(Status.DOWN, "Cannot register")
        self.mch.send_post(session, title, flag, username)
        post_id, post_body = self.mch.does_post_exist_by_title(session, title)
        self.cquit(Status.OK, username, f'{username}:{password}:{post_id}:{title}:{post_body}')

    def get(self, flag_id: str, flag: str, vuln: str):
        session = self.mch.session_with_requests()
        username, password, post_id, title = flag_id.split(':')

        self.mch.login(session, username, password)
        temp_post_id, flag_by_title = self.mch.does_post_exist_by_title(session, title, need_body=True)
        temp_post_title, flag_by_id = self.mch.does_post_exist_by_id(session, post_id, need_body=True)
        if flag_by_title != flag and flag != flag_by_id:
            self.cquit(Status.MUMBLE, 'Saved invalid flag')
        self.cquit(Status.OK)


if __name__ == '__main__':
    c = Checker(sys.argv[2])

    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception() as e:
        cquit(Status(c.status), c.public, c.private)
