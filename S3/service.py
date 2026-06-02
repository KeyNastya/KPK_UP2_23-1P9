from fastapi import FastAPI, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from peewee import DoesNotExist

from models import database, Role

app = FastAPI(title="Role Service")


# Pydantic схемы (валидация здесь, а не в Peewee)
class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class RoleResponse(BaseModel):
    id: int
    name: str


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)

    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Name cannot be empty')
            return v.strip()
        return v


# API Endpoints
@app.post("/roles", response_model=RoleResponse, status_code=201)
def create_role(role_data: RoleCreate):
    if Role.select().where(Role.name == role_data.name).exists():
        raise HTTPException(409, f"Role '{role_data.name}' already exists")
    role = Role.create(name=role_data.name)
    return RoleResponse(id=role.id, name=role.name)


@app.put("/roles/{role_id}", response_model=RoleResponse)
def update_role(role_id: int, role_data: RoleUpdate):
    try:
        role = Role.get_by_id(role_id)
    except DoesNotExist:
        raise HTTPException(404, f"Role {role_id} not found")

    if role_data.name is not None and role_data.name != role.name:
        if Role.select().where(Role.name == role_data.name).exists():
            raise HTTPException(409, f"Role '{role_data.name}' already exists")
        role.name = role_data.name
        role.save()

    return RoleResponse(id=role.id, name=role.name)


@app.delete("/roles/{role_id}")
def delete_role(role_id: int):
    # Перед удалением проверяем, есть ли связанные Access
    from models import Access
    if Access.select().where(Access.role == role_id).exists():
        raise HTTPException(400, "Cannot delete role with existing access relations")

    deleted = Role.delete().where(Role.id == role_id).execute()
    return deleted > 0


@app.get("/roles/{role_id}", response_model=RoleResponse)
def get_role(role_id: int):
    try:
        role = Role.get_by_id(role_id)
    except DoesNotExist:
        raise HTTPException(404, f"Role {role_id} not found")
    return RoleResponse(id=role.id, name=role.name)


@app.get("/roles", response_model=List[RoleResponse])
def get_roles(name: Optional[str] = None, limit: Optional[int] = None):
    query = Role.select()
    if name:
        query = query.where(Role.name.contains(name))
    if limit is not None and limit > 0:
        query = query.limit(limit)
    roles = list(query)
    return [RoleResponse(id=r.id, name=r.name) for r in roles]


@app.on_event("startup")
def startup():
    database.connect()


@app.on_event("shutdown")
def shutdown():
    if not database.is_closed():
        database.close()
