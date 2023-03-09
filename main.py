from fastapi import FastAPI, Request
from fastapi.responses import *
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Union
from datetime import datetime
import sqlite3
import io
import csv
con = sqlite3.connect("food.db")
con.row_factory = sqlite3.Row # Access values by name
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS freezerfood(rowid INTEGER PRIMARY KEY, name TEXT, qty INTEGER, lbs REAL, loc TEXT, tag INTEGER, notes TEXT, freeze TEXT, thaw TEXT);")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

navigation = [
        {"caption":"Add an item", "href":"/add"},
        {"caption":"View items", "href":"/view"},
        {"caption":"Thaw an item", "href":"/thaw"},
        {"caption":"Download spreadhseet", "href":"/freezerfood.csv"},
]


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
                                       "form":{
                                       "freeze":today(), 
                                       "qty":1, 
                                       "notes":default_notes,
                                       }})


@app.get("/add", response_class=HTMLResponse)
async def get_add(request: Request, 
                 name: str = "",
                 qty: int = 1,
                 lbs: float = 0,
                 oz: float = 0,
                 freezer: str = "fr1",
                 tag: Union[int,None] = None,
                 notes: str = "",
                 freeze: Union[str,None] = None,
                 ):
    newname = ' '.join([w.title() for w in name.split()])
    freeze = nofuture(freeze)
    if notes.startswith(default_notes): #Remove default notes
        notes = notes[len(default_notes):]
    form = {
         "name": newname,
         "qty": qty,
         "lbs": lbs + oz/16,
         "loc": freezer,
         "tag": tag,
         "notes": notes,
         "freeze": freeze,
        }
    if tag is not None:
        cur.execute("SELECT * FROM freezerfood WHERE thaw IS NULL and tag=? LIMIT 1",[tag])
        if cur.fetchone() is None:
            cur.execute("INSERT INTO freezerfood (name, qty, lbs, loc, tag, notes, freeze) VALUES(:name, :qty, :lbs, :loc,:tag, :notes, :freeze)", form)
            con.commit()
        else:
            form["error"] = "Duplicate tag already in freezer. Please use another tag."
    form[freezer] = "selected"
    if notes == "": #Add default notes if missing
        form["notes"]=default_notes
    return templates.TemplateResponse("add.html", {"request": request, "title":"Add Food to the Freezer", "navigation":navigation,"form":form})

@app.get("/view", response_class=HTMLResponse)
async def get_existing(request: Request,
                       tag: Union[int,None] = None,
                       thaw_now: bool = False,):
    data = {}
    cur.execute("SELECT * FROM freezerfood WHERE tag=? order by rowid desc limit 1",[tag])
    a = cur.fetchone()
    data.update(dict(a))
    return templates.TemplateResponse("view.html", {"request":request,"title":"View Frozen Item", "navigation":navigation,"form":data})

@app.get("/thaw", response_class=HTMLResponse)
async def thatme(request: Request,
                 tag: Union[int,None] = None,):
    data = {}
    cur.execute("SELECT * FROM freezerfood WHERE tag=? order by rowid desc limit 1",[tag])
    a = cur.fetchone()
    if a is None:
        data["error"] = "This tag is currently not in use"
    else:
        data.update(dict(a))
        print(data)
        t = today()
        data["thaw"] = t
        cur.execute("UPDATE freezerfood set thaw = :thaw where tag = :tag and thaw is NULL;", data)
        con.commit()
    return templates.TemplateResponse("view.html", {"request":request,"title":"Thaw an Item", "navigation":navigation,"form":data})


def csvrow(arr):
    return '"'+'","'.join(arr)+'"\r\n'

@app.get("/freezerfood.csv", response_class=StreamingResponse)
async def export(request: Request):
    response = io.StringIO()
    cur.execute("SELECT * from freezerfood")
    arr = cur.fetchall()
    rows = map(lambda row: map(lambda x: row[x], row.keys()), arr)
    mycsv = csv.writer(response)
    mycsv.writerow(arr[0].keys())
    mycsv.writerows(rows)
    response.seek(0)
    return StreamingResponse(response, media_type="text/csv", )
