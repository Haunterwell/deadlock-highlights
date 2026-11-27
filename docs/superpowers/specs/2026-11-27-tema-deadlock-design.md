# Tema Deadlock no app (Tkinter) — design curto

**Aprovado em:** 2026-11-27

## Intenção
Deixar o Deadlock Highlights com o tema Deadlock: verde-escuro e dourado, em vez da janela cinza padrão do Windows.

## Objetivos
- Paleta do site em toda a janela: fundo `#081B1B`, cartões `#203B37`, borda `#2f524c`, texto creme `#EEE8B2`, rótulos menta `#96CDB0`, dourado `#C18D52` (hover `#d6a873`), texto sobre dourado `#081B1B`, erro `#ef8a74`.
- Botões principais (Achar destaques, Gravar selecionados) dourados com texto escuro; demais com contorno dourado.
- Abas, campos, spinbox, combobox, tabela, barra de progresso e caixa de mensagens escuros; linha selecionada da tabela em dourado escurecido.
- ✔ em menta, ✖ em `#ef8a74`.
- Barra de título do Windows escura.
- Caixa "Mensagens" mais baixa.
- Corrigir o bug do `run_bg` (lambda usando `e` depois do `except`).

## Fora do escopo (anti-objetivos)
- Nada de arte da Valve (Archmother, Hidden King) nem a fonte Valve Oracle: o app é público.
- Sem imagem de fundo (o Tkinter não permite atrás dos controles).
- Sem trocar de toolkit nem mexer na lógica de análise, jogo ou OBS.

## Abordagens
- **A. Interface em HTML/CSS (pywebview):** permitiria fundo com imagem e fontes web, mas exige reescrever a tela. Descartada pelo usuário.
- **B. Tema no Tkinter (escolhida):** tema `clam` do ttk reconfigurado com a paleta + widgets `tk` (Text, Listbox do combobox) coloridos à mão. Rápido e sem dependências novas.

## Decisões do builder
- Fonte: Segoe UI / Segoe UI Semibold (do sistema, sem embutir).
- Cores centralizadas num só lugar (`dlh/theme.py`) para facilitar ajustes.
