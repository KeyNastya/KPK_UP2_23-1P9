from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import peewee

from models import database, Role

app = FastAPI(title="Role Service")


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

    @Field.validator('name')
    def validate_name(cls, v):
        return v.strip()


class RoleResponse(BaseModel):
    id: int
    name: str


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)

    @Field.validator('name')
    def validate_name(cls, v):
        return v.strip() if v else v


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


@app.post("/roles", response_model=RoleResponse, status_code=201)
def create_role(data: RoleCreate):
    """
    Создание роли
    ---
    **Метод:** POST
    **Параметры:** JSON-тело {name: str}
    **Возвращает:** созданный объект с ID
    **Пример ответа:**
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
    **Параметры:** id в пути, JSON-тело {name: str} (опционально)
    **Возвращает:** обновлённый объект
    **Пример ответа:**
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
    Логическое удаление роли по ID
    ---
    **Метод:** DELETE
    **Параметры:** id в пути
    **Возвращает:** {"success": true} или {"success": false}
    **Пример ответа:**
    {
        "success": true
    }
    """
    role = get_role_by_id(role_id)
    if hasattr(role, 'is_active'):
        role.is_active = False
        role.save()
        return {"success": True}
    else:
        return {"success": Role.delete().where(Role.id == role_id).execute() > 0}


@app.get("/roles/{role_id}", response_model=RoleResponse)
def get_role(role_id: int):
    """
    Получить роль по ID
    ---
    **Метод:** GET
    **Параметры:** id в пути
    **Возвращает:** объект роли
    **Пример ответа:**
    {
        "id": 1,
        "name": "Admin"
    }
    """
    role = get_role_by_id(role_id)
    return RoleResponse(id=role.id, name=role.name)


@app.get("/roles", response_model=List[RoleResponse])
def list_roles(
    name: Optional[str] = Query(None, description="Частичное совпадение имени"),
    limit: Optional[int] = Query(None, description="Лимит количества записей", ge=1)
):
    """
    Получить список ролей по параметрам
    ---
    **Метод:** GET
    **Параметры:** query-параметры name (частичное совпадение), limit (лимит)
    **Возвращает:** список объектов ролей
    **Пример ответа:**
    [
        {"id": 1, "name": "Admin"},
        {"id": 2, "name": "Director"}
    ]
    """
    query = Role.select()
    if name:
        query = query.where(Role.name.contains(name))
    if limit:
        query = query.limit(limit)
    return [RoleResponse(id=role.id, name=role.name) for role in query]


@app.on_event("startup")
def startup():
    database.connect()


@app.on_event("shutdown")
def shutdown():
    if not database.is_closed():
        database.close()