# Tema Deadlock Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deixar a janela Tkinter do app com o tema Deadlock (verde-escuro e dourado) e corrigir o bug do `run_bg`.

**Architecture:** Um módulo novo `dlh/theme.py` concentra a paleta e configura o tema `clam` do ttk; `app.py` passa a chamar `theme.apply(self)` e usa as cores do módulo nos widgets `tk` puros (status ✔/✖, caixa de mensagens).

**Tech Stack:** Python 3.13, Tkinter/ttk (tema `clam`), `unittest` da biblioteca padrão.

**Spec:** `docs/superpowers/specs/2026-11-27-tema-deadlock-design.md`

## Global Constraints

- Paleta exata: fundo `#081B1B`, cartão `#203B37`, borda `#2f524c`, texto `#EEE8B2`, rótulo `#96CDB0`, dourado `#C18D52`, dourado hover `#d6a873`, texto sobre dourado `#081B1B`, erro `#ef8a74`.
- Fonte: Segoe UI / Segoe UI Semibold. Nenhuma fonte embutida, nenhuma arte da Valve, nenhuma imagem de fundo.
- Sem dependências novas; lógica de análise, jogo e OBS não muda.

## Review Focus

- Botão desabilitado (Parar, Achar destaques durante a análise): precisa continuar visivelmente apagado, não dourado vivo.
- Lista do Combobox de replays (popup `Listbox`): não pode abrir branca com texto creme ilegível.
- Linha selecionada da tabela: texto legível sobre o dourado.
- Campo de senha e spinbox com foco: cursor visível (não preto sobre verde-escuro).
- Falha numa tarefa de fundo: a mensagem "Erro: ..." aparece na caixa de mensagens.

---

### Task 1: Módulo de tema

**Files:**
- Create: `dlh/theme.py`
- Test: `tests/test_theme.py`

**Interfaces:**
- Produces: `PALETTE: dict[str, str]` com as chaves `bg, card, line, text, muted, gold, gold_hover, on_gold, error`; `FONT = "Segoe UI"`, `FONT_BOLD = "Segoe UI Semibold"`; `apply(root: tk.Tk) -> ttk.Style`; `dark_titlebar(root: tk.Tk) -> None`. Estilos criados: `Title.TLabel`, `Sub.TLabel`, `Step.TLabel`, `Muted.TLabel`, `Gold.TButton`, `Card.TFrame`, `Card.TLabelframe`.

- [ ] **Step 1: Write the failing test** em `tests/test_theme.py` (unittest, cria `tk.Tk()` e `withdraw()`):
  - `test_palette_values`: `PALETTE["bg"] == "#081B1B"`, `PALETTE["gold"] == "#C18D52"`, `PALETTE["text"] == "#EEE8B2"`, `PALETTE["muted"] == "#96CDB0"`.
  - `test_apply_configures_styles`: depois de `apply(root)`, `style.theme_use() == "clam"`, `style.lookup("TFrame", "background") == "#081B1B"`, `style.lookup("Gold.TButton", "background") == "#C18D52"`, `style.lookup("Gold.TButton", "foreground") == "#081B1B"`, `style.lookup("Treeview", "fieldbackground") == "#203B37"`, `root.cget("bg") == "#081B1B"`.
  - `test_disabled_button_not_gold`: `style.lookup("Gold.TButton", "background", ["disabled"]) != "#C18D52"`.
  - `test_combobox_popup_dark`: `root.option_get("background", "TCombobox.Listbox")` ou a opção `*TCombobox*Listbox.background` igual a `#203B37` (ler com `root.tk.call("option", "get", ...)` num `Listbox` filho criado com nome de classe; aceitar o que o implementador definir via `option_add`).
