"""A beginner-friendly command-line password generator.

Generated passwords are only ever shown on screen. They are never saved
to files or logs.
"""

import secrets
import string

MIN_LENGTH = 8
MAX_LENGTH = 64
DEFAULT_LENGTH = 16

UPPERCASE = string.ascii_uppercase
LOWERCASE = string.ascii_lowercase
DIGITS = string.digits
SYMBOLS = "!@#$%^&*-_"

# The only character sets generate_password() will accept.
ALLOWED_CHARACTER_SETS = (UPPERCASE, LOWERCASE, DIGITS, SYMBOLS)


def parse_length(text: str) -> int:
    """Convert the user's answer into a valid password length.

    An empty answer means "use the default length". Raises ValueError if
    the text is not a whole number between MIN_LENGTH and MAX_LENGTH.
    """
    text = text.strip()
    if text == "":
        return DEFAULT_LENGTH

    # int() would also accept "+16", "1_6" and non-English digits like "١٦",
    # so only plain 0-9 digits are allowed through.
    if not (text.isascii() and text.isdigit()):
        raise ValueError("Please enter a whole number, such as 16.")

    length = int(text)
    if length < MIN_LENGTH or length > MAX_LENGTH:
        raise ValueError(f"Length must be between {MIN_LENGTH} and {MAX_LENGTH}.")
    return length


def parse_yes_no(text: str) -> bool:
    """Convert a yes/no answer into True or False.

    Accepts y, yes, n and no in any letter case. Raises ValueError for
    anything else, including an empty answer.
    """
    answer = text.strip().lower()
    if answer in ("y", "yes"):
        return True
    if answer in ("n", "no"):
        return False
    raise ValueError("Please answer y or n.")


def select_character_sets(use_uppercase: bool, use_lowercase: bool,
                          use_digits: bool, use_symbols: bool) -> list[str]:
    """Return the character sets the user chose, in a fixed order.

    Raises ValueError if no character type was chosen.
    """
    chosen = []
    if use_uppercase:
        chosen.append(UPPERCASE)
    if use_lowercase:
        chosen.append(LOWERCASE)
    if use_digits:
        chosen.append(DIGITS)
    if use_symbols:
        chosen.append(SYMBOLS)

    if not chosen:
        raise ValueError("Please choose at least one character type.")
    return chosen


def generate_password(length: int, character_sets: list[str]) -> str:
    """Generate a secure random password.

    The password contains at least one character from every set in
    character_sets. Raises TypeError if an argument has the wrong type,
    and ValueError if an argument has an invalid value.
    """
    # True and False count as ints in Python, so they are rejected separately.
    if isinstance(length, bool) or not isinstance(length, int):
        raise TypeError("length must be a whole number (int).")
    if length < MIN_LENGTH or length > MAX_LENGTH:
        raise ValueError(f"length must be between {MIN_LENGTH} and {MAX_LENGTH}.")

    if not isinstance(character_sets, list):
        raise TypeError("character_sets must be a list of strings.")
    if not character_sets:
        raise ValueError("character_sets must contain at least one character set.")
    for character_set in character_sets:
        if not isinstance(character_set, str):
            raise TypeError("Each character set must be a string.")
        if character_set == "":
            raise ValueError("Character sets must not be empty.")
        if character_set not in ALLOWED_CHARACTER_SETS:
            raise ValueError("Unknown character set. Use the sets from select_character_sets().")
    if len(set(character_sets)) != len(character_sets):
        raise ValueError("Each character set may only be given once.")

    # Step 1: one character from each chosen set guarantees every type appears.
    password_chars = [secrets.choice(character_set) for character_set in character_sets]

    # Step 2: fill the remaining spots from all chosen characters combined,
    # so every allowed character is equally likely.
    pool = "".join(character_sets)
    for _ in range(length - len(password_chars)):
        password_chars.append(secrets.choice(pool))

    # Step 3: shuffle, otherwise the guaranteed characters would always come first.
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)


def ask_length() -> int:
    """Ask for a password length until the user enters a valid one."""
    while True:
        answer = input(f"Password length ({MIN_LENGTH}-{MAX_LENGTH}, "
                       f"press Enter for {DEFAULT_LENGTH}): ")
        try:
            return parse_length(answer)
        except ValueError as error:
            print(error)


def ask_yes_no(question: str) -> bool:
    """Ask a yes/no question until the user gives a valid answer."""
    while True:
        answer = input(f"{question} (y/n): ")
        try:
            return parse_yes_no(answer)
        except ValueError as error:
            print(error)


def ask_character_sets() -> list[str]:
    """Ask which character types to use until at least one is chosen."""
    while True:
        use_uppercase = ask_yes_no("Include uppercase letters (A-Z)?")
        use_lowercase = ask_yes_no("Include lowercase letters (a-z)?")
        use_digits = ask_yes_no("Include digits (0-9)?")
        use_symbols = ask_yes_no(f"Include symbols ({SYMBOLS})?")
        try:
            return select_character_sets(use_uppercase, use_lowercase,
                                         use_digits, use_symbols)
        except ValueError as error:
            print(f"{error} Let's try again.")


def main() -> None:
    """Run one password-generating session in the terminal."""
    # Ctrl+C raises KeyboardInterrupt and end-of-input raises EOFError.
    # Catching both here covers every prompt, so the user never sees a traceback.
    try:
        print("Welcome to the Password Generator!")
        length = ask_length()
        character_sets = ask_character_sets()

        while True:
            password = generate_password(length, character_sets)
            # This is the only place a password is ever shown.
            print(f"\nYour password: {password}\n")
            if not ask_yes_no("Generate another password with the same settings?"):
                break
    except (KeyboardInterrupt, EOFError):
        print()  # Finish the half-written prompt line.

    print("Goodbye!")


if __name__ == "__main__":
    main()
