from checklib import *
import requests
from bs4 import BeautifulSoup

PORT = 9000

class CheckMachine:
    @property
    def url(self) -> str:
        return f'http://{self.c.host}:{self.port}/'

    def __init__(self, checker: BaseChecker):
        self.c = checker
        self.port = PORT

    @staticmethod
    def session_with_requests():
        return get_initialized_session()

    def register(self, session: requests.Session, username: str, password: str):
        return session.post(self.url + 'register', data={'login': username, 'password': password})

    def login(self, session: requests.Session, username: str, password: str):
        return session.post(self.url + 'login', data={'login': username, 'password': password})

    def does_post_exist_by_title(self, session: requests.Session, title: str, need_body=False):
        res = session.get(self.url)
        soup = BeautifulSoup(res.text, "html.parser")
        for post in soup.findAll('div', class_='ms-2 me-auto'):
            cur_post_id, cur_post_title = post.find('h1', 'fw-bold').text.split('. ')
            body = post.find('h3', class_='body').text
            if cur_post_title == title and need_body:
                return cur_post_id, body
            elif cur_post_title == title:
                return cur_post_id
        return

    def does_post_exist_by_id(self, session: requests.Session, post_id: str, need_body=False):
        res = session.get(self.url)
        soup = BeautifulSoup(res.text, "html.parser")
        for post in soup.findAll('div', class_='ms-2 me-auto'):
            cur_post_id, cur_post_title = post.find('h1', 'fw-bold').text.split('. ')
            body = post.find('h3', class_='body').text
            if cur_post_id == post_id and need_body:
                return cur_post_title, body
            elif cur_post_title == post_id:
                return cur_post_id
        return

    def send_post(self, session: requests.Session, title: str, body: str, username: str) -> requests.Response:
        return session.post(self.url + 'post', data={'title': title, 'body': body, 'available': username})

    def update_post(self, session: requests.Session, new_title: str, new_body: str, post_id: str) -> requests.Response:
        return session.post(self.url + 'update', data={'post_id': post_id, 'title': new_title, 'body': new_body})
