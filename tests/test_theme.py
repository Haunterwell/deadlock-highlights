import tkinter as tk
import unittest
from tkinter import ttk

from dlh import theme
from dlh.theme import PALETTE, SELECT_BG, apply


class ThemeTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_palette_values(self):
        self.assertEqual(PALETTE["bg"], "#081B1B")
        self.assertEqual(PALETTE["gold"], "#C18D52")
        self.assertEqual(PALETTE["text"], "#EEE8B2")
        self.assertEqual(PALETTE["muted"], "#96CDB0")

    def test_apply_configures_styles(self):
        style = apply(self.root)
        self.assertEqual(style.theme_use(), "clam")
        self.assertEqual(style.lookup("TFrame", "background"), "#081B1B")
        self.assertEqual(style.lookup("Gold.TButton", "background"), "#C18D52")
        self.assertEqual(style.lookup("Gold.TButton", "foreground"), "#081B1B")
        self.assertEqual(style.lookup("Treeview", "fieldbackground"), "#203B37")
        self.assertEqual(self.root.cget("bg"), "#081B1B")

    def test_disabled_button_not_gold(self):
        style = apply(self.root)
        self.assertNotEqual(
            style.lookup("Gold.TButton", "background", ["disabled"]), "#C18D52")

    def test_disabled_button_text_dimmed(self):
        style = apply(self.root)
        self.assertEqual(
            style.lookup("TButton", "foreground", ["disabled"]), PALETTE["line"])

    def test_plain_button_gold_outline(self):
        style = apply(self.root)
        self.assertEqual(style.lookup("TButton", "bordercolor"), PALETTE["gold"])
        self.assertEqual(
            style.lookup("TButton", "bordercolor", ["disabled"]), PALETTE["line"])

    def test_selection_is_darkened_gold(self):
        style = apply(self.root)
        self.assertEqual(SELECT_BG, "#8a6438")
        self.assertEqual(
            style.lookup("Treeview", "background", ["selected"]), "#8a6438")
        self.assertEqual(
            style.lookup("Treeview", "foreground", ["selected"]), PALETTE["text"])

    def test_combobox_popup_dark(self):
        apply(self.root)
        cb = ttk.Combobox(self.root)
        pd = self.root.tk.eval(f"ttk::combobox::PopdownWindow {cb}")
        bg = self.root.tk.call(pd + ".f.l", "cget", "-background")
        self.assertEqual(str(bg), "#203B37")

    def test_dark_titlebar_does_not_raise(self):
        theme.dark_titlebar(self.root)


if __name__ == "__main__":
    unittest.main()
