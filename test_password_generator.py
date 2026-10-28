"""Automated tests for password_generator.py.

Run with:  python -m unittest -v

Generated passwords are never printed. Interactive output is captured in
a StringIO buffer, and failure messages describe the problem without
including the password itself.
"""

import io
import itertools
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import password_generator as pg

ALL_TYPES = [pg.UPPERCASE, pg.LOWERCASE, pg.DIGITS, pg.SYMBOLS]


class TestConstants(unittest.TestCase):

    def test_length_rules(self):
        self.assertEqual(pg.MIN_LENGTH, 8)
        self.assertEqual(pg.MAX_LENGTH, 64)
        self.assertEqual(pg.DEFAULT_LENGTH, 16)

    def test_curated_symbols(self):
        self.assertEqual(pg.SYMBOLS, "!@#$%^&*-_")


class TestParseLength(unittest.TestCase):

    def test_valid_lengths(self):
        cases = {"8": 8, "16": 16, "33": 33, "64": 64, " 20 ": 20, "016": 16}
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(pg.parse_length(text), expected)

    def test_blank_uses_default(self):
        for text in ["", "   ", "\t"]:
            with self.subTest(text=text):
                self.assertEqual(pg.parse_length(text), pg.DEFAULT_LENGTH)

    def test_out_of_range(self):
        for text in ["7", "65", "0", "1", "1000000"]:
            with self.subTest(text=text):
                with self.assertRaisesRegex(ValueError, "between 8 and 64"):
                    pg.parse_length(text)

    def test_not_a_whole_number(self):
        for text in ["abc", "12.5", "-5", "+16", "1_6", "١٦", "16a", "1 6"]:
            with self.subTest(text=text):
                with self.assertRaisesRegex(ValueError, "whole number"):
                    pg.parse_length(text)


class TestParseYesNo(unittest.TestCase):

    def test_yes_answers(self):
        for text in ["y", "Y", "yes", "YES", "Yes", "  y  "]:
            with self.subTest(text=text):
                self.assertTrue(pg.parse_yes_no(text))

    def test_no_answers(self):
        for text in ["n", "N", "no", "NO", "No", "  n  "]:
            with self.subTest(text=text):
                self.assertFalse(pg.parse_yes_no(text))

    def test_invalid_answers(self):
        for text in ["", " ", "maybe", "yep", "1", "0", "ye", "true"]:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    pg.parse_yes_no(text)


class TestSelectCharacterSets(unittest.TestCase):

    def test_each_single_type(self):
        for index, expected in enumerate(ALL_TYPES):
            flags = [False] * 4
            flags[index] = True
            with self.subTest(flags=flags):
                self.assertEqual(pg.select_character_sets(*flags), [expected])

    def test_all_types_in_fixed_order(self):
        self.assertEqual(pg.select_character_sets(True, True, True, True), ALL_TYPES)

    def test_no_types_is_rejected(self):
        with self.assertRaises(ValueError):
            pg.select_character_sets(False, False, False, False)


class TestGeneratePassword(unittest.TestCase):

    def test_all_15_type_combinations(self):
        """Every non-empty combination: right length, every chosen type, nothing else."""
        combinations = [flags for flags in itertools.product([True, False], repeat=4)
                        if any(flags)]
        self.assertEqual(len(combinations), 15)

        for flags in combinations:
            selected = pg.select_character_sets(*flags)
            unselected = "".join(s for s in ALL_TYPES if s not in selected)
            for length in [8, 16, 64]:
                with self.subTest(flags=flags, length=length):
                    # Many repetitions, so a "lucky" pass is very unlikely.
                    for _ in range(100):
                        password = pg.generate_password(length, selected)
                        self.assertEqual(len(password), length)
                        for character_set in selected:
                            self.assertTrue(
                                any(c in character_set for c in password),
                                "a selected character type is missing")
                        self.assertFalse(
                            any(c in unselected for c in password),
                            "password contains an unselected character type")

    def test_passwords_are_not_repeated(self):
        passwords = {pg.generate_password(16, ALL_TYPES) for _ in range(100)}
        self.assertEqual(len(passwords), 100)

    def test_uses_secrets_choice_and_shuffle(self):
        """With randomness replaced by predictable fakes, the steps are easy to check."""
        with patch.object(pg.secrets, "choice", side_effect=lambda seq: seq[0]), \
                patch.object(pg.secrets, "SystemRandom") as fake_system_random:
            password = pg.generate_password(8, [pg.UPPERCASE, pg.DIGITS])

        # One "A" and one "0" are guaranteed, then 6 fill characters from the pool.
        self.assertEqual(password, "A0AAAAAA")
        fake_system_random.return_value.shuffle.assert_called_once()

    def test_length_wrong_type(self):
        for length in [16.0, "16", None, True, False]:
            with self.subTest(length=length):
                with self.assertRaises(TypeError):
                    pg.generate_password(length, ALL_TYPES)

    def test_length_out_of_range(self):
        for length in [7, 65, 0, -1]:
            with self.subTest(length=length):
                with self.assertRaises(ValueError):
                    pg.generate_password(length, ALL_TYPES)

    def test_character_sets_wrong_type(self):
        cases = [pg.DIGITS, tuple(ALL_TYPES), None, [5], [pg.DIGITS, None]]
        for character_sets in cases:
            with self.subTest(character_sets=character_sets):
                with self.assertRaises(TypeError):
                    pg.generate_password(16, character_sets)

    def test_character_sets_invalid_values(self):
        cases = [
            [],                              # nothing selected
            [""],                            # empty set
            [pg.DIGITS, ""],                 # empty set mixed with a valid one
            ["abc"],                         # not an approved set
            [pg.SYMBOLS + "~"],              # symbols outside the curated list
            [pg.DIGITS, pg.DIGITS],          # duplicate set
        ]
        for character_sets in cases:
            with self.subTest(character_sets=character_sets):
                with self.assertRaises(ValueError):
                    pg.generate_password(16, character_sets)


