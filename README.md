# Event Registration Demo

A small Flask + Supabase app used for teaching how a backend API and a frontend fit together.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your Supabase URL and publishable key
python app.py
```

Open http://127.0.0.1:5001

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | /api/users | List users (used by the fake-login dropdown) |
| GET | /api/events | Browse events |
| GET | /api/events/{id} | Event details |
| POST | /api/registrations | Create registration, 201 or 409 |
| GET | /api/me/registrations | Current user's registrations |
| GET | /api/events/{id}/registrations | Attendee list, owning organiser only |

Routes that need a user read the `X-User-Id` header. There is no real login yet;
the frontend dropdown picks a user and sends their id in that header.

## Tables

- `users`: id, email, role
- `events`: id, organiser_id, title, capacity, status
- `registrations`: id, user_id, event_id
