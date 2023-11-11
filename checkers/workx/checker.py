#!/usr/bin/env python3
import json
import random
import re
import sys
import zlib

import requests
from checklib import *


class Checker(BaseChecker):
    vulns: int = 2
    timeout: int = 10
    uses_attack_data: bool = True
    port: int = 44555
    service_name: str = "workworkwork"

    def __init__(self, host: str, *args, **kwargs):
        super(Checker, self).__init__(host)
        self.host = host
        self.url = f'http://{self.host}:{self.port}/'
        self._TASK_ID_PATTERN = re.compile(r'/task/(\d+)')

    @property
    def headers(self):
        return {
            'Content-Type': 'application/json'
        }

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except requests.exceptions.ConnectionError:
            self.cquit(Status.DOWN, 'Connection error', 'Got requests connection error')

    def register(self, session: requests.Session, username: str, password: str):
        # Register account
        register_resp = session.post(self.url + 'register', headers=self.headers, json={
            "username": username,
            "password": password,
            "role": "job-giver",
        })
        self.assert_eq(register_resp.status_code, 201, 'Failed to register')
        self.assert_eq(register_resp.text, 'User registered successfully', 'Failed to register')
        return register_resp

    def login(self, session: requests.Session, username: str, password: str):
        # Login to account
        login_resp = session.post(self.url + 'login', json={
            'username': username,
            'password': password,
        })
        self.assert_neq(login_resp.text, 'Invalid username or password', 'Invalid creds', status=Status.CORRUPT)
        self.assert_eq(login_resp.status_code, 200, 'Failed to login to account')

        return login_resp

    def get_last_task_id_from_page(self, session: requests.Session):
        tasks_get_resp = session.get(self.url + 'tasks')

        matches = self._TASK_ID_PATTERN.findall(tasks_get_resp.text)
        assert_eq(len(matches) > 0, True, "Failed to find (checker's one) task on tasks page")

        return matches[-1]

    def comment_task(self, session: requests.Session, task_id, comment: str):
        comment_resp = session.post(self.url + f'task/{task_id}/comment', json={'content': comment})
        assert_in('Comment created successfully', comment_resp.text, 'NO MESSAGE: "Comment created successfully"')
        crc32_hash = comment_resp.text.split('=')[1]
        assert_eq(hex(zlib.crc32(comment.encode())).replace('0x', '').lower().lstrip('0'), crc32_hash.lower(),
                  'Comment hash is incorrect')

        assert_in(comment, self.get_comments(session, task_id), 'Comment cannot be get')

    def mark_task_as_completed(self, session: requests.Session, task_id):
        task_cnts = session.get(self.url + f'task/{task_id}').text
        assert_nin('Status:</b> completed', task_cnts,
                   'Task is open, not already completed but page shows that it is completed')
        assert_in('Status:</b> open', task_cnts, 'Task is open, but page NOT shows that it is open')

        complete_resp = session.post(self.url + f'task/{task_id}/complete')
        assert_eq(complete_resp.text, 'Job completed successfully', 'Unable to complete task')

        task_cnts = session.get(self.url + f'task/{task_id}').text
        assert_in('Status:</b> completed', task_cnts,
                  'Task cannot be marked as completed ("completed" NOT found in page)')
        assert_nin('Status:</b> open', task_cnts, 'Task cannot be marked as completed ("open" found in page)')

    def new_task(self, session: requests.Session, title: str, descr: str):
        # Create task with name and description of flag
        new_task_resp = session.post(self.url + 'task', json={
            'title': title,
            'description': descr,
        })
        self.assert_eq(new_task_resp.text, 'Task created successfully', 'Failed to create new task')

        task_id = self.get_last_task_id_from_page(session)

        return task_id

    def get_comments(self, session: requests.Session, task_id):
        session.get(self.url + f'task/{task_id}/comments')
        return session.get(self.url + f'task/{task_id}/comments').text

    def check(self):
        s = get_initialized_session()

        username = rnd_username(salt_length=random.randint(7, 20))
        password = rnd_password(random.randint(15, 40))
        self.register(s, username, password)
        self.login(s, username, password)
        # Create new tasks & add some comment #
        task_ids = [self.new_task(s, rnd_username(salt_length=random.randint(7, 20)),
                                  rnd_username(salt_length=random.randint(40, 100))) for _ in
                    range(random.randint(2, 5))]
        for task_id in task_ids:
            if random.randint(1, 2) == 1:
                # Comment functionality test
                self.comment_task(s, task_id, rnd_username(salt_length=random.randint(40, 100)))
            if random.randint(1, 2) == 1:
                # "Mark as complete" test
                self.mark_task_as_completed(s, task_id)

        # Random unpredictable part #
        if random.randint(1, 3) == 1:
            s = get_initialized_session()

            username = rnd_username(salt_length=random.randint(20, 30))
            password = rnd_password(random.randint(40, 110))
            self.register(s, username, password)
            self.login(s, username, password)

            task_ids = [self.new_task(s, rnd_username(salt_length=random.randint(4, 10)),
                                      rnd_username(salt_length=random.randint(20, 40))) for _ in
                        range(random.randint(3, 15))]
            for task_id in task_ids:
                if random.randint(1, 2) == 1:
                    self.mark_task_as_completed(s, task_id)
                if random.randint(1, 2) == 1:
                    self.comment_task(s, task_id, rnd_username(salt_length=random.randint(5, 100)))

        # Give access to other user functionality check #
        for _ in range(random.randint(1, 2)):
            s2 = get_initialized_session()
            username2 = rnd_username(salt_length=random.randint(7, 20))
            password2 = rnd_password(random.randint(15, 40))
            self.register(s2, username2, password2)
            self.login(s2, username2, password2)

            rnd_usern_ = rnd_username(salt_length=random.randint(11, 20))
            new_task_name = rnd_password(random.randint(15, 40))
            new_task_id = self.new_task(s2, new_task_name, '')

            nonext_addition = s2.post(self.url + f'task/{new_task_id}/assign-to', json={'nickname': rnd_usern_}).json()
            assert_eq(nonext_addition['success'], False, 'Succeeds in adding task access to NON-EXISTING USER!')
            assert_eq(nonext_addition['message'], f"User with nickname '{rnd_usern_}' not found",
                      'Succeeds in adding task access to NON-EXISTING USER!')

            ext_addition = s2.post(self.url + f'task/{new_task_id}/assign-to', json={'nickname': username}).json()
            assert_eq(ext_addition['success'], True, 'Task not assigned to ACTUAL user!')
            assert_eq(ext_addition['message'], "Task assigned successfully", 'Task not assigned to ACTUAL user!')

            _rvalue = random.randint(1, 3)
            if _rvalue == 1:
                self.mark_task_as_completed(s, new_task_id)
            elif _rvalue == 2:
                self.mark_task_as_completed(s2, new_task_id)

            tasks_text = s.get(self.url + 'tasks').text
            assert_in(f'<h2><a href="/task/{new_task_id}">{new_task_name}</a></h2>', tasks_text,
                      'Newly assigned task is NOT found on assigned to what user page')

            task_cnts_detailed = s.get(self.url + f'task/{new_task_id}').text
            assert_in(f'<h2>Task: {new_task_name}</h2>', task_cnts_detailed,
                      '[New Assign] Flag not found in task title on GET /tasks')

        self.cquit(Status.OK)

    def put(self, flag_id: str, flag: str, vuln: str):
        s = get_initialized_session()

        username = rnd_username(salt_length=random.randint(7, 20))
        password = rnd_password(random.randint(15, 40))
        self.register(s, username, password)
        self.login(s, username, password)
        if vuln == "1":  # flag in task title and description
            t_id = self.new_task(s, flag, flag)
            for _ in range(random.randint(1, 4)):
                self.comment_task(s, t_id, rnd_username(salt_length=random.randint(3, 55)))

        elif vuln == "2":  # flag in task comment
            t_id = self.new_task(s, rnd_username(salt_length=random.randint(3, 55)),
                                 rnd_username(salt_length=random.randint(3, 55)))
            self.comment_task(s, t_id, flag)
        else:
            raise Exception("Bad vuln index")

        if random.randint(1, 2) == 1:
            self.mark_task_as_completed(s, t_id)

        self.cquit(Status.OK, json.dumps({'username': username, 'task_id': t_id}), f"{username}:{password}:{t_id}")

    def get(self, flag_id: str, flag: str, vuln: str):
        s = get_initialized_session()
        username, password, t_id = flag_id.split(':')
        self.login(s, username, password)

        if vuln == "1":  # flag in task title and description
            tasks_get_resp = s.get(self.url + 'tasks').text
            assert_in(f'{flag}</a></h2>', tasks_get_resp, 'Flag not found in task title on GET /tasks',
                      status=Status.CORRUPT)
            assert_in(f'<p><b>Description:</b><br><br>{flag}</p>', tasks_get_resp,
                      'Flag not found in task description on GET /tasks', status=Status.CORRUPT)

            lt_id = self.get_last_task_id_from_page(s)
            task_cnts_detailed = s.get(self.url + f'task/{lt_id}').text

            assert_in(f'<h2>Task: {flag}</h2>', task_cnts_detailed, 'Flag not found in task title on GET /tasks',
                      status=Status.CORRUPT)
            assert_in(f'<p><b>Description:</b> {flag}</p>', task_cnts_detailed,
                      'Flag not found in task description on GET /tasks', status=Status.CORRUPT)

        elif vuln == "2":
            lt_id = self.get_last_task_id_from_page(s)
            comms = json.loads(self.get_comments(s, lt_id))
            assert_eq(len(comms), 1, 'More than one comment in flag-storing task', status=Status.CORRUPT)
            comm = comms[0]
            assert_eq(comm["Content"], flag, 'Incorrect flag in comments')

        self.cquit(Status.OK)


if __name__ == '__main__':
    type_of_check = sys.argv[1]
    # type_of_check = 'check'
    host = sys.argv[2]
    # host = '51.250.41.212'

    checker = Checker(host)

    try:
        checker.action(type_of_check, *sys.argv[3:])  # *['FLAGID', 'FLAG=', 'VULN'])  # *sys.argv[3:])
    except checker.get_check_finished_exception() as e:
        cquit(Status(checker.status), checker.public, checker.private)
