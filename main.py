from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Union
from datetime import date

class Food(BaseModel):
    name: str
    qty: int
    lbs: Union[float,None] = None
    fr1: bool
    fr2: bool
    fr3: bool
    tag: int
    notes: Union[str,None] = None
    freeze: date
    thaw: Union[date,None] = None




app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")

def today():
    return date.today().strftime("%Y-%m-%d")

@app.get("/add", response_class=HTMLResponse)
async def get_add(request: Request):
    return templates.TemplateResponse("add.html", 
        {"request": request, 
         "qty": 1,
         "notes": "Add notes here...",
         "freeze": today(),
        })

@app.post("/add")
async def post_add(item: Food):
    return item
    return templates.TemplateResponse("add.html", item)

