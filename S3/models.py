from peewee import SqliteDatabase, Model, CharField, IntegerField, ForeignKeyField

database = SqliteDatabase("roles.db")


class BaseModel(Model):
    class Meta:
        database = database


class Role(BaseModel):
    name = CharField(min_length=1, max_length=1, unique=True)


class UserRole(BaseModel):
    role_id = ForeignKeyField(Role, backref='users', on_delete='CASCADE')
    user_id = IntegerField()


def init_db():
    database.connect()
    database.create_tables([Role, UserRole], safe=True)
    # Создание ролей согласно требованиям: Админ, Директор, Завуч, Преподаватель, Студент, Родитель
    for name in ["Admin", "Director", "HeadTeacher", "Teacher", "Student", "Parent"]:
        Role.get_or_create(name=name)
    database.close()


if __name__ == "__main__":
    init_db()
