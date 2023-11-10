
from flask import Flask, render_template, request, make_response, redirect
import db
from db import Users, Posts, Comments
from jwt_actions import make_jwt, decode_jwt

app = Flask(__name__)
debug = False
host = '0.0.0.0'
port = 8080
app.config['SECRET_KEY'] = 'ASDLASDLASDLSADLASLDHasda'


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        token = request.cookies.get('token', '')
        username = decode_jwt(token).get('login', '') if token else 'all'
        posts = [(post.id, post.title, post.body, post.available, list(post.comments), post.author_username.login) for post in
                 Posts.select().where(Posts.available.in_((username, 'all')))]
        username = '' if username == 'all' else username
        return render_template('index.html', posts=posts[::-1], username=username)
    else:
        post_id = request.form.get('post_id', '')
        comment_text = request.form.get('comment', '')
        author_username = request.cookies.get('token', 'anonymous')
        if post_id and comment_text:
            if author_username == 'anonymous':
                Comments.insert(post_id=post_id, author_username_id='anonymous', text=comment_text).execute()
            else:
                author_username = decode_jwt(author_username)['login']
                Comments.insert(post_id=post_id, author_username_id=author_username, text=comment_text).execute()
        return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        result = Users.get_or_none(login=login, password=password)
        if result:
            res = make_response(redirect('/'))
            res.set_cookie(key='token', value=make_jwt(result.login, result.password))
            return res
        return render_template('login.html', title='Login', is_loggined=False)

    return render_template('login.html', title='Login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        is_added = Users.get_or_create(login=login, password=password)[1]
        if is_added:
            res = make_response(redirect('/'))
            res.set_cookie(key='token', value=make_jwt(login, password))
            return res
        return render_template('register.html', title='Registration', not_added=False)

    return render_template('register.html', title='Registration')


@app.route('/post', methods=['GET', 'POST'])
def post():
    if request.method == 'GET':
        return render_template('post.html', error=False)
    else:
        try:
            title = request.form['title']
            body = request.form['body']
            available = request.form['available']
            author_username = decode_jwt(request.cookies.get('token', '')).get('login', '')
            assert author_username != ''
            Posts.insert(title=title, body=body, available=available, author_username_id=author_username).execute()
            return redirect('/')
        except Exception as e:
            print(e)
            return render_template('post.html', error=True)


@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        username = request.cookies.get('token', '')
        if not username:
            return redirect('/login')
        try:
            post_id = request.form.get('post_id', '')
            assert post_id != ''
            post_id = int(post_id)
            res = Posts.select().where(Posts.id == post_id)
            assert len(res) != 0
            title = request.form.get('title', '')
            body = request.form.get('body', '')
            available = request.form.get('available', '')
            if not any((title, body, available)):
                return render_template('update.html', post_id=post_id)
            if title:
                Posts.update(title=title).where(Posts.id == post_id).execute()
            if body:
                Posts.update(body=body).where(Posts.id == post_id).execute()
            if available:
                Posts.update(available=available).where(Posts.id == post_id).execute()

            return redirect('/')
        except Exception as e:
            print(e)
            return render_template('update.html', error=True)


if __name__ == "__main__":
    # from waitress import serve
    # serve(app, host=host, port=port)
    app.run(host=host, port=port, debug=debug)
