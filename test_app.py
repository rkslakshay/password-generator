"""Automated tests for the VAULT web app in app.py.

Run with:  python -m unittest -v

Like the CLI tests, these never print generated passwords, and failure
messages describe the problem without including the password itself.
"""

import itertools
import json
import unittest
from unittest.mock import patch

import password_generator as pg
from app import app

ALL_TYPES = [pg.UPPERCASE, pg.LOWERCASE, pg.DIGITS, pg.SYMBOLS]
OPTION_NAMES = ["uppercase", "lowercase", "digits", "symbols"]


def make_request(length=16, uppercase=True, lowercase=True, digits=True, symbols=True):
    """Build a valid generate request body that a test can then change."""
    return {"length": length, "uppercase": uppercase, "lowercase": lowercase,
            "digits": digits, "symbols": symbols}


class WebTestCase(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def post_json(self, body):
        return self.client.post("/api/generate", json=body)

    def assert_json_error(self, response, status, message_part=None):
        """Check a response is a JSON error with only an "error" field."""
        self.assertEqual(response.status_code, status)
        self.assertEqual(response.mimetype, "application/json")
        data = response.get_json()
        self.assertEqual(list(data), ["error"])
        self.assertIsInstance(data["error"], str)
        if message_part is not None:
            self.assertIn(message_part, data["error"])


class TestIndexPage(WebTestCase):

    def test_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("VAULT", html)
        self.assertIn("Create passwords that protect what matters.", html)
        self.assertIn("https://github.com/rkslakshay/password-generator", html)

    def test_page_uses_generator_settings(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn('min="8"', html)
        self.assertIn('max="64"', html)
        self.assertIn('value="16"', html)
        # The page shows the exact curated symbols (& is HTML-escaped).
        self.assertIn("!@#$%^&amp;*-_", html)

    def test_page_has_no_inline_scripts_or_styles(self):
        """The Content-Security-Policy blocks inline code, so the page must not need it."""
        html = self.client.get("/").get_data(as_text=True)
        self.assertNotIn("<script>", html)
        self.assertNotIn(" style=", html)
        self.assertNotIn("onclick", html)

    def test_static_files_are_served(self):
        for path in ["/static/css/styles.css", "/static/js/app.js", "/static/favicon.svg"]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                response.close()

    def test_security_headers(self):
        response = self.client.get("/")
        self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
        self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["Referrer-Policy"], "no-referrer")


class TestGenerateValid(WebTestCase):

    def test_default_request(self):
        response = self.post_json(make_request())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        data = response.get_json()
        self.assertEqual(list(data), ["password"])
        self.assertEqual(len(data["password"]), 16)

    def test_response_is_not_cached(self):
        response = self.post_json(make_request())
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_length_boundaries(self):
        for length in [8, 64]:
            with self.subTest(length=length):
                response = self.post_json(make_request(length=length))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.get_json()["password"]), length)

    def test_all_15_type_combinations(self):
        combinations = [flags for flags in itertools.product([True, False], repeat=4)
                        if any(flags)]
        self.assertEqual(len(combinations), 15)

        for flags in combinations:
            body = make_request(8, *flags)
            selected = [s for s, on in zip(ALL_TYPES, flags) if on]
            unselected = "".join(s for s, on in zip(ALL_TYPES, flags) if not on)
            with self.subTest(flags=flags):
                for _ in range(20):
                    response = self.post_json(body)
                    self.assertEqual(response.status_code, 200)
                    password = response.get_json()["password"]
                    self.assertEqual(len(password), 8)
                    for character_set in selected:
                        self.assertTrue(any(c in character_set for c in password),
                                        "a selected character type is missing")
                    self.assertFalse(any(c in unselected for c in password),
                                     "password contains an unselected character type")

    def test_reuses_existing_generator(self):
        with patch.object(pg, "generate_password", wraps=pg.generate_password) as spy:
            response = self.post_json(make_request(20, True, False, True, False))
        self.assertEqual(response.status_code, 200)
        spy.assert_called_once_with(20, [pg.UPPERCASE, pg.DIGITS])

    def test_nothing_is_logged(self):
        with self.assertNoLogs(level="DEBUG"):
            response = self.post_json(make_request())
        self.assertEqual(response.status_code, 200)


