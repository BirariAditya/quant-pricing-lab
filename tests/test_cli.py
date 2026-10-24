import contextlib
import io
import json
import unittest

from quant_pricing_lab.cli import main


class CommandLineTests(unittest.TestCase):
    def test_emits_valid_json_for_put(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(["--kind", "put", "--paths", "1000"]), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["option"]["kind"], "put")
        self.assertAlmostEqual(result["analytical_price"], 5.57352602225697)
        self.assertEqual(result["monte_carlo"]["independent_samples"], 500)

    def test_expiry_omits_undefined_greeks(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main(["--maturity", "0", "--spot", "120"])
        result = json.loads(output.getvalue())
        self.assertEqual(result["analytical_price"], 20)
        self.assertIsNone(result["greeks"])

    def test_invalid_input_has_actionable_exit(self):
        output = io.StringIO()
        with contextlib.redirect_stderr(output), self.assertRaises(SystemExit) as caught:
            main(["--spot", "-1"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("strictly positive", output.getvalue())


if __name__ == "__main__":
    unittest.main()
