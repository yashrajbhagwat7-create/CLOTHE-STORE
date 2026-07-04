from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Static Folder
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates Folder
templates = Jinja2Templates(directory="templates")

store = {
    "name": "BlueWave Clothing",
    "owner": "Yashraj Bhagwat",
    "location": "Yewalewadi, Kondhwa Road, Pune",
    "phone": "+91 9876******",
    "email": "bluewave@gmail.com",
    "timing": "Monday -Saturday (10 AM - 9 PM)",
    "description":
        "Fashion for Men, Women and Kids with premium quality at affordable prices."
}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
        "store": store,
        }
    )


@app.get("/men", response_class=HTMLResponse)
async def men(request: Request):
    return templates.TemplateResponse(
        request,
        "men.html",
        {
            "request": request,
            "store": store
        }
    )


@app.get("/woman", response_class=HTMLResponse)
async def women(request: Request):
    return templates.TemplateResponse(
        "woman.html",
        {
            "request": request,
            "store": store
        }
    )


@app.get("/kids", response_class=HTMLResponse)
async def kids(request: Request):
    return templates.TemplateResponse(
        "kids.html",
        {
            "request": request,
            "store": store
        }
    )


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse(
        "about.html",
        {
            "request": request,
            "store": store
        }
    )


@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse(
        "contact.html",
        {
            "request": request,
            "store": store
        }
    )