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
async def get_add(request: Request, 
                 name: str = "",
                 qty: int = 1,
                 lbs: float = 0,
                 freezer: Union[str,None]= None,
                 tag: Union[int,None] = None,
                 notes: str = "Add notes here...",
                 freeze: date = today(),
                 ):
    form = {"request": request, 
         "name": name,
         "qty": qty,
         "lbs": lbs,
         "freezer": freezer,
         "notes": notes,
         "freeze": freeze,
        }
    form[freezer] = "selected"
    return templates.TemplateResponse("add.html", form)

