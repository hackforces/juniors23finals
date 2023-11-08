import jwt


def make_jwt(login: str, password: str) -> str:
    return jwt.encode(payload={"login": login, "password": password},
                      key='Haha Pls change it',
                      algorithm="HS256")


def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(jwt=token, key='Haha Pls change it', algorithms=['HS256'])
    except:
        return {}
