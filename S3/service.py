from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import peewee

from models import database, Role

app = FastAPI(title="Role Service")


# ----- СХЕМЫ (Pydantic) -----
class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

    @validator('name')
    def validate_name(cls, v):
        return v.strip()


class RoleResponse(BaseModel):
    id: int
    name: str


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)

    @validator('name')
    def validate_name(cls, v):
        return v.strip() if v else v


# ----- ЛОГИКА (Peewee) -----
def get_role_by_id(role_id: int) -> Role:
    try:
        return Role.get_by_id(role_id)
    except peewee.DoesNotExist:
        raise HTTPException(status_code=404, detail="Role not found")


def check_name_unique(name: str, exclude_id: Optional[int] = None):
    query = Role.select().where(Role.name == name)
    if exclude_id:
        query = query.where(Role.id != exclude_id)
    if query.exists():
        raise HTTPException(status_code=409, detail="Role with this name already exists")


# ----- ЭНДПОИНТЫ -----
@app.post("/roles", response_model=RoleResponse, status_code=201)
def create_role(data: RoleCreate):
    """
    Создание роли
    ---
    **Метод:** POST
    **Эндпоинт:** /roles
    **Параметры запроса:** JSON-тело (name)
    **Назначение:** Создание новой роли с уникальным именем
    **Ошибки:**
        - 400: Ошибка валидации (имя не соответствует ограничениям)
        - 409: Роль с таким именем уже существует
    **Пример ответа (201):**
    {
        "id": 1,
        "name": "Admin"
    }
    """
    check_name_unique(data.name)
    role = Role.create(name=data.name)
    return RoleResponse(id=role.id, name=role.name)


@app.put("/roles/{role_id}", response_model=RoleResponse)
def update_role(role_id: int, data: RoleUpdate):
    """
    Изменение роли по ID
    ---
    **Метод:** PUT
    **Эндпоинт:** /roles/{id}
    **Параметры запроса:** id в пути, JSON-тело (name - опционально)
    **Назначение:** Обновление имени существующей роли
    **Ошибки:**
        - 400: Ошибка валидации (имя не соответствует ограничениям)
        - 404: Роль с указанным ID не найдена
        - 409: Новое имя роли уже существует
    **Пример ответа (200):**
    {
        "id": 1,
        "name": "SuperAdmin"
    }
    """
    role = get_role_by_id(role_id)
    if data.name:
        check_name_unique(data.name, exclude_id=role_id)
        role.name = data.name
        role.save()
    return RoleResponse(id=role.id, name=role.name)


@app.delete("/roles/{role_id}")
def delete_role(role_id: int):
    """
    Удаление роли по ID
    ---
    **Метод:** DELETE
    **Эндпоинт:** /roles/{id}
    **Параметры запроса:** id в пути
    **Назначение:** Физическое удаление роли из базы данных
    **Ошибки:**
        - 404: Роль с указанным ID не найдена
    **Пример ответа (200):**
    {
        "success": true
    }
    """
    role = get_role_by_id(role_id)
    deleted_count = Role.delete().where(Role.id == role_id).execute()
    return {"success": deleted_count > 0}


@app.get("/roles/{role_id}", response_model=RoleResponse)
def get_role(role_id: int):
    """
    Получение роли по ID
    ---
    **Метод:** GET
    **Эндпоинт:** /roles/{id}
    **Параметры запроса:** id в пути
    **Назначение:** Получение информации о роли по её идентификатору
    **Ошибки:**
        - 404: Роль с указанным ID не найдена
    **Пример ответа (200):**
    {
        "id": 1,
        "name": "Admin"
    }
    """
    role = get_role_by_id(role_id)
    return RoleResponse(id=role.id, name=role.name)


@app.get("/roles", response_model=List[RoleResponse])
def list_roles(
    name: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, description="Лимит количества записей")
):
    """
    Получение списка ролей по заданным параметрам
    ---
    **Метод:** GET
    **Эндпоинт:** /roles
    **Параметры запроса:** query-параметры name (опционально), limit (опционально)
    **Назначение:** Получение списка ролей с возможностью фильтрации по имени и ограничением количества записей
    **Ошибки:**
        - 400: Некорректное значение параметра limit (меньше 1)
    **Пример ответа (200):**
    [
        {"id": 1, "name": "Admin"},
        {"id": 2, "name": "Director"}
    ]
    """
    query = Role.select()
    if name:
        query = query.where(Role.name.contains(name))
    if limit is not None and limit < 1:
        raise HTTPException(status_code=400, detail="limit must be >= 1")
    return [RoleResponse(id=role.id, name=role.name) for role in query]


# ----- ОБРАБОТЧИКИ ЖИЗНЕННОГО ЦИКЛА -----
@app.on_event("startup")
def startup():
    database.connect()


@app.on_event("shutdown")
def shutdown():
    if not database.is_closed():
        database.close()
