from peewee import SqliteDatabase, Model, CharField, ForeignKeyField

database = SqliteDatabase("roles.db")


class BaseModel(Model):
    class Meta:
        database = database


class Role(BaseModel):
    name = CharField(max_length=255, unique=True)
    description = CharField(max_length=255, null=True)


class Access(BaseModel):
    role = ForeignKeyField(Role, backref='users', on_delete='CASCADE')
    user = ForeignKeyField(User, backref='roles', on_delete='CASCADE')


def init_db():
    database.connect()
    database.create_tables([Role, Access], safe=True)
    for name in ["Admin", "Director", "HeadTeacher", "Teacher", "Student", "Parent"]:
        Role.get_or_create(name=name, defaults={"description": f"Role {name}"})
    database.close()


if __name__ == "__main__":
    init_db()
