import contextlib
import io
import queue
import unittest
from unittest import mock

import app as app_module
from dlh import game as gm


class AppUiTests(unittest.TestCase):
    def setUp(self):
        # sem efeitos colaterais: nada de OBS, jogo ou escrita da config real
        for target, name in ((app_module.App, "check_all"), (app_module.App, "refresh_replays"),
                             (gm, "save_config")):
            p = mock.patch.object(target, name)
            p.start()
            self.addCleanup(p.stop)
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

    def test_log_frame_packed_at_bottom_before_notebook(self):
        a = self.app
        self.assertEqual(a.logf.pack_info()["side"], "bottom")
        slaves = a.pack_slaves()
        self.assertLess(slaves.index(a.logf), slaves.index(a.nb))

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
            # o worker enfileira 2 itens (log e print); drena sem depender do relogio/after
            for _ in range(2):
                try:
                    a.q.get(timeout=10)()
                except queue.Empty:
                    self.fail("o worker nao enfileirou o erro")
        self.assertIn("Erro: division by zero", a.logbox.get("1.0", "end"))


if __name__ == "__main__":
    unittest.main()