class TestInteractive(unittest.TestCase):
    """input() is replaced by a list of fake answers; output goes to a buffer."""

    def run_with_answers(self, function, answers):
        """Call function() with fake typed answers. Returns (result, output, fake_input)."""
        output = io.StringIO()
        with patch("builtins.input", side_effect=answers) as fake_input, \
                redirect_stdout(output):
            result = function()
        return result, output.getvalue(), fake_input

    def test_ask_length_retries_until_valid(self):
        result, output, fake_input = self.run_with_answers(pg.ask_length, ["abc", "5", "20"])
        self.assertEqual(result, 20)
        self.assertEqual(fake_input.call_count, 3)
        self.assertIn("whole number", output)
        self.assertIn("between 8 and 64", output)

    def test_ask_length_blank_uses_default(self):
        result, _, _ = self.run_with_answers(pg.ask_length, [""])
        self.assertEqual(result, 16)

    def test_ask_yes_no_retries_until_valid(self):
        result, output, fake_input = self.run_with_answers(
            lambda: pg.ask_yes_no("Continue?"), ["maybe", "", "YES"])
        self.assertTrue(result)
        self.assertEqual(fake_input.call_count, 3)
        self.assertEqual(output.count("Please answer y or n."), 2)
        fake_input.assert_called_with("Continue? (y/n): ")

    def test_ask_character_sets(self):
        result, _, _ = self.run_with_answers(pg.ask_character_sets, ["n", "y", "y", "n"])
        self.assertEqual(result, [pg.LOWERCASE, pg.DIGITS])

    def test_ask_character_sets_all_no_asks_again(self):
        answers = ["n", "n", "n", "n", "y", "n", "n", "n"]
        result, output, fake_input = self.run_with_answers(pg.ask_character_sets, answers)
        self.assertEqual(result, [pg.UPPERCASE])
        self.assertEqual(fake_input.call_count, 8)
        self.assertIn("Let's try again.", output)

    def test_main_generates_multiple_with_same_settings(self):
        # Length 10, digits only, then "y" for one more password, then "n" to stop.
        answers = ["10", "n", "n", "y", "n", "y", "n"]
        with patch.object(pg, "generate_password", wraps=pg.generate_password) as spy:
            _, output, _ = self.run_with_answers(pg.main, answers)

        self.assertEqual(spy.call_count, 2)
        for call in spy.call_args_list:
            self.assertEqual(call.args, (10, [pg.DIGITS]))

        passwords = [line.removeprefix("Your password: ")
                     for line in output.splitlines()
                     if line.startswith("Your password: ")]
        self.assertEqual(len(passwords), 2)
        for password in passwords:
            self.assertEqual(len(password), 10)
            self.assertTrue(password.isdigit(), "password contains non-digit characters")
        self.assertIn("Welcome", output)
        self.assertTrue(output.rstrip().endswith("Goodbye!"))

    def test_main_exits_politely_on_eof_and_ctrl_c(self):
        for error in [EOFError, KeyboardInterrupt]:
            # Stop at the first prompt, at the character questions, and at "generate another?".
            for answers_before in [[], ["12", "y"], ["12", "y", "y", "y", "y"]]:
                with self.subTest(error=error.__name__, answers_before=answers_before):
                    # No exception may escape main(); the test fails if one does.
                    _, output, _ = self.run_with_answers(pg.main, answers_before + [error])
                    self.assertTrue(output.rstrip().endswith("Goodbye!"))
                    self.assertNotIn("Traceback", output)


if __name__ == "__main__":
    unittest.main()
