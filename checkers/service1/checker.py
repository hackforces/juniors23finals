#!/usr/bin/env python3
import sys
import os
import requests
import random

from checklib import *
from innogram_lib import *
from pathlib import Path

BASE_DIR = Path(__file__).absolute().resolve().parent
images_path = BASE_DIR / 'images/'


class Checker(BaseChecker):
    vulns: int = 2
    timeout: int = 5
    uses_attack_data: bool = True

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)
        self.mch = CheckMachine(self)

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except requests.exceptions.ConnectionError:
            self.cquit(Status.DOWN, 'Connection error', 'Got requests.exceptions.ConnectionError')

    def check(self):
        session = self.get_initialized_session()
        username, password = rnd_username(), rnd_password() 

        description = rnd_string(20)
        comment = rnd_string(15)

        self.mch.register(session, username, password)
        self.mch.login(session, username, password, Status.MUMBLE)
        newProfiles = self.mch.get_newProfiles(session, Status.MUMBLE)
        userFound = False
        for profile in newProfiles:
            if username == profile["username"]:
                userFound = True
                break
        self.assert_eq(userFound, True, "No checker user found in new profiles", Status.CORRUPT)

        image_files = [f for f in os.listdir(images_path) if os.path.isfile(os.path.join(images_path, f))]
        random_image = random.choice(image_files)
        with open(f'{images_path}/{random_image}', 'rb') as f:
            image_data = f.read()
        self.mch.create_post(session, private=False, description=description, file=image_data, status=Status.MUMBLE)
        self.mch.create_comment(session, post_owner=username, post_id=1, text=comment, status=Status.MUMBLE)

        data = self.mch.get_post(session, username=username, post_id=1, status=Status.MUMBLE)
        self.assert_eq(data["post"]["description"], description, "Description value is invalid", Status.CORRUPT)
        self.assert_eq(data["comments"][0]["comment"], comment, "Comment text is invalid", Status.CORRUPT)

        data = self.mch.get_uploadsFile(session, filename=data["post"]["image"], status=Status.MUMBLE)
        self.assert_in('image', data.headers['Content-Type'], "Post image retrieval attempt returned nonimage file", Status.MUMBLE)

        postsFound = self.mch.get_searchResult(session, query=description, status=Status.MUMBLE)
        postFound = False
        for post in postsFound:
            if description == post["description"]:
                postFound = True
                break
        self.assert_eq(postFound, True, "No post found using search", Status.CORRUPT)
        self.cquit(Status.OK)

        #check if comment posted == comment gotten + desciption == description + search working + image viewing


    def put(self, flag_id: str, flag: str, vuln: str):
        session = self.get_initialized_session()
        username, password = rnd_username(), rnd_password()
        self.mch.register(session, username, password)
        self.mch.login(session, username, password, Status.MUMBLE)
        image_files = [f for f in os.listdir(images_path) if os.path.isfile(os.path.join(images_path, f))]
        random_image = random.choice(image_files)
        with open(f'{images_path}/{random_image}', 'rb') as f:
            image_data = f.read()
        post_id = 1
        if vuln == "1":
            for i in range(random.randint(1, 4)):
                description = rnd_string(20)
                self.mch.create_post(session, private=False, description=description, file=image_data, status=Status.MUMBLE)
                random_image = random.choice(image_files)
                with open(f'{images_path}/{random_image}', 'rb') as f:
                    image_data = f.read()
                post_id += 1
            self.mch.create_post(session, private=True, description=flag, file=image_data, status=Status.MUMBLE)
            # self.cquit(Status.OK, username, f'{username}:{password}:{post_id}')
        elif vuln == "2":
            description = rnd_string(20)
            self.mch.create_post(session, private=True, description=description, file=image_data, status=Status.MUMBLE)
            self.mch.create_comment(session, post_owner=username, post_id=1, text=flag, status=Status.MUMBLE)
        self.cquit(Status.OK, f"{username}", f'{username}:{password}:{post_id}')

    def get(self, flag_id: str, flag: str, vuln: str):
        session = self.get_initialized_session()
        username, password, post_id = flag_id.split(':')
        self.mch.login(session, username, password, Status.CORRUPT)
        data = self.mch.get_post(session, username=username, post_id=post_id, status=Status.CORRUPT)
        if vuln == "1":
            self.assert_eq(data["post"]["description"], flag, "Description value is invalid", Status.CORRUPT)
        elif vuln == "2":
            self.assert_eq(data["comments"][0]["comment"], flag, "Comment value is invalid", Status.CORRUPT)
        self.cquit(Status.OK)
        # + check access with search

if __name__ == '__main__':
    c = Checker(sys.argv[2])
    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)
