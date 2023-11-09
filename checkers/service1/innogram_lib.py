
import requests

from checklib import *

PORT = 8080

class CheckMachine:
    @property
    def url(self) -> str:
        return f'http://{self.c.host}:{self.port}'

    def __init__(self, checker: BaseChecker):
        self.c = checker
        self.port = PORT

    def register(self, session: requests.Session, username: str, password: str):
        url = f'{self.url}/registration'
        response = session.post(url, data={
            "username": username,
            "password": password
        })
        self.c.assert_neq(session.cookies.get("connect.sid"), None, "connect.sid not set on registration")
        self.c.assert_eq(200, response.status_code, "invalid response on registration")	

    def login(self, session: requests.Session, username: str, password: str, status: Status):
        url = f'{self.url}/login'
        response = session.post(url, data={
            "username": username,
            "password": password
        })
        self.c.assert_eq(200, response.status_code, "invalid response on login", status)

    def create_post(self, session: requests.Session, private: bool, description: str, file: bytes, status: Status):
        url = f'{self.url}/create'
        data = {
            "description": description
        }
        if private:
            data['private'] = 'on'
        files= {'image': ('image.jpg', file, 'multipart/form-data') }
        response = session.post(url, data=data, files=files)
        self.c.assert_eq(200, response.status_code, "failed to create post", status)

    def create_comment(self, session: requests.Session, post_owner: str, post_id: int, text: str, status: Status):
        url = f'{self.url}/api/comment'
        data = {
            "post_owner_username": post_owner,
            "post_id": post_id,
            "comment": text
        }
        response = session.post(url, data=data)
        data = self.c.get_json(response, "Invalid response on adding new comment", status)
        self.c.assert_eq(type(data), dict, "Invalid response on adding new comment", status)
        self.c.assert_eq(data["success"], True, "Adding new comment wasn't success", status)

    def get_post(self, session: requests.Session, username: str, post_id: int, status: Status) -> dict: 
        url = f'{self.url}/api/user/{username}/{post_id}'
        response = session.get(url)
        data = self.c.get_json(response, "Invalid response on getting post", status)
        self.c.assert_eq(type(data), dict, "Invalid response on getting post", status)
        self.c.assert_eq(data['username'], username, "Invalid response on getting post", status)
        self.c.assert_eq(type(data["post"]), dict, "Invalid response on getting post", status)
        return data
    
    def get_newProfiles(self, session: requests.Session, status: Status) -> list: 
        url = f'{self.url}/api/getNewProfiles'
        response = session.get(url)
        data = self.c.get_json(response, "Invalid response on getting newProfiles", status)
        self.c.assert_eq(type(data), list, "Invalid response on getting newProfiles", status)
        return data
    
    def get_searchResult(self, session: requests.Session, query: str, status: Status) -> list: 
        url = f'{self.url}/api/search'
        response = session.get(url, params={"query": query})
        data = self.c.get_json(response, "Invalid response on getting search results", status)
        self.c.assert_eq(type(data), list, "Invalid response on getting search results", status)
        return data

    def get_uploadsFile(self, session: requests.Session, filename: str, status: Status): 
        url = f'{self.url}/uploads?file={filename}'
        response = session.get(url)
        self.c.assert_eq(200, response.status_code, "Invalid response on getting uploads file", status)
        return response
