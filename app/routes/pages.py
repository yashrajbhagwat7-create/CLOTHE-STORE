from fastapi import APIRouter, Request
from fastapi import Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_429_TOO_MANY_REQUESTS

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


@router.post("/contact", response_class=HTMLResponse)
async def submit_contact(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    subject: str = Form(""),
    message: str = Form(...),
):
    from app.core.contact_db import save_submission
    from app.core.rate_limiter import check_and_increment_rate_limit

    def _clean(s: str) -> str:
        return (s or "").strip()

    name_c = _clean(name)
    email_c = _clean(email)
    subject_c = _clean(subject)
    message_c = _clean(message)

    # Rate limiting (fixed window)
    # Default: 5 submissions per 10 minutes per client IP.
    client_ip = getattr(request.client, "host", None) if request.client else None
    key_ip = (client_ip or "unknown").strip()

    window_seconds = 10 * 60
    max_requests = 5

    rl = check_and_increment_rate_limit(
        key=f"ip:{key_ip}",
        window_seconds=window_seconds,
        max_requests=max_requests,
    )

    if not rl.allowed:
        return templates.TemplateResponse(
            request=request,
            name="contact.html",
            context={
                "request": request,
                "store": store,
                "success": False,
                "error": "Too many messages from your location. Please wait a few minutes and try again.",
                "form": {
                    "name": name_c,
                    "email": email_c,
                    "subject": subject_c or "",
                    "message": message_c,
                },
            },
            status_code=HTTP_429_TOO_MANY_REQUESTS,
        )

    errors = []

    if len(name_c) < 2 or len(name_c) > 100:
        errors.append("Please enter a valid name (2-100 characters).")

    if "@" not in email_c or len(email_c) > 255:
        errors.append("Please enter a valid email address.")

    # subject is optional
    if subject_c == "":
        subject_c = None

    if len(message_c) < 10 or len(message_c) > 5000:
        errors.append("Please enter a message (at least 10 characters).")

    if errors:
        # Render same page with server-side error
        return templates.TemplateResponse(
            request=request,
            name="contact.html",
            context={
                "request": request,
                "store": store,
                "success": False,
                "error": " ".join(errors),
                "form": {
                    "name": name_c,
                    "email": email_c,
                    "subject": subject_c or "",
                    "message": message_c,
                },
            },
            status_code=HTTP_400_BAD_REQUEST,
        )

    try:
        save_submission(
            name=name_c,
            email=email_c,
            subject=subject_c,
            message=message_c,
        )
    except Exception:
        return templates.TemplateResponse(
            request=request,
            name="contact.html",
            context={
                "request": request,
                "store": store,
                "success": False,
                "error": "Something went wrong while saving your message. Please try again.",
                "form": {
                    "name": name_c,
                    "email": email_c,
                    "subject": subject_c or "",
                    "message": message_c,
                },
            },
            status_code=500,
        )

    return templates.TemplateResponse(
        request=request,
        name="contact.html",
        context={
            "request": request,
            "store": store,
            "success": True,
            "error": None,
            "form": {},
        },
    )

