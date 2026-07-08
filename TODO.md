# TODO

- [x] Implement rate limiting for `POST /contact` (default 5 submissions / 10 minutes per IP) using SQLite-backed counters.
- [x] Return HTTP 429 with a user-friendly error on rate limit hits.
- [ ] (Optional) Add email-based throttling and/or rate-limit headers.


