- [x] Identify mismatch / 500 root cause (TemplateResponse parameters)
- [x] Fix TemplateResponse usage for `/men` and other category routes
- [x] Verify page rendering after fix
- [x] Modularize backend with minimal folders: app/core, app/routes
- [x] Move `store` dict into `app/core/store.py`
- [x] Move all page GET routes into `app/routes/pages.py`
- [x] Simplify root `main.py` to only mount static and include router
- [ ] Run `uvicorn main:app --reload --port 8000` and verify `/`, `/men`, `/women`, `/kids`, `/about`, `/contact`
- [ ] Confirm static assets load from `/static/style.css`

