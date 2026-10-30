# VAULT: Password Generator

A beginner-friendly password generator written in Python, with two ways to use it:

- **VAULT web app**: a polished browser interface built with Flask, HTML, CSS and vanilla JavaScript.
- **Command-line program**: the original interactive terminal version.

Both use the same generator code, which creates strong random passwords with Python's built-in `secrets` module.

It started as a learning project, so the code is kept small, well-commented and covered by automated tests.

## Features

- Secure randomness from Python's `secrets` module.
- Password length from 8 to 64 characters, with a default of 16.
- Turn uppercase letters, lowercase letters, digits and symbols on or off.
- Every character type you choose is guaranteed to appear at least once.
- Passwords are never saved to files, logs or browser storage.

**Web app**

- Length slider, accessible on/off switches, and copy, hide/show and regenerate buttons.
- A configuration strength estimate that shows exactly how it is calculated.
- Passwords are generated on the server, and every request is validated there too.
- Works with a keyboard and screen reader, and adapts to phone, tablet and desktop screens.

**Command line**

- Invalid answers are explained and the question is asked again, instead of crashing.
- Generate as many passwords as you like in one session, reusing the same settings.
- Ctrl+C or end-of-input exits politely with "Goodbye!" instead of an error message.

## Requirements

- Python 3.10 or newer.
- [Flask](https://flask.palletsprojects.com/) for the web app only, installed from `requirements.txt`. The command-line program needs nothing beyond Python itself.

Check your Python version with:

```bash
python --version
```

## Getting the code

Clone the repository:

```bash
git clone https://github.com/rkslakshay/password-generator
```

Then move into the project folder:

```bash
cd password-generator
```

## Setting up the web app

These steps are for Windows. If `python` is not recognised, use `py` instead (the Python launcher for Windows).

1. Create a virtual environment, a private folder for this project's packages:

   ```powershell
   python -m venv .venv
   ```

2. Activate it. In PowerShell:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

   In Command Prompt, use `.venv\Scripts\activate.bat` instead. Your prompt should now start with `(.venv)`.

   If PowerShell says running scripts is disabled, you can skip activating and run the virtual environment's Python directly, as `.venv\Scripts\python.exe`, in place of `python` in the commands below.

3. Install Flask:

   ```powershell
   python -m pip install -r requirements.txt
   ```

## Running the web app

With the virtual environment active:

```powershell
python app.py
```

Then open <http://127.0.0.1:5000> in your browser. A password is generated as soon as the page loads.

Press **Ctrl+C** in the terminal to stop the server.

### Using VAULT

- Drag the **Length** slider, or focus it and use the arrow keys, to pick 8–64 characters.
- Use the four **Character types** switches. Changing a setting creates a new password straight away.
- **Copy** puts the password on your clipboard and shows a confirmation.
- **Hide / Show** masks the password, for example while sharing your screen.
- **Regenerate** creates a new password with the same settings.

If you switch off every character type, VAULT explains that at least one is needed and disables generation until you pick one.

### Configuration strength

The strength panel rates your **settings**, not one particular password. It shows its working:

> estimated entropy = length × log₂(pool size)

The pool size is how many different characters your settings allow: 26 uppercase + 26 lowercase + 10 digits + 10 symbols = 72 when all four are on. This assumes every character is picked at random, which VAULT does. Guaranteeing one character of each type reduces the true figure very slightly, so treat the number as an upper bound.

| Rating | Estimated entropy |
|--------|-------------------|
| Weak | under 45 bits |
| Fair | 45–64 bits |
| Strong | 65–89 bits |
| Excellent | 90 bits or more |

A high rating does not prove a password is safe. It can still be stolen or reused, so use a different password for every account and keep them in a password manager.

### The API

The page gets passwords from one endpoint, `POST /api/generate`, which expects JSON with exactly these fields:

```json
{"length": 16, "uppercase": true, "lowercase": true, "digits": true, "symbols": true}
```

| Response | When |
|----------|------|
| `200` `{"password": "..."}` | Success |
| `400` `{"error": "..."}` | Invalid length, wrong types, missing or unknown fields, no character types selected, or malformed JSON |
| `405` | Any method other than POST |
| `413` | Request body over 1 KB |
| `415` | The body is not sent as JSON |

Error messages never contain a password. API responses are sent with `Cache-Control: no-store` so browsers and proxies don't keep a copy.

## Running the command-line program

From the project folder (no virtual environment needed):

```bash
python password_generator.py
```

### Example session

```text
Welcome to the Password Generator!
Password length (8-64, press Enter for 16): 20
Include uppercase letters (A-Z)? (y/n): y
Include lowercase letters (a-z)? (y/n): y
Include digits (0-9)? (y/n): y
Include symbols (!@#$%^&*-_)? (y/n): n

Your password: <a random 20-character password appears here>

Generate another password with the same settings? (y/n): n
Goodbye!
```

Answering `y` to the last question creates another password with the same length and character types. To change the settings, exit and run the program again.

## Password options

### Length

- Any whole number from **8** to **64**.
- In the command-line program, press **Enter** without typing anything to use the default of **16**. Anything else, such as `abc`, `12.5`, `-5` or `100`, shows an error and asks again.
- The web app's slider starts at 16.

### Character types

| Type | Characters |
|------|------------|
| Uppercase letters | `A`–`Z` |
| Lowercase letters | `a`–`z` |
| Digits | `0`–`9` |
| Symbols | `! @ # $ % ^ & * - _` |

You must choose at least one type. The command-line program asks about each type separately and accepts `y`/`yes` or `n`/`no` in any letter case. If you answer no to all four, it explains the problem and asks again.

The symbol list is deliberately short. These symbols are accepted by most websites and are easy to type.

## Running the tests

With the virtual environment active, from the project folder:

```powershell
python -m unittest -v
```

This runs 53 tests using Python's built-in `unittest` framework.

**`test_password_generator.py`** (26 tests, command-line program and generator):

- length and yes/no parsing, including the 8 and 64 boundaries and the blank default
- all 15 possible combinations of character types: correct length, every chosen type present, no unchosen types
- rejection of invalid arguments passed to `generate_password()`
- the interactive questions, using simulated typing, including retries, repeated generation and Ctrl+C / end-of-input

**`test_app.py`** (27 tests, web app):

- the page loads with the right settings, security headers and no inline scripts
- valid generation for all 15 type combinations and both length boundaries
- the server rejects invalid lengths, wrong types, missing or unknown fields, no character types, malformed JSON, the wrong content type, oversized bodies and wrong methods
- unexpected errors return a generic message, and nothing about the password is logged

The web tests need Flask installed. To run only the command-line tests without Flask:

```bash
python -m unittest test_password_generator -v
```

The tests never print the passwords they generate.

## Project structure

```text
password-generator/
├── app.py                      # Flask web app (VAULT)
├── password_generator.py       # Password generator and command-line program
├── requirements.txt            # Web app dependency (Flask)
├── static/
│   ├── css/styles.css          # Web app styles
│   ├── js/app.js               # Web app behaviour
│   └── favicon.svg             # Browser tab icon
├── templates/
│   └── index.html              # Web app page
├── test_app.py                 # Web app tests
├── test_password_generator.py  # Generator and command-line tests
└── README.md                   # This file
```

How the pieces fit together:

- **`password_generator.py`** holds the **logic functions**: `parse_length()`, `parse_yes_no()`, `select_character_sets()` and `generate_password()`. They decide things but never ask questions or print, which keeps them easy to test. The same file holds the **interactive functions** for the command line: `ask_length()`, `ask_yes_no()`, `ask_character_sets()` and `main()`.
- **`app.py`** imports the generator and reuses `select_character_sets()` and `generate_password()`. It only adds web-specific checks, such as making sure the JSON has the right fields and types.
- **`templates/index.html`** gets the length limits and symbol list from the Python constants, so they only ever need changing in one place.

## Security choices

- **`secrets.choice()` picks every character.** The `secrets` module uses your operating system's secure source of randomness, which is designed for passwords and security tokens.
- **Python's `random` module is not used.** `random` is fine for games and simulations, but it is predictable: someone who sees enough of its output can work out what comes next. That makes it unsuitable for passwords.
- **One character from each chosen type is picked first**, so every type you selected is guaranteed to appear. The remaining characters are picked from all your chosen characters combined, so each allowed character is equally likely.
- **The characters are shuffled with `secrets.SystemRandom().shuffle()`.** Without shuffling, the guaranteed characters would always sit at the start of the password in the same order, which would make it easier to guess.
- **Passwords are never saved.** The command-line program prints them once. The web app sends them once in the response and keeps them only in the page's memory. Neither writes them to files, logs or browser storage.

**Web app protections**

- **The server checks every request itself**, whatever the browser sends, and accepts only whole-number lengths in range, true/false switches, and the four approved character sets.
- **Error messages are safe to show.** They come from the app's own validation. Unexpected errors return a generic message, and only the error type is logged, never request data.
- **Debug mode is off**, so tracebacks and Flask's interactive debugger are never shown to users.
- **Security headers:**
  - a strict Content-Security-Policy, which only allows the app's own scripts and styles and blocks inline code
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: no-referrer`
- **No external requests.** No web fonts, analytics or third-party scripts are loaded.

## Limitations

- `python app.py` uses Flask's built-in development server, which is meant for running on your own computer. Putting VAULT on the internet would need a production server (such as Waitress or Gunicorn) behind HTTPS, which this project does not include.
- The web app's server only listens on your own computer (`127.0.0.1`).
- The command-line program leaves passwords visible in your terminal and its scroll history until you clear it.
- In the command-line program, changing the length or character types means restarting it, and settings can't be given as command-line arguments.
- The symbol list is fixed and cannot be customised.
- There is no option to leave out look-alike characters such as `0`/`O` or `1`/`l`/`I`.
- Copying in the web app needs a browser that allows clipboard access. If it is blocked, VAULT says so and you can copy by hand.
- The web app needs JavaScript to generate passwords.

## Possible future improvements

These ideas are **not implemented yet**:

- An option to exclude look-alike characters.
- Accept command-line settings as arguments (for example with Python's `argparse`).
- Clear copied passwords from the clipboard after a short time.
- Deployment instructions for a production server.
