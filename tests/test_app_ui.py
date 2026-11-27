import contextlib
import io
import time
import unittest

import app as app_module


class AppUiTests(unittest.TestCase):
    def setUp(self):
        self.app = app_module.App()
        self.app.withdraw()

    def tearDown(self):
        self.app.destroy()

    def test_window_uses_theme(self):
        a = self.app
        self.assertEqual(a.cget("bg"), "#081B1B")
        self.assertEqual(a.logbox.cget("background"), "#203B37")
        self.assertEqual(int(a.logbox.cget("height")), 4)
        self.assertEqual(str(a.b_analyze.cget("style")), "Gold.TButton")
        self.assertEqual(str(a.b_rec.cget("style")), "Gold.TButton")

    def test_status_colors(self):
        a = self.app
        a._set(a.s_dir, True)
        self.assertEqual(str(a.s_dir.cget("fg")), "#96CDB0")
        a._set(a.s_dir, False)
        self.assertEqual(str(a.s_dir.cget("fg")), "#ef8a74")
        self.assertEqual(str(a.s_dir.cget("bg")), "#081B1B")

    def test_run_bg_logs_error(self):
        a = self.app
        with contextlib.redirect_stdout(io.StringIO()):  # run_bg imprime o traceback
            a.run_bg(lambda: 1 / 0)
            deadline = time.time() + 2
            while time.time() < deadline:
                a.update()
                if "Erro: division by zero" in a.logbox.get("1.0", "end"):
                    break
                time.sleep(0.05)
            a.update()
        self.assertIn("Erro: division by zero", a.logbox.get("1.0", "end"))


if __name__ == "__main__":
    unittest.main()
