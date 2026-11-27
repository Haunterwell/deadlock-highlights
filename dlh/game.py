"""Tudo que fala com o Deadlock: achar a pasta do jogo, ler o console.log, mandar comandos pela tecla."""
import ctypes
import json
import os
import re
import subprocess
import time
import winreg
from ctypes import wintypes
from pathlib import Path

APP_ID = "1422450"
WINDOW_TITLE = "deadlock"
CMD_FILE = "dlh_cmd"          # cfg/dlh_cmd.cfg
DEFAULT_KEY = "F10"
SCANCODES = {"F6": 0x40, "F8": 0x42, "F9": 0x43, "F10": 0x44, "F11": 0x57, "F12": 0x58}
CREATE_NO_WINDOW = 0x08000000


# ---------------------------------------------------------------- pastas

def steam_dir():
    for hive, key in ((winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
                      (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")):
        try:
            with winreg.OpenKey(hive, key) as k:
                for name in ("SteamPath", "InstallPath"):
                    try:
                        p = Path(winreg.QueryValueEx(k, name)[0])
                        if p.exists():
                            return p
                    except OSError:
                        pass
        except OSError:
            pass
    p = Path(r"C:\Program Files (x86)\Steam")
    return p if p.exists() else None


def find_game_dir():
    """Pasta game/citadel do Deadlock, procurando em todas as bibliotecas da Steam."""
    s = steam_dir()
    libs = [s] if s else []
    if s:
        vdf = s / "steamapps" / "libraryfolders.vdf"
        if vdf.exists():
            for m in re.finditer(r'"path"\s+"([^"]+)"', vdf.read_text(encoding="utf-8", errors="replace")):
                libs.append(Path(m.group(1).replace("\\\\", "\\")))
    for lib in libs:
        acf = lib / "steamapps" / f"appmanifest_{APP_ID}.acf"
        if acf.exists():
            m = re.search(r'"installdir"\s+"([^"]+)"', acf.read_text(encoding="utf-8", errors="replace"))
            folder = m.group(1) if m else "Deadlock"
            g = lib / "steamapps" / "common" / folder / "game" / "citadel"
            if g.exists():
                return g
    return None


class Game:
    def __init__(self, citadel_dir, key=DEFAULT_KEY):
        self.dir = Path(citadel_dir)
        self.key = key

    @property
    def log(self):
        return self.dir / "console.log"

    @property
    def replays_dir(self):
        return self.dir / "replays"

    @property
    def cmd_cfg(self):
        return self.dir / "cfg" / f"{CMD_FILE}.cfg"

    def replays(self):
        if not self.replays_dir.exists():
            return []
        return sorted(self.replays_dir.glob("*.dem"), key=lambda p: p.stat().st_mtime, reverse=True)

    # ------------------------------------------------------------ checagens
    def process_cmdline(self):
        """Linha de comando do deadlock.exe aberto, ou None se o jogo esta fechado."""
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_Process -Filter \"Name='deadlock.exe'\").CommandLine"],
                capture_output=True, text=True, timeout=15, creationflags=CREATE_NO_WINDOW).stdout.strip()
        except Exception:
            return None
        return out or None

    def bind_ok(self):
        """True se alguma tecla do jogo esta ligada a 'exec dlh_cmd'; devolve tambem a tecla."""
        files = list((self.dir / "cfg").glob("user_keys_*.vcfg"))
        s = steam_dir()
        if s:
            files += list((s / "userdata").glob(f"*/{APP_ID}/remote/user_keys.vcfg"))
            files += list((s / "userdata").glob(f"*/{APP_ID}/local/cfg/user_keys_*.vcfg"))
        for f in files:
            try:
                m = re.search(rf'"(\w+)"\s+"exec {CMD_FILE}"', f.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
            if m:
                return True, m.group(1).upper()
        return False, None

    def bind_command(self):
        return f'bind {self.key} "exec {CMD_FILE}"'

    # ------------------------------------------------------------ log
    def log_pos(self):
        return self.log.stat().st_size if self.log.exists() else 0

    def log_since(self, pos):
        if not self.log.exists():
            return ""
        with self.log.open("rb") as f:
            f.seek(pos)
            return f.read().decode("utf-8", "replace")

    def wait_log(self, pos, pattern, timeout, stop=None):
        end = time.time() + timeout
        while time.time() < end:
            if stop and stop.is_set():
                return False
            if re.search(pattern, self.log_since(pos)):
                return True
            time.sleep(0.2)
        return False

    # ------------------------------------------------------------ comandos
    def send(self, *cmds):
        self.cmd_cfg.parent.mkdir(parents=True, exist_ok=True)
        self.cmd_cfg.write_text("\n".join(cmds) + "\n", encoding="utf-8")
        press_key(self.key)

    def send_checked(self, *cmds, timeout=4):
        """Manda e confirma pelo log que o jogo executou o arquivo."""
        pos = self.log_pos()
        self.send(*cmds)
        return self.wait_log(pos, rf"execing {CMD_FILE}", timeout)

    def launch_with_demo(self, demo_name=None):
        args = "-condebug"
        if demo_name:
            args += f" +playdemo replays/{demo_name}"
        os.startfile(f"steam://run/{APP_ID}//{args}/")


# ---------------------------------------------------------------- teclado

_u = ctypes.windll.user32


class _KI(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class _INP(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("ki", _KI), ("pad", ctypes.c_byte * 8)]


def find_window():
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def cb(h, _):
        n = ctypes.create_unicode_buffer(256)
        _u.GetWindowTextW(h, n, 256)
        if _u.IsWindowVisible(h) and n.value.strip().lower() == WINDOW_TITLE:
            found.append(h)
        return True

    _u.EnumWindows(cb, 0)
    return found[0] if found else None


def press_key(key):
    h = find_window()
    if not h:
        raise RuntimeError("Janela do Deadlock nao encontrada. O jogo esta aberto?")
    if _u.GetForegroundWindow() != h:
        _u.ShowWindow(h, 9)
        # truque padrao para o Windows deixar trocar a janela da frente
        _u.keybd_event(0x12, 0, 0, 0)
        _u.SetForegroundWindow(h)
        _u.keybd_event(0x12, 0, 2, 0)
        time.sleep(0.4)
    sc = SCANCODES[key]

    def send(flags):
        i = _INP(1, _KI(0, sc, flags, 0, 0))
        _u.SendInput(1, ctypes.byref(i), ctypes.sizeof(_INP))

    send(0x0008)
    time.sleep(0.05)
    send(0x0008 | 0x0002)


# ---------------------------------------------------------------- configuracao do app

CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "DeadlockHighlights"
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULTS = {
    "game_dir": "",
    "key": DEFAULT_KEY,
    "obs_host": "127.0.0.1",
    "obs_port": 4455,
    "obs_password": "",
    "obs_scene": "Deadlock Highlights",
    "window_s": 20,
    "min_kills": 2,
    "min_assists": 0,
    "before_s": 8,
    "after_s": 4,
}


def load_config():
    cfg = dict(DEFAULTS)
    try:
        cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
