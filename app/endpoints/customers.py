from fastapi import APIRouter, Request
from ..database import *
import json

router = APIRouter()
table = "customers"

@router.post("/add")
async def add_customer(
    name: str, age: int, contact_info: str, is_disabled: bool, medical_conditions: str
):
    
    data = {
        "name": name,
        "age": age,
        "contact_info": contact_info,
        "is_disabled": is_disabled,
        "medical_conditions": medical_conditions
    }

    response = add(table, data)

    return json.dumps(response[0])

@router.post("/remove")
async def remove_customers(request: Request):
    response = delete(request, table)

    return json.dumps({"message": "Customers removed successfully"})

@router.get("/get")
async def get_customers(request: Request):
    response = get(request, table)
    return json.dumps(response)


@router.post("/update")
async def update_customers(request: Request, id: int):
    response = update(request, table, id)
    return json.dumps(response)