- [ ] **Step 2: Run test to verify it fails** — `.venv\Scripts\python -m unittest tests.test_theme -v` → FAIL (`No module named 'dlh.theme'`).
- [ ] **Step 3: Implement `dlh/theme.py`** — `apply` usa `theme_use("clam")`, `configure` + `map` para TFrame, TLabel, TButton, Gold.TButton, TEntry, TSpinbox, TCombobox, TNotebook/TNotebook.Tab (aba ativa com texto dourado), Treeview/Treeview.Heading (seleção `#C18D52` com texto `#081B1B`), TScrollbar, TProgressbar (barra dourada), TLabelframe, TSeparator; `insertcolor` creme nos campos; `option_add("*TCombobox*Listbox.*", ...)` para o popup. `dark_titlebar` chama `DwmSetWindowAttribute(hwnd, 20, 1)` via ctypes em `try/except` (sem efeito fora do Windows 10/11).
- [ ] **Step 4: Run test to verify it passes** — mesmo comando → OK.
- [ ] **Step 5: Commit** — `git add dlh/theme.py tests/test_theme.py && git commit -m "Tema Deadlock: módulo de cores"`.

### Task 2: Aplicar o tema no app e corrigir o run_bg

**Files:**
- Modify: `app.py` (constantes linha 20; estilo linhas 43-55; caixa de mensagens 62-66; `run_bg` 91-103; `_status` 138; `Big.TButton` 229, 397, 426; rótulos com `foreground=GRAY`)
- Test: `tests/test_app_ui.py`

**Interfaces:**
- Consumes: `dlh.theme.apply`, `dlh.theme.dark_titlebar`, `dlh.theme.PALETTE`.

- [ ] **Step 1: Write the failing test** em `tests/test_app_ui.py` (unittest; `App()` com `after`/`withdraw`, sem esperar o jogo/OBS):
  - `test_window_uses_theme`: `app.cget("bg") == "#081B1B"`, `app.logbox.cget("background") == "#203B37"`, `app.logbox.cget("height") == 4`, `str(app.b_analyze.cget("style")) == "Gold.TButton"`, `str(app.b_rec.cget("style")) == "Gold.TButton"`.
  - `test_status_colors`: `app._set(app.s_dir, True)` → `fg == "#96CDB0"`; `app._set(app.s_dir, False)` → `fg == "#ef8a74"`; `app.s_dir.cget("bg") == "#081B1B"`.
  - `test_run_bg_logs_error`: `app.run_bg(lambda: 1/0)`, bombear `app.q` até vazio (com pequena espera pela thread), e o texto de `app.logbox` contém `"Erro: division by zero"`.
- [ ] **Step 2: Run** `.venv\Scripts\python -m unittest tests.test_app_ui -v` → FAIL.
- [ ] **Step 3: Implement** — trocar `GREEN, RED, GRAY` por `PALETTE["muted"], PALETTE["error"], PALETTE["muted"]`; chamar `theme.apply(self)` e `theme.dark_titlebar(self)` no lugar do bloco `vista`; título com `Title.TLabel` (dourado) e subtítulo com `Sub.TLabel`; `foreground=GRAY` dos rótulos vira `style="Muted.TLabel"`; `Big.TButton` vira `Gold.TButton` (os três botões principais); `logbox` com `height=4`, `background=card`, `foreground=muted`, `insertbackground=text`, `relief="flat"`, `highlightthickness=0`; `_status` com `bg=PALETTE["bg"]`. No `run_bg`, capturar a mensagem em variável local (`msg = f"Erro: {e}"`) antes do `lambda`.
- [ ] **Step 4: Run** os dois arquivos de teste → OK.
- [ ] **Step 5: Commit** — `git add app.py tests/test_app_ui.py && git commit -m "Tema Deadlock na janela e correção do erro do run_bg"`.

### Task 3: Conferência visual

- [ ] **Step 1:** Capturar as duas abas com a janela em primeiro plano (`attributes("-topmost", True)` + `CopyFromScreen` do retângulo da janela) e conferir: fundo verde, cartões, botões dourados, aba ativa, tabela com uma análise do replay de exemplo `..\highlights\demos\144195658.dem` e uma linha selecionada, popup do Combobox aberto.
- [ ] **Step 2:** Ajustar espaçamentos que ficarem estranhos e repetir a captura.
- [ ] **Step 3: Commit** dos ajustes, se houver.
