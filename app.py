import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from postgrest import APIError
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__, static_folder='frontend', static_url_path='')

# Allow the frontend (served from another domain, e.g. Vercel) to call this API.
# FRONTEND_URL is optional; when unset, any origin is allowed (fine for a demo).
CORS(app, origins=os.environ.get('FRONTEND_URL', '*'))

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)


def current_user_id():
    # No login yet: the caller sends their user UUID in this header.
    return request.headers.get("X-User-Id")


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/api/users')
def list_users():
    try:
        response = supabase.table('users').select("*").execute()
    except APIError as error:
        return jsonify(error=error.message), 500
    return jsonify(response.data)


# GET /api/events  - browse events
@app.route('/api/events')
def list_events():
    try:
        response = supabase.table('events').select("*").execute()
    except APIError as error:
        return jsonify(error=error.message), 500
    return jsonify(response.data)


# GET /api/events/<id>  - event details
@app.route('/api/events/<event_id>')
def get_event(event_id):
    try:
        response = supabase.table('events').select("*").eq("id", event_id).execute()
    except APIError as error:
        return jsonify(error=error.message), 500
    if not response.data:
        return jsonify(error="Event not found"), 404
    return jsonify(response.data[0])


# POST /api/registrations  - create registration, 201 or 409
@app.route('/api/registrations', methods=['POST'])
def create_registration():
    user_id = current_user_id()
    if not user_id:
        return jsonify(error="X-User-Id header required"), 401

    body = request.get_json(silent=True) or {}
    event_id = body.get("event_id")
    if not event_id:
        return jsonify(error="event_id is required"), 400

    try:
        # event must exist and be active
        event = supabase.table('events').select("*").eq("id", event_id).execute().data
        if not event:
            return jsonify(error="Event not found"), 404
        event = event[0]
        if event["status"] != "active":
            return jsonify(error="Event is not open for registration"), 409

        # already registered?
        existing = (supabase.table('registrations').select("id")
                    .eq("event_id", event_id).eq("user_id", user_id).execute().data)
        if existing:
            return jsonify(error="Already registered"), 409

        # capacity full?
        count = (supabase.table('registrations').select("id", count="exact")
                 .eq("event_id", event_id).execute().count)
        if count >= event["capacity"]:
            return jsonify(error="Event is full"), 409

        response = supabase.table('registrations').insert(
            {"event_id": event_id, "user_id": user_id}
        ).execute()
    except APIError as error:
        return jsonify(error=error.message), 500

    return jsonify(response.data[0]), 201


# GET /api/me/registrations  - current user's registrations
@app.route('/api/me/registrations')
def my_registrations():
    user_id = current_user_id()
    if not user_id:
        return jsonify(error="X-User-Id header required"), 401
    try:
        response = (supabase.table('registrations')
                    .select("id, event_id, events(title, status)")
                    .eq("user_id", user_id).execute())
    except APIError as error:
        return jsonify(error=error.message), 500
    return jsonify(response.data)


# GET /api/events/<id>/registrations  - attendee list, owning organiser only
@app.route('/api/events/<event_id>/registrations')
def event_registrations(event_id):
    user_id = current_user_id()
    if not user_id:
        return jsonify(error="X-User-Id header required"), 401
    try:
        event = supabase.table('events').select("organiser_id").eq("id", event_id).execute().data
        if not event:
            return jsonify(error="Event not found"), 404
        if event[0]["organiser_id"] != user_id:
            return jsonify(error="Only the organiser can view attendees"), 403

        response = (supabase.table('registrations')
                    .select("id, user_id, users(email)")
                    .eq("event_id", event_id).execute())
    except APIError as error:
        return jsonify(error=error.message), 500
    return jsonify(response.data)


if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5001)))
