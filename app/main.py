from fastapi import FastAPI, HTTPException, Request
from .endpoints import customers, rentals
from .database import *

app = FastAPI()

app.include_router(customers.router, prefix="/customers", tags=["customers"])
app.include_router(rentals.router, prefix="/rentals", tags=["rentals"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Bowling Shoes Rental Service"}
