from fastapi import FastAPI
from typing import List, Optional
from pydantic import BaseModel, Field, validator


from models import database, Role

app = FastAPI(title="Role Service")


# Pydantic схемы
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


# API Endpoints
@app.post("/roles", response_model=RoleResponse, status_code=201)
def create_role(role_data: RoleCreate):
    role = Role.create(name=role_data.name)
    return RoleResponse(id=role.id, name=role.name)


@app.put("/roles/{role_id}", response_model=RoleResponse)
def update_role(role_id: int, role_data: RoleUpdate):
    role = Role.get_by_id(role_id)
    if role_data.name:
        role.name = role_data.name
        role.save()
    return RoleResponse(id=role.id, name=role.name)


@app.delete("/roles/{role_id}")
def delete_role(role_id: int):
    return Role.delete().where(Role.id == role_id).execute() > 0


@app.get("/roles/{role_id}", response_model=RoleResponse)
def get_role(role_id: int):
    role = Role.get_by_id(role_id)
    return RoleResponse(id=role.id, name=role.name)


@app.get("/roles", response_model=List[RoleResponse])
def get_roles(name: Optional[str] = None, limit: Optional[int] = None):
    query = Role.select()
    if name:
        query = query.where(Role.name.contains(name))
    if limit:
        query = query.limit(limit)
    return [RoleResponse(id=r.id, name=r.name) for r in query]


@app.on_event("startup")
def startup():
    database.connect()


@app.on_event("shutdown")
def shutdown():
    if not database.is_closed():
        database.close()
