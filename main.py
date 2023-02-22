from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")

def today():
    from datetime import date
    return date.today().strftime("%Y-%m-%d")

@app.get("/add", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("add.html", {"request": request, "today": today()})