class TestGenerateInvalid(WebTestCase):
    """The server must reject bad requests itself, whatever the browser sends."""

    def test_length_out_of_range(self):
        for length in [7, 65, 0, -1, 1000, 10 ** 30]:
            with self.subTest(length=length):
                self.assert_json_error(self.post_json(make_request(length=length)),
                                       400, "between 8 and 64")

    def test_length_wrong_type(self):
        for length in ["16", 16.0, 16.5, True, False, None, [16], {"value": 16}]:
            with self.subTest(length=length):
                self.assert_json_error(self.post_json(make_request(length=length)),
                                       400, "whole number")

    def test_no_character_types(self):
        body = make_request(16, False, False, False, False)
        self.assert_json_error(self.post_json(body), 400, "at least one character type")

    def test_character_option_wrong_type(self):
        for name in OPTION_NAMES:
            for value in ["true", 1, 0, None, "yes", []]:
                with self.subTest(option=name, value=value):
                    body = make_request()
                    body[name] = value
                    self.assert_json_error(self.post_json(body), 400, f"{name} must be true or false")

    def test_missing_fields(self):
        for name in ["length", *OPTION_NAMES]:
            with self.subTest(missing=name):
                body = make_request()
                del body[name]
                self.assert_json_error(self.post_json(body), 400, f"Missing field(s): {name}")

    def test_unknown_field(self):
        body = make_request()
        body["exclude_ambiguous"] = True
        self.assert_json_error(self.post_json(body), 400, "Unknown field(s): exclude_ambiguous")

    def test_body_not_an_object(self):
        for body in [[], [16, True], "16", 16, None]:
            with self.subTest(body=body):
                response = self.client.post("/api/generate", data=json.dumps(body),
                                            content_type="application/json")
                self.assert_json_error(response, 400, "JSON object")

    def test_malformed_json(self):
        for raw in ["{", "{'length': 16}", "", "length=16"]:
            with self.subTest(raw=raw):
                response = self.client.post("/api/generate", data=raw,
                                            content_type="application/json")
                self.assert_json_error(response, 400, "JSON object")

    def test_wrong_content_type(self):
        response = self.client.post("/api/generate", data=json.dumps(make_request()),
                                    content_type="text/plain")
        self.assert_json_error(response, 415, "JSON")

    def test_form_post_rejected(self):
        response = self.client.post("/api/generate", data={"length": "16"})
        self.assert_json_error(response, 415)

    def test_body_too_large(self):
        body = make_request()
        body["padding"] = "x" * 2000
        self.assert_json_error(self.post_json(body), 413, "too large")

    def test_wrong_method(self):
        for method in [self.client.get, self.client.put, self.client.delete]:
            with self.subTest(method=method.__name__):
                self.assert_json_error(method("/api/generate"), 405)

    def test_unknown_route(self):
        self.assert_json_error(self.client.get("/api/does-not-exist"), 404, "Not found")

    def test_errors_are_not_cached(self):
        response = self.post_json(make_request(length=7))
        self.assertEqual(response.headers["Cache-Control"], "no-store")


class TestUnexpectedErrors(WebTestCase):

    def test_internal_error_is_generic(self):
        """Unexpected errors return a safe message and log no details."""
        secret_detail = "internal detail that must not leak"
        with patch.object(pg, "generate_password", side_effect=RuntimeError(secret_detail)), \
                self.assertLogs(app.logger, level="ERROR") as logs:
            response = self.post_json(make_request())

        self.assert_json_error(response, 500, "Something went wrong")
        body = response.get_data(as_text=True)
        self.assertNotIn(secret_detail, body)
        self.assertNotIn("Traceback", body)
        log_text = "\n".join(logs.output)
        self.assertIn("RuntimeError", log_text)
        self.assertNotIn(secret_detail, log_text)

    def test_debug_mode_is_off(self):
        self.assertFalse(app.debug)


if __name__ == "__main__":
    unittest.main()
