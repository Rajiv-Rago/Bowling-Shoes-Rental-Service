from supabase import create_client, Client
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
import json

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_API_KEY)

def parse_items(request):
    items = None
    try:
        items = request.query_params.items()
    except AttributeError:
        items = request.items()

    return items

def add(table, data):
    client = get_supabase_client()

    response = (
        client.table(table)
        .insert(data)
        .execute()
    )

    return response.data

def delete(request, table):
    client = get_supabase_client()

    response = client.table(table).delete()

    items = parse_items(request)

    for key, value in items:
        if key != "table":
            response = response.eq(key, value)
    
    response.execute()

    return response

def get(request, table):
    client = get_supabase_client()

    response = client.table(table).select("*")
    items = parse_items(request)

    for key, value in items:
        if key != "table":
            response = response.eq(key, value)
    
    data = response.execute().data
    
    return data


def update(request, table, id):
    clinet = get_supabase_client()

    response = clinet.table(table)
    
    items = parse_items(request)
    
    for key, value in items:
        if key != "table" and key != "id":
            response = response.update({key: value})
    
    
    data = response.eq("id", int(id)).execute().data

    return data