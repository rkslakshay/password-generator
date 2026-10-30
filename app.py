"""VAULT: a small Flask web app built on password_generator.py.

Passwords are generated on the server by the existing generator and sent
back once in the response. They are never stored, logged, or included
in error messages.

Run with:  python app.py
"""

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

import password_generator as pg

GITHUB_URL = "https://github.com/rkslakshay/password-generator"

# The JSON fields a generate request must contain, and nothing else.
CHARACTER_OPTIONS = ("uppercase", "lowercase", "digits", "symbols")
REQUIRED_FIELDS = {"length", *CHARACTER_OPTIONS}

# Short, safe messages for HTTP errors. Werkzeug's defaults are longer.
HTTP_ERROR_MESSAGES = {
    404: "Not found.",
    405: "Method not allowed.",
    413: "Request is too large.",
}

app = Flask(__name__)
# A generate request is only about 80 bytes, so anything over 1 KB is rejected.
app.config["MAX_CONTENT_LENGTH"] = 1024


def error_response(message: str, status: int):
    """Return a JSON error like {"error": "..."} with the given HTTP status."""
    return jsonify(error=message), status


def parse_generate_request(data) -> tuple[int, list[str]]:
    """Check the shape and types of a generate request.

    Returns (length, character_sets). Raises ValueError with a message
    that is safe to show the user. Range checks and the "at least one
    type" rule are left to the existing generator functions.
    """
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")

    missing = REQUIRED_FIELDS - data.keys()
    if missing:
        raise ValueError(f"Missing field(s): {', '.join(sorted(missing))}.")
    unknown = data.keys() - REQUIRED_FIELDS
    if unknown:
        raise ValueError(f"Unknown field(s): {', '.join(sorted(unknown))}.")

    length = data["length"]
    # True and False count as ints in Python, so they are rejected separately.
    if isinstance(length, bool) or not isinstance(length, int):
        raise ValueError("length must be a whole number.")

    for name in CHARACTER_OPTIONS:
        if not isinstance(data[name], bool):
            raise ValueError(f"{name} must be true or false.")

    character_sets = pg.select_character_sets(
        data["uppercase"], data["lowercase"], data["digits"], data["symbols"])
    return length, character_sets


@app.get("/")
def index():
    return render_template(
        "index.html",
        min_length=pg.MIN_LENGTH,
        max_length=pg.MAX_LENGTH,
        default_length=pg.DEFAULT_LENGTH,
        symbols=pg.SYMBOLS,
        pool_sizes={
            "uppercase": len(pg.UPPERCASE),
            "lowercase": len(pg.LOWERCASE),
            "digits": len(pg.DIGITS),
            "symbols": len(pg.SYMBOLS),
        },
        github_url=GITHUB_URL,
    )


@app.post("/api/generate")
def generate():
    if not request.is_json:
        return error_response("Send the request as JSON (Content-Type: application/json).", 415)

    # silent=True turns malformed JSON into None, which is rejected below.
    data = request.get_json(silent=True)
    try:
        length, character_sets = parse_generate_request(data)
        password = pg.generate_password(length, character_sets)
    except ValueError as error:
        # These messages come from our own validation and never contain a password.
        return error_response(str(error), 400)

    return jsonify(password=password)


@app.after_request
def add_security_headers(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; "
        "connect-src 'self'; object-src 'none'; base-uri 'none'; "
        "form-action 'self'; frame-ancestors 'none'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    if request.path.startswith("/api/"):
        # Stop browsers and proxies from keeping a copy of a password.
        response.headers["Cache-Control"] = "no-store"
    return response


@app.errorhandler(HTTPException)
def handle_http_error(error):
    message = HTTP_ERROR_MESSAGES.get(error.code, "Request could not be processed.")
    return error_response(message, error.code)


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    # Log only the error type and path, never request data or details.
    app.logger.error("Unexpected %s while handling %s %s",
                     type(error).__name__, request.method, request.path)
    return error_response("Something went wrong. Please try again.", 500)


if __name__ == "__main__":
    # debug=False keeps tracebacks and the interactive debugger away from users.
    app.run(host="127.0.0.1", port=5000, debug=False)
