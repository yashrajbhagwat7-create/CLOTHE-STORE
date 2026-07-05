from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.store import store

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def render(template_name: str, request: Request):
    # Keep TemplateResponse signature compatible across FastAPI/Starlette versions
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={"request": request, "store": store},
    )


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return render("index.html", request)


@router.get("/men", response_class=HTMLResponse)
async def men(request: Request):
    return render("men.html", request)


@router.get("/women", response_class=HTMLResponse)
async def women(request: Request):
    return render("women.html", request)


@router.get("/kids", response_class=HTMLResponse)
async def kids(request: Request):
    return render("kids.html", request)


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return render("about.html", request)


@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return render("contact.html", request)
        
    

