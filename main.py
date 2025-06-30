from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import openai
import os

# Load OpenAI API key from environment
openai.api_key = os.getenv("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")

app = FastAPI(),

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Google Sheet data
def load_sheet(sheet_name='SportVot Play Venue Mapping Details'):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(os.getenv("1640363545")).worksheet(sheet_name)
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    return df

# Manual filter query
@app.get("/query")
def query(
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    type: Optional[str] = Query(None)
):
    df = load_sheet()
    if city:
        df = df[df['City'].str.lower() == city.lower()]
    if state:
        df = df[df['State'].str.lower() == state.lower()]
    if type:
        df = df[df['Type of Property'].str.lower() == type.lower()]
    return df.to_dict(orient="records")

# Natural language query using GPT
@app.post("/ask")
def ask_gpt(question: str = Body(..., embed=True)):
    df = load_sheet()
    columns = ", ".join(df.columns.tolist())

    prompt = f"""
You are a smart assistant helping query a database of sports sponsorship opportunities.
The data has the following columns: {columns}.
Here is a sample user question: '{question}'.

Write Python-style Pandas filter conditions to extract the relevant rows from the DataFrame.
Don't write full code, just return the conditions.
Use lowercase comparisons with 'str.lower()'.
Example output: df[df['City'].str.lower() == 'mumbai']
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    try:
        condition_code = response['choices'][0]['message']['content']
        result = eval(condition_code)
        return result.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e), "gpt_code": condition_code}
