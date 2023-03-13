from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.responses import *
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Union, Optional, List
from datetime import datetime
import sqlite3
import io
import csv
import requests
con = sqlite3.connect("food.db")
con.row_factory = sqlite3.Row # Access values by name
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS freezerfood(rowid INTEGER PRIMARY KEY, name TEXT, qty INTEGER, lbs REAL, loc TEXT, tag INTEGER, notes TEXT, freeze TEXT, thaw TEXT);")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

navigation = [
        {"caption":"Add an item", "href":"/"},
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
    form = {"notes":default_notes,
            "freeze": today(),
            "qty": 1,
            }
    return templates.TemplateResponse("add.html", {"request": request, "title":"Add Food to the Freezer", "navigation":navigation,"form":form, "focus":"name"})

@app.post("/", response_class=HTMLResponse)
async def post_add(request: Request, 
                 name: str = Form(""),
                 qty: int = Form(1),
                 lbs: Optional[float] = Form(0),
                 oz: Optional[float] = Form(0),
                 freezer: str = Form("fr1"),
                 tag: int = Form(0),
                 notes: str = Form(""),
                 freeze: str = Form(today()),
                 ):
    newname = ' '.join([w.title() for w in name.split()])
    freeze = nofuture(freeze)
    weight = oz/16 + lbs
    if notes.startswith(default_notes): #Remove default notes
        notes = notes[len(default_notes):]
    form = {
         "name": newname,
         "qty": qty,
         "lbs": weight,
         "loc": freezer,
         "tag": tag,
         "notes": notes,
         "freeze": freeze,
        }
    cur.execute("SELECT * FROM freezerfood WHERE thaw IS NULL and tag=? LIMIT 1",[tag])
    if cur.fetchone() is None:
        cur.execute("INSERT INTO freezerfood (name, qty, lbs, loc, tag, notes, freeze) VALUES(:name, :qty, :lbs, :loc,:tag, :notes, :freeze)", form)
        con.commit()
    else:
        form["error"] = "Duplicate tag already in freezer. Please use another tag."
    form[freezer] = "selected"
    if notes == "": #Add default notes if missing
        form["notes"]=default_notes
    #Clear data that should be unique for each entry
    form["tag"] = None
    form["lbs"] = None
    return templates.TemplateResponse("add.html", {"request": request, "title":"Add Food to the Freezer", "navigation":navigation,"form":form, "focus":"lbs"})

@app.get("/view", response_class=HTMLResponse)
async def get_existing(request: Request,
                       tag: Union[int,None] = None,
                       ):
    data = {}
    if tag is not None:
        cur.execute("SELECT * FROM freezerfood WHERE tag=? order by rowid desc limit 1",[tag])
        a = cur.fetchone()
        if a is None:
            data["error"] = "This tag is currently not in use"
        else:
            data.update(dict(a))
            data[data["loc"]] = "selected"
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
        data["thaw"] = today()
        cur.execute("UPDATE freezerfood set thaw = :thaw where tag = :tag and thaw is NULL;", data)
        con.commit()
    data[data["loc"]] = "selected"
    return templates.TemplateResponse("view.html", {"request":request,"title":"Thaw an Item", "navigation":navigation,"form":data})

@app.post("/view", response_class=HTMLResponse)
@app.post("/thaw", response_class=HTMLResponse)
async def modify_entry(request: Request, 
                 name: str = Form(""),
                 qty: int = Form(1),
                 lbs: Optional[float] = Form(0),
                 oz: Optional[float] = Form(0),
                 freezer: str = Form("fr1"),
                 tag: int = Form(0),
                 notes: Optional[str] = Form(""),
                 freeze: str = Form(today()),
                 thaw: Optional[str] = Form(None),
                 ):
    newname = ' '.join([w.title() for w in name.split()])
    weight = oz/16 + lbs
    form = {
         "name": newname,
         "qty": qty,
         "lbs": weight,
         "loc": freezer,
         "tag": tag,
         "notes": notes,
         "freeze": freeze,
         "thaw": thaw,
        }
    cur.execute("SELECT rowid FROM freezerfood WHERE tag=? ORDER BY ROWID DESC LIMIT 1", [tag]);
    form["rowid"] = cur.fetchone()["rowid"];
    cur.execute("UPDATE freezerfood SET name=:name,qty=:qty,lbs=:lbs,loc=:loc,tag=:tag,notes=:notes,freeze=:freeze,thaw=:thaw WHERE rowid=:rowid", form)
    con.commit()
    form[freezer] = "selected"
    return templates.TemplateResponse("view.html", {"request":request,"title":"Modify an Item", "navigation":navigation,"form":form})

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

#@app.get("/search", response_class=PlainTextResponse)
def search(key: str):
    cur.execute("SELECT name,lbs FROM freezerfood WHERE thaw IS NULL ORDER BY name ASC");
    key = key.lower()
    items = filter(lambda x: key in x["name"].lower(), cur.fetchall())
    from collections import defaultdict
    weights = defaultdict(lambda: 0)
    for i in items:
        weights[i["name"]] += i["lbs"]
    weight_str = '\n'.join([f'{key}: {val} lbs' for (key,val) in weights.items()])
    return weight_str

from secret import token_str

def line_reply(token: str, msg:str):
    url = "https://api.line.me/v2/bot/message/reply"
    #url = "http://127.0.0.1:7000"
    x = requests.post(url,
        json={'replyToken':token, 'messages':[{'type':'text','text':msg}]},
        headers={'Content-Type':'application/json','Authorization':token_str}
    )
    print(x.content)
    

from linebot import Webhook
@app.post("/webhook")
async def post_webhook(hook: Webhook, bg: BackgroundTasks):
    for event in hook.events:
        if event.message:
            reply_msg = search(event.message.text)
            bg.add_task(line_reply,event.replyToken,reply_msg)
    return {}
