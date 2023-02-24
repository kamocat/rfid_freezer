from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Union
from datetime import datetime
import sqlite3
con = sqlite3.connect("food.db")
con.row_factory = sqlite3.Row # Access values by name
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS freezerfood(rowid INTEGER PRIMARY KEY, name TEXT, qty INTEGER, lbs REAL, loc TEXT, tag INTEGER, notes TEXT, freeze TEXT, thaw TEXT);")

def fetch_entry(tag: int):
    cur.execute("SELECT * FROM freezerfood WHERE thaw IS NULL and tag=? LIMIT 1",[tag])
    return cur.fetchone()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

df = "%Y-%m-%d"
def today():
    return datetime.now().strftime("%Y-%m-%d")

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

default_notes = "Add notes here..."
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("add.html", 
                                      {"request": request,
                                       "freeze":today(), 
                                       "qty":1, 
                                       "lbs":0,
                                       "notes":default_notes,
                                       })


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
        }
    if tag is not None:
        if fetch_entry(tag) is None:
            cur.execute("INSERT INTO freezerfood (name, qty, lbs, loc, tag, notes, freeze) VALUES(:name, :qty, :lbs, :loc,:tag, :notes, :freeze)", form)
            con.commit()
        else:
            form["error"] = "Duplicate tag already in freezer. Please use another tag."
    form[freezer] = "selected"
    if notes == "": #Add default notes if missing
        form["notes"]=default_notes
    return templates.TemplateResponse("add.html", form)


@app.get("/view", response_class=HTMLResponse)
async def get_existing(request: Request,
                       tag: Union[int,None] = None,
                       thaw_now: bool = False,):
    data = {"request": request}
    cur.execute("SELECT * FROM freezerfood WHERE tag=? order by rowid desc limit 1",[tag])
    a = cur.fetchone()
    if a is None:
        data["error"] = "This tag is currently not in use"
    else:
        data.update(dict(a))
        if data["thaw"] is not None:
            data["error"] = "This item has already been used"
        elif thaw_now:
            print(data)
            t = today()
            data["thaw"] = t
            cur.execute("UPDATE freezerfood set thaw = :thaw where tag = :tag and thaw is NULL;", data)
            con.commit()
    return templates.TemplateResponse("view.html", data)

@app.get("/thaw", response_class=HTMLResponse)
async def thatme(request: Request,
                 tag: Union[int,None] = None,):
    return await get_existing(request=request, tag=tag, thaw_now=True)

