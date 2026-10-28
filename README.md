# Password Generator

A beginner-friendly command-line password generator written in Python. You choose a length and which kinds of characters to use, and it creates strong random passwords using Python's built-in `secrets` module.

It was built as a learning project, so the code is kept in one small, well-commented file with a full set of automated tests.

## Features

- Secure randomness from Python's `secrets` module.
- Choose a password length from 8 to 64 characters (press Enter for the default of 16).
- Turn uppercase letters, lowercase letters, digits and symbols on or off.
- Every character type you choose is guaranteed to appear at least once.
- Invalid answers are explained and the question is asked again, instead of crashing.
- Generate as many passwords as you like in one session, reusing the same settings.
- Ctrl+C or end-of-input exits politely with "Goodbye!" instead of an error message.
- Passwords are only shown on screen. They are never saved to files or logs.

## Requirements

- Python 3.10 or newer.
- No third-party packages. Everything used comes with Python.

Check your Python version with:

```bash
python --version
```

## Getting the code

Clone the repository, replacing the placeholder with the real repository URL:

```bash
git clone <YOUR-GITHUB-REPOSITORY-URL>
```

Then move into the project folder:

```bash
cd password-generator
```

## Running the program

On Windows, from the project folder:

```bash
python password_generator.py
```

If `python` is not recognised, try `py password_generator.py` instead (the Python launcher for Windows).

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
- Press **Enter** without typing anything to use the default of **16**.
- Anything else, such as `abc`, `12.5`, `-5` or `100`, shows an error and asks again.

### Character types

You are asked about each type separately and must answer `y`/`yes` or `n`/`no` (any letter case):

| Type | Characters |
|------|------------|
| Uppercase letters | `A`–`Z` |
| Lowercase letters | `a`–`z` |
| Digits | `0`–`9` |
| Symbols | `! @ # $ % ^ & * - _` |

You must choose at least one type. If you answer no to all four, the program explains the problem and asks the four questions again.

The symbol list is deliberately short. These symbols are accepted by most websites and are easy to type.

## Running the tests

From the project folder:

```bash
python -m unittest -v
```

This runs 26 tests using Python's built-in `unittest` framework. They check:

- length and yes/no parsing, including the 8 and 64 boundaries and the blank default
- all 15 possible combinations of character types: correct length, every chosen type present, no unchosen types
- rejection of invalid arguments passed to `generate_password()`
- the interactive questions, using simulated typing, including retries, repeated generation and Ctrl+C / end-of-input

The tests never print the passwords they generate.

## Project structure

```text
password-generator/
├── password_generator.py       # The program
├── test_password_generator.py  # Automated tests
└── README.md                   # This file
```

Inside `password_generator.py` the code is split into two groups:

- **Logic functions** decide things but never ask questions or print: `parse_length()`, `parse_yes_no()`, `select_character_sets()` and `generate_password()`. Keeping them separate makes them easy to test.
- **Interactive functions** talk to the user and pass the answers to the logic functions: `ask_length()`, `ask_yes_no()`, `ask_character_sets()` and `main()`.

## Security choices

- **`secrets.choice()` picks every character.** The `secrets` module uses your operating system's secure source of randomness, which is designed for passwords and security tokens.
- **Python's `random` module is not used.** `random` is fine for games and simulations, but it is predictable: someone who sees enough of its output can work out what comes next. That makes it unsuitable for passwords.
- **One character from each chosen type is picked first**, so every type you selected is guaranteed to appear. The remaining characters are picked from all your chosen characters combined, so each allowed character is equally likely.
- **The characters are shuffled with `secrets.SystemRandom().shuffle()`.** Without shuffling, the guaranteed characters would always sit at the start of the password in the same order, which would make it easier to guess.
- **Passwords are never saved.** They are printed once on screen and not written to any file or log.

## Limitations

- Generated passwords stay visible in your terminal window and its scroll history until you clear it.
- To change the length or character types, you have to exit and start the program again.
- Settings can only be entered by answering the questions, not as command-line arguments.
- The symbol list is fixed and cannot be customised.
- There is no option to leave out look-alike characters such as `0`/`O` or `1`/`l`/`I`.
- Passwords are not copied to the clipboard automatically. Copy them by hand.

## Possible future improvements

These ideas are **not implemented yet**:

- Offer to change settings without restarting the program.
- Accept settings as command-line arguments (for example with Python's `argparse`).
- An option to exclude look-alike characters.
- Generate several passwords at once.
- Show an estimate of password strength.
