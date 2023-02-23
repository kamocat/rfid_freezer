from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Union
from datetime import datetime

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

def today():
    return date.today().strftime("%Y-%m-%d")

# Prevents from using future dates
def nofuture(datestring: Union[str,None]):
    df = "%Y-%m-%d"
    t = datetime.now()
    if datestring is None:
        datenum = t
    else:
        datenum = datetime.strptime(datestring, df)
        if datenum > t:
            datenum = t
    return datenum.strftime(df)


@app.get("/add", response_class=HTMLResponse)
async def get_add(request: Request, 
                 name: str = "",
                 qty: int = 1,
                 lbs: float = 0,
                 freezer: str = "fr1",
                 tag: Union[int,None] = None,
                 notes: str = "Add notes here...",
                 freeze: Union[str,None] = None,
                 ):
    newname = ' '.join([w.title() for w in name.split()])
    freeze = nofuture(freeze)
    form = {"request": request, 
         "name": newname,
         "qty": qty,
         "lbs": lbs,
         "freezer": freezer,
         "notes": notes,
         "freeze": freeze,
        }
    form[freezer] = "selected"
    return templates.TemplateResponse("add.html", form)

