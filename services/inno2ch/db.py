from peewee import SqliteDatabase, Model, AutoField, CharField, TextField, ForeignKeyField


class BaseModel(Model):
    class Meta:
        database = SqliteDatabase('innoCTF.db')


class Users(BaseModel):
    login = CharField(primary_key=True, max_length=150)
    password = CharField(max_length=150)

    class Meta:
        db_table = 'users'


class Posts(BaseModel):
    id = AutoField(primary_key=True)
    title = TextField()
    body = TextField()
    available = TextField()
    author_username = ForeignKeyField(Users)

    class Meta:
        db_table = 'posts'


class Comments(BaseModel):
    id = AutoField(primary_key=True)
    author_username = ForeignKeyField(Users, 'login', backref='comments')
    post_id = ForeignKeyField(Posts, 'id', backref='comments')
    text = TextField()

Comments.drop_table()
Users.drop_table()
Comments.drop_table()

Comments.create_table()
Users.create_table()
Posts.create_table()
