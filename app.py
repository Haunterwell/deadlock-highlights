"""Deadlock Highlights - acha os multi-kills de um replay do Deadlock e grava cada um no OBS."""
import os
import queue
import sys
import threading
import time
import tkinter as tk
import traceback
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from dlh import game as gm
from dlh import recorder
from dlh import theme
from dlh.analyze import find_highlights
from dlh.theme import PALETTE

APP_NAME = "Deadlock Highlights"
VERSION = "1.0.1"
OK, BAD, WAIT = "✔", "✖", "…"
GREEN, RED, GRAY = PALETTE["muted"], PALETTE["error"], PALETTE["muted"]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} {VERSION}")
        self.geometry("1040x720")
        self.minsize(900, 620)
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        try:
            self.iconbitmap(default=str(base / "assets" / "icon.ico"))
        except tk.TclError:
            pass
        self.cfg = gm.load_config()
        if not self.cfg.get("game_dir"):
            d = gm.find_game_dir()
            self.cfg["game_dir"] = str(d) if d else ""
        self.q = queue.Queue()
        self.analysis = None
        self.stop = threading.Event()
        self.busy = False

        theme.apply(self)
        theme.dark_titlebar(self)

        top = ttk.Frame(self, padding=(12, 10, 12, 0))
        top.pack(fill="x")
        ttk.Label(top, text=APP_NAME, style="Title.TLabel").pack(side="left")
        ttk.Label(top, text="multi-kills do replay  →  clipes no OBS", style="Sub.TLabel").pack(side="left", padx=12)

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=12, pady=8)
        self._build_setup(ttk.Frame(self.nb, padding=12))
        self._build_highlights(ttk.Frame(self.nb, padding=12))

        logf = ttk.LabelFrame(self, text="Mensagens", padding=6)
        logf.pack(fill="x", padx=12, pady=(0, 10))
        self.logbox = tk.Text(logf, height=4, wrap="word", font=("Consolas", 9), state="disabled",
                              background=PALETTE["card"], foreground=PALETTE["muted"],
                              insertbackground=PALETTE["text"], relief="flat", highlightthickness=0)
        self.logbox.pack(fill="x")

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._pump)
        self.after(300, self.check_all)
        self.after(400, self.refresh_replays)

    # ================================================================ util
    def log(self, msg):
        self.q.put(lambda: self._log(msg))

    def _log(self, msg):
        self.logbox.configure(state="normal")
        self.logbox.insert("end", f"{datetime.now():%H:%M:%S}  {msg}\n")
        self.logbox.see("end")
        self.logbox.configure(state="disabled")

    def _pump(self):
        try:
            while True:
                self.q.get_nowait()()
        except queue.Empty:
            pass
        self.after(100, self._pump)

    def run_bg(self, fn, done=None):
        def work():
            try:
                r = fn()
                if done:
                    self.q.put(lambda: done(r))
            except Exception as e:
                tb = traceback.format_exc()
                msg = f"Erro: {e}"
                self.q.put(lambda: self._log(msg))
                self.q.put(lambda: print(tb))
                if done:
                    self.q.put(lambda: done(None))
        threading.Thread(target=work, daemon=True).start()

    def game(self):
        ok, key = gm.Game(self.cfg["game_dir"]).bind_ok() if self.cfg.get("game_dir") else (False, None)
        return gm.Game(self.cfg["game_dir"], key or self.cfg.get("key", gm.DEFAULT_KEY))

    def save(self):
        self.cfg["obs_host"] = self.v_host.get().strip() or "127.0.0.1"
        try:
            self.cfg["obs_port"] = int(self.v_port.get())
        except ValueError:
            self.cfg["obs_port"] = 4455
        self.cfg["obs_password"] = self.v_pass.get()
        self.cfg["obs_scene"] = self.v_scene.get().strip() or "Deadlock Highlights"
        for k, v in (("window_s", self.v_window), ("min_kills", self.v_min), ("min_assists", self.v_assists),
                     ("before_s", self.v_before), ("after_s", self.v_after)):
            try:
                val = float(v.get())
                self.cfg[k] = max(0, int(val)) if k in ("min_kills", "min_assists") else val
            except ValueError:
                pass
        if self.cfg["min_kills"] + self.cfg["min_assists"] < 1:
            self.cfg["min_kills"] = 1
            self.v_min.set("1")
        gm.save_config(self.cfg)

    def _on_close(self):
        self.stop.set()
        try:
            self.save()
        finally:
            self.destroy()

    # ================================================================ aba 1: preparar
    def _status(self, parent, row):
        lbl = tk.Label(parent, text=WAIT, fg=GRAY, bg=PALETTE["bg"],
                       font=("Segoe UI Symbol", 13, "bold"), width=2)
        lbl.grid(row=row, column=0, sticky="nw", padx=(0, 8), pady=6)
        return lbl

    def _set(self, lbl, ok, detail_lbl=None, detail=""):
        lbl.configure(text=OK if ok else BAD, fg=GREEN if ok else RED)
        if detail_lbl is not None:
            detail_lbl.configure(text=detail)

    def _build_setup(self, f):
        self.nb.add(f, text="  1. Preparar  ")
        f.columnconfigure(1, weight=1)
        r = 0
        ttk.Label(f, text="Faça isto uma vez. Quando tudo estiver com ✔, vá para a aba 2.",
                  style="Muted.TLabel").grid(row=r, column=0, columnspan=3, sticky="w", pady=(0, 6))

        # --- pasta do jogo
        r += 1
        self.s_dir = self._status(f, r)
        box = ttk.Frame(f)
        box.grid(row=r, column=1, sticky="ew", pady=6)
        ttk.Label(box, text="Pasta do Deadlock", style="Step.TLabel").pack(anchor="w")
        self.v_dir = tk.StringVar(value=self.cfg.get("game_dir", ""))
        row = ttk.Frame(box)
        row.pack(fill="x")
        ttk.Entry(row, textvariable=self.v_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Procurar…", command=self.pick_dir).pack(side="left", padx=4)
        ttk.Button(row, text="Achar sozinho", command=self.auto_dir).pack(side="left")
        ttk.Label(box, text=r"É a pasta ...\steamapps\common\Deadlock\game\citadel", style="Muted.TLabel").pack(anchor="w")

        # --- jogo aberto com -condebug
        r += 1
        self.s_run = self._status(f, r)
        box = ttk.Frame(f)
        box.grid(row=r, column=1, sticky="ew", pady=6)
        ttk.Label(box, text="Deadlock aberto com a opção -condebug", style="Step.TLabel").pack(anchor="w")
        self.d_run = ttk.Label(box, text="", style="Muted.TLabel", wraplength=640, justify="left")
        self.d_run.pack(anchor="w")
        ttk.Button(f, text="Abrir o Deadlock com -condebug", command=self.launch_game).grid(row=r, column=2, sticky="ne", pady=6)

        # --- bind
        r += 1
        self.s_bind = self._status(f, r)
        box = ttk.Frame(f)
        box.grid(row=r, column=1, sticky="ew", pady=6)
        ttk.Label(box, text="Tecla de comando no jogo", style="Step.TLabel").pack(anchor="w")
        self.d_bind = ttk.Label(box, text="", style="Muted.TLabel", wraplength=640, justify="left")
        self.d_bind.pack(anchor="w")
        ttk.Button(f, text="Copiar o comando", command=self.copy_bind).grid(row=r, column=2, sticky="ne", pady=6)

        # --- OBS
        r += 1
        self.s_obs = self._status(f, r)
        box = ttk.Frame(f)
        box.grid(row=r, column=1, sticky="ew", pady=6)
        ttk.Label(box, text="OBS Studio (WebSocket)", style="Step.TLabel").pack(anchor="w")
        row = ttk.Frame(box)
        row.pack(fill="x", pady=2)
        self.v_host = tk.StringVar(value=self.cfg["obs_host"])
        self.v_port = tk.StringVar(value=str(self.cfg["obs_port"]))
        self.v_pass = tk.StringVar(value=self.cfg.get("obs_password", ""))
        ttk.Label(row, text="Endereço").pack(side="left")
        ttk.Entry(row, textvariable=self.v_host, width=16).pack(side="left", padx=(4, 10))
        ttk.Label(row, text="Porta").pack(side="left")
        ttk.Entry(row, textvariable=self.v_port, width=7).pack(side="left", padx=(4, 10))
        ttk.Label(row, text="Senha").pack(side="left")
        ttk.Entry(row, textvariable=self.v_pass, width=22, show="•").pack(side="left", padx=4)
        self.d_obs = ttk.Label(box, text="No OBS: Ferramentas → Configurações do servidor WebSocket → "
                                         "Mostrar informações de conexão.", style="Muted.TLabel", wraplength=640)
        self.d_obs.pack(anchor="w")
        ttk.Button(f, text="Testar conexão", command=self.check_obs).grid(row=r, column=2, sticky="ne", pady=6)

        # --- cena
        r += 1
        self.s_scene = self._status(f, r)
        box = ttk.Frame(f)
        box.grid(row=r, column=1, sticky="ew", pady=6)
        ttk.Label(box, text="Cena do OBS com a captura do Deadlock", style="Step.TLabel").pack(anchor="w")
        row = ttk.Frame(box)
        row.pack(fill="x", pady=2)
        self.v_scene = tk.StringVar(value=self.cfg.get("obs_scene", "Deadlock Highlights"))
        ttk.Label(row, text="Nome da cena").pack(side="left")
        ttk.Entry(row, textvariable=self.v_scene, width=28).pack(side="left", padx=4)
        self.d_scene = ttk.Label(box, text="O app troca para esta cena só enquanto grava e depois volta.",
                                 style="Muted.TLabel", wraplength=640)
        self.d_scene.pack(anchor="w")
        ttk.Button(f, text="Criar / conferir cena", command=self.make_scene).grid(row=r, column=2, sticky="ne", pady=6)

        r += 1
        ttk.Separator(f).grid(row=r, column=0, columnspan=3, sticky="ew", pady=10)
        r += 1
        ttk.Button(f, text="Verificar tudo de novo", style="Gold.TButton",
                   command=self.check_all).grid(row=r, column=0, columnspan=3, sticky="w")

    def pick_dir(self):
        d = filedialog.askdirectory(title="Escolha a pasta game\\citadel do Deadlock")
        if d:
            self.v_dir.set(d)
            self.check_all()

    def auto_dir(self):
        d = gm.find_game_dir()
        if d:
            self.v_dir.set(str(d))
            self.log(f"Deadlock encontrado em {d}")
        else:
            self.log("Não achei o Deadlock nas bibliotecas da Steam. Use Procurar…")
        self.check_all()

    def launch_game(self):
        self.cfg["game_dir"] = self.v_dir.get().strip()
        cmd = self.game().process_cmdline()
        if cmd:
            messagebox.showinfo(APP_NAME, "O Deadlock já está aberto.\n\nPara usar a opção -condebug, feche o jogo "
                                          "e clique neste botão de novo (ou coloque -condebug nas Opções de "
                                          "inicialização do Deadlock na Steam).")
            return
        self.game().launch_with_demo(None)
        self.log("Pedi para a Steam abrir o Deadlock com -condebug. Se a Steam perguntar sobre os parâmetros, confirme.")
        self.after(20000, self.check_all)

    def copy_bind(self):
        self.clipboard_clear()
        self.clipboard_append(self.game().bind_command())
        self.log(f"Copiado: {self.game().bind_command()}  → no jogo, abra o console (F7), cole com Ctrl+V e aperte Enter.")

    def check_all(self):
        self.cfg["game_dir"] = self.v_dir.get().strip()
        self.save()
        for s in (self.s_dir, self.s_run, self.s_bind):
            s.configure(text=WAIT, fg=GRAY)
        g = gm.Game(self.cfg["game_dir"]) if self.cfg["game_dir"] else None
        ok_dir = bool(g) and (g.dir / "gameinfo.gi").exists()
        self._set(self.s_dir, ok_dir)

        def work():
            if not ok_dir:
                return None, (False, None)
            return g.process_cmdline(), g.bind_ok()

        def done(res):
            if res is None:
                return
            cmd, (bind, key) = res
            if not ok_dir:
                self._set(self.s_run, False, self.d_run, "Escolha primeiro a pasta do Deadlock.")
                self._set(self.s_bind, False, self.d_bind, "")
                return
            if not cmd:
                self._set(self.s_run, False, self.d_run,
                          "O Deadlock está fechado. Clique em \"Abrir o Deadlock com -condebug\".")
            elif "-condebug" not in cmd.lower():
                self._set(self.s_run, False, self.d_run,
                          "O jogo está aberto, mas sem -condebug. Feche o jogo e abra pelo botão ao lado, ou "
                          "coloque -condebug nas Opções de inicialização do Deadlock na Steam.")
            else:
                self._set(self.s_run, True, self.d_run, "Tudo certo: o jogo está gravando o console.log.")
            if bind:
                self.cfg["key"] = key
                self._set(self.s_bind, True, self.d_bind, f"A tecla {key} executa os comandos do app.")
            else:
                self._set(self.s_bind, False, self.d_bind,
                          f"Com o jogo aberto, aperte F7 para abrir o console, cole o comando "
                          f"{gm.Game(self.cfg['game_dir']).bind_command()} e aperte Enter "
                          f"(o botão ao lado copia). Depois clique em Verificar tudo.")
            self.save()

        self.run_bg(work, done)
        self.check_obs(quiet=True)

    def check_obs(self, quiet=False):
        self.save()
        self.s_obs.configure(text=WAIT, fg=GRAY)
        self.s_scene.configure(text=WAIT, fg=GRAY)
        cfg = dict(self.cfg)

        def work():
            obs = recorder.connect_obs(cfg)
            try:
                v = obs.call("GetVersion")
                scenes = [s["sceneName"] for s in obs.call("GetSceneList")["scenes"]]
                has_capture = False
                if cfg["obs_scene"] in scenes:
                    items = obs.call("GetSceneItemList", {"sceneName": cfg["obs_scene"]})["sceneItems"]
                    has_capture = any(i.get("inputKind") in ("game_capture", "window_capture", "monitor_capture")
                                      or "deadlock" in i["sourceName"].lower() for i in items)
                rec_dir = obs.call("GetRecordDirectory").get("recordDirectory", "")
                return v, has_capture, rec_dir
            finally:
                obs.close()

        def done(res):
            if not res:
                self._set(self.s_obs, False, self.d_obs,
                          "Não conectou. Confira se o OBS está aberto, o servidor WebSocket ligado, "
                          "e o endereço, a porta e a senha (Ferramentas → Configurações do servidor WebSocket).")
                self._set(self.s_scene, False)
                return
            v, has_capture, rec_dir = res
            self.rec_dir = rec_dir
            self._set(self.s_obs, True, self.d_obs,
                      f"Conectado ao OBS {v.get('obsVersion')}. Os vídeos vão para: {rec_dir}")
            self._set(self.s_scene, has_capture, self.d_scene,
                      "Cena pronta." if has_capture else
                      "A cena não existe ou não tem a captura do Deadlock. Clique em \"Criar / conferir cena\".")
            if not quiet:
                self.log("OBS conectado.")

        self.run_bg(work, done)

    def make_scene(self):
        self.save()
        cfg = dict(self.cfg)

        def work():
            obs = recorder.connect_obs(cfg)
            try:
                return recorder.ensure_scene(obs, cfg["obs_scene"])
            finally:
                obs.close()

        def done(created):
            if created is None:
                return
            self.log(f"Cena '{cfg['obs_scene']}' " + ("criada com a captura do Deadlock." if created else "já estava pronta."))
            self.check_obs(quiet=True)

        self.run_bg(work, done)

    # ================================================================ aba 2: destaques
    def _build_highlights(self, f):
        self.nb.add(f, text="  2. Destaques e gravação  ")
        f.columnconfigure(0, weight=1)
        f.rowconfigure(3, weight=1)

        # replays
        top = ttk.LabelFrame(f, text="Replay (baixe a partida no Deadlock: Perfil → Histórico → Baixar replay)", padding=8)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1)
        self.v_replay = tk.StringVar()
        self.cb_replay = ttk.Combobox(top, textvariable=self.v_replay, state="readonly")
        self.cb_replay.grid(row=0, column=0, sticky="ew")
        ttk.Button(top, text="Atualizar lista", command=self.refresh_replays).grid(row=0, column=1, padx=4)
        ttk.Button(top, text="Outro arquivo…", command=self.pick_replay).grid(row=0, column=2)
        ttk.Button(top, text="Abrir pasta", command=self.open_replays).grid(row=0, column=3, padx=(4, 0))

        # opcoes
        opt = ttk.Frame(f, padding=(0, 8))
        opt.grid(row=1, column=0, sticky="ew")
        self.v_min = tk.StringVar(value=str(self.cfg["min_kills"]))
        self.v_window = tk.StringVar(value=str(self.cfg["window_s"]))
        self.v_before = tk.StringVar(value=str(self.cfg["before_s"]))
        self.v_after = tk.StringVar(value=str(self.cfg["after_s"]))
        self.v_assists = tk.StringVar(value=str(self.cfg.get("min_assists", 0)))
        for txt, var, lo, hi in (("Abates", self.v_min, 0, 8), ("+ Assistências", self.v_assists, 0, 8),
                                 ("em até (s)", self.v_window, 5, 60),
                                 ("Gravar antes (s)", self.v_before, 2, 30), ("Gravar depois (s)", self.v_after, 1, 30)):
            ttk.Label(opt, text=txt).pack(side="left")
            ttk.Spinbox(opt, from_=lo, to=hi, textvariable=var, width=4).pack(side="left", padx=(4, 12))
        self.b_analyze = ttk.Button(opt, text="Achar destaques", style="Gold.TButton", command=self.analyze)
        self.b_analyze.pack(side="right")

        self.l_summary = ttk.Label(f, text="Escolha um replay e clique em Achar destaques.", style="Muted.TLabel")
        self.l_summary.grid(row=2, column=0, sticky="w")

        # tabela
        tf = ttk.Frame(f)
        tf.grid(row=3, column=0, sticky="nsew", pady=4)
        tf.columnconfigure(0, weight=1)
        tf.rowconfigure(0, weight=1)
        cols = ("n", "clock", "player", "hero", "kills", "assists", "span", "victims")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", selectmode="extended")
        for c, t, w, a in (("n", "#", 40, "center"), ("clock", "Tempo", 70, "center"), ("player", "Jogador", 170, "w"),
                           ("hero", "Herói", 110, "w"), ("kills", "Abates", 60, "center"),
                           ("assists", "Assist.", 60, "center"),
                           ("span", "Em (s)", 60, "center"), ("victims", "Vítimas", 360, "w")):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor=a, stretch=(c == "victims"))
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)

        # gravacao
        rec = ttk.LabelFrame(f, text="Gravar (selecione as linhas; Ctrl/Shift para várias)", padding=8)
        rec.grid(row=4, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(rec, text="Selecionar todos", command=lambda: self.tree.selection_set(self.tree.get_children())).pack(side="left")
        ttk.Button(rec, text="Abrir este replay no jogo", command=self.open_demo).pack(side="left", padx=6)
        self.b_rec = ttk.Button(rec, text="●  Gravar selecionados", style="Gold.TButton", command=self.record)
        self.b_rec.pack(side="left", padx=6)
        self.b_stop = ttk.Button(rec, text="Parar", command=self.stop_rec, state="disabled")
        self.b_stop.pack(side="left")
        ttk.Button(rec, text="Abrir pasta dos vídeos", command=self.open_videos).pack(side="right")
        self.pb = ttk.Progressbar(rec, length=160, mode="determinate")
        self.pb.pack(side="right", padx=8)

    def refresh_replays(self):
        self.cfg["game_dir"] = self.v_dir.get().strip()
        reps = self.game().replays() if self.cfg["game_dir"] else []
        self.replay_paths = {}
        labels = []
        for p in reps:
            st = p.stat()
            lab = f"{p.stem}   —   {datetime.fromtimestamp(st.st_mtime):%d/%m/%Y %H:%M}   —   {st.st_size / 1e6:.0f} MB"
            self.replay_paths[lab] = p
            labels.append(lab)
        if getattr(self, "extra_replay", None):
            lab = f"{self.extra_replay.name}   —   (escolhido)"
            self.replay_paths[lab] = self.extra_replay
            labels.insert(0, lab)
        self.cb_replay["values"] = labels
        if labels and self.v_replay.get() not in labels:
            self.v_replay.set(labels[0])
        if not labels:
            self.v_replay.set("")
            self.l_summary.configure(text="Nenhum replay baixado. No Deadlock: Perfil → Histórico de partidas → "
                                          "escolha a partida → Baixar replay. Depois clique em Atualizar lista.")

    def pick_replay(self):
        p = filedialog.askopenfilename(title="Escolha um replay do Deadlock", filetypes=[("Replay do Deadlock", "*.dem")])
        if p:
            self.extra_replay = Path(p)
            self.refresh_replays()
            self.v_replay.set(self.cb_replay["values"][0])

    def open_replays(self):
        d = self.game().replays_dir
        if d.exists():
            os.startfile(d)

    def open_videos(self):
        d = getattr(self, "rec_dir", "") or str(Path.home() / "Videos")
        if Path(d).exists():
            os.startfile(d)

    def current_replay(self):
        return self.replay_paths.get(self.v_replay.get()) if hasattr(self, "replay_paths") else None

    def analyze(self):
        p = self.current_replay()
        if not p:
            messagebox.showwarning(APP_NAME, "Escolha um replay primeiro.")
            return
        self.save()
        cfg = dict(self.cfg)
        self.b_analyze.configure(state="disabled")
        self.l_summary.configure(text=f"Lendo {p.name}… (leva uns 15 segundos)")
        self.log(f"Analisando {p.name}…")
        t0 = time.time()

        def work():
            return find_highlights(p, cfg["window_s"], cfg["min_kills"], cfg["before_s"],
                                   cfg.get("min_assists", 0))

        def done(res):
            self.b_analyze.configure(state="normal")
            if not res:
                self.l_summary.configure(text="Não consegui ler este replay. Veja as mensagens abaixo.")
                return
            self.analysis = res
            self.tree.delete(*self.tree.get_children())
            for i, h in enumerate(res["highlights"]):
                self.tree.insert("", "end", iid=str(i), values=(
                    i + 1, h["clock"], h["player"], h["hero"], h["kills"], h.get("assists", 0),
                    h["span_s"], ", ".join(h["victims"])))
            self.tree.selection_set(self.tree.get_children())
            what = f"{cfg['min_kills']}+ abates"
            if cfg.get("min_assists", 0):
                what += f" e {cfg['min_assists']}+ assistências"
            msg = (f"Partida {res['match']}: {res['total_kills']} abates, {len(res['highlights'])} destaques "
                   f"({what} em até {cfg['window_s']:g} s). Lido em {time.time() - t0:.0f} s.")
            self.l_summary.configure(text=msg)
            self.log(msg)

        self.run_bg(work, done)

    def open_demo(self):
        p = self.current_replay()
        if not p:
            messagebox.showwarning(APP_NAME, "Escolha um replay primeiro.")
            return
        g = self.game()
        try:
            rel = p.resolve().relative_to(g.dir.resolve()).with_suffix("")
            arg = rel.as_posix()
        except ValueError:
            messagebox.showwarning(APP_NAME, "O replay precisa estar dentro da pasta do jogo "
                                             f"({g.replays_dir}) para o Deadlock conseguir abrir.")
            return
        cmd = f"playdemo {arg}"
        if g.process_cmdline():
            self.clipboard_clear()
            self.clipboard_append(cmd)
            messagebox.showinfo(APP_NAME, f"Comando copiado:\n\n{cmd}\n\nNo Deadlock, aperte F7 (console), cole com "
                                          "Ctrl+V e aperte Enter. Quando a partida carregar, FECHE o console (F7) e "
                                          "volte aqui para gravar.")
        else:
            os.startfile(f"steam://run/{gm.APP_ID}//-condebug +{cmd}/")
            self.log("Abrindo o Deadlock já com o replay. Se a Steam perguntar sobre os parâmetros, confirme.")

    def record(self):
        if self.busy:
            return
        if not self.analysis:
            messagebox.showwarning(APP_NAME, "Clique em Achar destaques primeiro.")
            return
        chosen = sorted(int(i) for i in self.tree.selection())
        if not chosen:
            messagebox.showwarning(APP_NAME, "Selecione pelo menos um destaque na lista.")
            return
        self.save()
        g = self.game()
        if not messagebox.askokcancel(
                APP_NAME, f"Vou gravar {len(chosen)} destaque(s).\n\nAntes de continuar:\n"
                          "• o replay desta partida está aberto no Deadlock;\n• o console do jogo está FECHADO;\n"
                          "• o OBS está aberto.\n\nDurante a gravação não use o mouse nem o teclado: o app "
                          f"aperta a tecla {g.key} no jogo."):
            return
        self.busy = True
        self.stop.clear()
        self.b_rec.configure(state="disabled")
        self.b_stop.configure(state="normal")
        self.pb.configure(maximum=len(chosen), value=0)
        cfg, analysis = dict(self.cfg), self.analysis

        def progress(i, n):
            self.q.put(lambda: self.pb.configure(value=i))

        def work():
            return recorder.record(g, cfg, analysis, chosen, self.log, self.stop, progress)

        def done(saved):
            self.busy = False
            self.b_rec.configure(state="normal")
            self.b_stop.configure(state="disabled")
            n = len(saved or [])
            self.log(f"Fim: {n} clipe(s) gravado(s).")
            if n:
                self.lift()
                if messagebox.askyesno(APP_NAME, f"{n} clipe(s) gravado(s). Abrir a pasta dos vídeos?"):
                    self.open_videos()

        self.run_bg(work, done)

    def stop_rec(self):
        self.stop.set()
        self.log("Parando depois do clipe atual…")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--analisar":
        # modo de diagnostico sem janela: DeadlockHighlights.exe --analisar <replay.dem> <saida.json>
        import json
        try:
            Path(sys.argv[3]).write_text(json.dumps(find_highlights(sys.argv[2]), ensure_ascii=False, indent=2),
                                         encoding="utf-8")
        except Exception:
            Path(sys.argv[3]).write_text(json.dumps({"erro": traceback.format_exc()}), encoding="utf-8")
            sys.exit(1)
        sys.exit(0)
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    App().mainloop()
