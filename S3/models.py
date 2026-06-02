from peewee import SqliteDatabase, Model, CharField, IntegerField, ForeignKeyField

database = SqliteDatabase("roles.db")


class BaseModel(Model):
    class Meta:
        database = database


class Role(BaseModel):
    name = CharField(unique=True)


class Access(BaseModel):
    role = ForeignKeyField(Role, backref='users', on_delete='CASCADE')
    user = IntegerField()


def init_db():
    database.connect()
    database.create_tables([Role, Access], safe=True)
    for name in ["Admin", "Director", "HeadTeacher", "Teacher", "Student", "Parent"]:
        Role.get_or_create(name=name)
    database.close()


if __name__ == "__main__":
    init_db()
