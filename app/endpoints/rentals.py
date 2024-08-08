from fastapi import APIRouter, Request
from ..database import *
import json
import lamini


router = APIRouter()
table = "rentals"
LLM_API_KEY = os.getenv("LLM_API_KEY")

@router.post("/add")
async def add_record(
    name: str, 
    rental_date: str, 
    shoe_size: float, 
    rental_fee: float, 
):
    
    customer = get({"name": name}, "customers")[0]
    

    input = f"""
    The discount model for the bowling shoe rental service will be based on the following criteria:
    Age:
    Age 0-12: 20% discount
    Age 13-18: 10% discount
    Age 65 and above: 15% discount
    Disability Status:
    Disabled: 25% discount
    Pre-existing Medical Conditions:
    Diabetes: 10% discount
    Hypertension: 10% discount
    Chronic Condition: 10% discount

    What would be the discount for a customer with the following attributes?
    Age: {customer["age"]}
    Disability Status: {customer["is_disabled"]}
    Pre-existing Medical Conditions: {customer["medical_conditions"]}

    Choose the highest discount percentage in decimal. Return a simple float.
    """

    llm = lamini.Lamini(api_key=LLM_API_KEY, model_name="meta-llama/Meta-Llama-3.1-8B-Instruct")
    discount = float(llm.generate(input, output_type={"Response":"str"})["Response"])

    print(discount)

    data = {
        "customer_id": customer["id"],
        "rental_date": rental_date,
        "shoe_size": shoe_size,
        "rental_fee": rental_fee,
        "discount": discount,
        "total_fee": rental_fee - (rental_fee * discount)
    }

    response = add(table, data)

    return json.dumps(response[0])
    return ""

@router.post("/remove")
async def remove_record(request: Request):
    response = delete(request, table)

    return json.dumps({"message": "Rental record removed successfully"})

@router.get("/get")
async def get_records(request: Request):
    response = get(request, table)
    return json.dumps(response)


@router.post("/update")
async def update_record(request: Request, id: int):
    response = update(request, table, id)
    return json.dumps(response)