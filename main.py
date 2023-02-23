from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Union
from datetime import datetime
import sqlite3
con = sqlite3.connect("food.db")
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS freezerfood(name TEXT, qty INTEGER, lbs REAL, loc TEXT, tag INTEGER, notes TEXT, freeze TEXT, thaw TEXT);")

def fetch_entry(tag: int):
    cur.execute("SELECT * FROM freezerfood WHERE thaw IS NULL and tag=?",[tag])
    return cur.fetchone()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

df = "%Y-%m-%d"
def today():
    return date.today().strftime("%Y-%m-%d")

# Prevents from using future dates
def nofuture(datestring: Union[str,None]):
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
                 notes: str = "",
                 freeze: Union[str,None] = None,
                 ):
    newname = ' '.join([w.title() for w in name.split()])
    freeze = nofuture(freeze)
    default_notes = "Add notes here..."
    if notes.startswith(default_notes): #Remove default notes
        notes = notes[len(default_notes):]
    form = {"request": request, 
         "name": newname,
         "qty": qty,
         "lbs": lbs,
         "loc": freezer,
         "tag": tag,
         "notes": notes,
         "freeze": freeze,
         "thaw": None,
        }
    if tag is not None:
        if fetch_entry(tag) is None:
            cur.execute("INSERT INTO freezerfood VALUES(:name, :qty, :lbs, :loc,:tag, :notes, :freeze, :thaw)", form)
            con.commit()
        else:
            form["error"] = "Duplicate tag already in freezer. Please use another tag."
    form[freezer] = "selected"
    if notes is "": #Add default notes if missing
        form["notes"]=default_notes
    return templates.TemplateResponse("add.html", form)

