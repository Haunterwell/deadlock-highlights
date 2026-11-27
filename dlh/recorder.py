"""Grava os destaques: pula a demo, trava a camera em quem matou e grava no OBS."""
import re
import time
from pathlib import Path

from .obsws import OBS

GAME_CAPTURE_WINDOW = "Deadlock:SDL_app:deadlock.exe"
CAPTURE_NAME = "Deadlock (captura de jogo)"


def connect_obs(cfg):
    return OBS(cfg["obs_host"], int(cfg["obs_port"]), cfg.get("obs_password", ""))


def ensure_scene(obs, scene):
    """Cria a cena com uma Captura de jogo do Deadlock, se ainda nao existir. Devolve True se criou."""
    names = [s["sceneName"] for s in obs.call("GetSceneList")["scenes"]]
    created = False
    if scene not in names:
        obs.call("CreateScene", {"sceneName": scene})
        created = True
    items = [i["sourceName"] for i in obs.call("GetSceneItemList", {"sceneName": scene})["sceneItems"]]
    if not any("deadlock" in i.lower() for i in items):
        inputs = [i["inputName"] for i in obs.call("GetInputList")["inputs"]]
        if CAPTURE_NAME in inputs:
            obs.call("CreateSceneItem", {"sceneName": scene, "sourceName": CAPTURE_NAME})
        else:
            obs.call("CreateInput", {
                "sceneName": scene, "inputName": CAPTURE_NAME, "inputKind": "game_capture",
                "inputSettings": {"capture_mode": "window", "window": GAME_CAPTURE_WINDOW, "priority": 2,
                                  "capture_audio": True, "capture_cursor": False},
                "sceneItemEnabled": True})
        vs = obs.call("GetVideoSettings")
        item = obs.call("GetSceneItemId", {"sceneName": scene, "sourceName": CAPTURE_NAME})["sceneItemId"]
        obs.call("SetSceneItemTransform", {"sceneName": scene, "sceneItemId": item, "sceneItemTransform": {
            "boundsType": "OBS_BOUNDS_SCALE_INNER", "boundsWidth": vs["baseWidth"],
            "boundsHeight": vs["baseHeight"], "positionX": 0, "positionY": 0,
            "alignment": 5, "boundsAlignment": 0}})
        created = True
    return created


def safe(s):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", s).strip("_") or "x"


def record(game, cfg, analysis, chosen, log, stop, progress=None):
    """Grava os destaques de indices `chosen` (0-based). `log(str)` recebe mensagens; `stop` e um Event."""
    rate = analysis["tick_rate"]
    match = analysis["match"]
    after_s = float(cfg.get("after_s", 4))
    scene = cfg.get("obs_scene") or ""
    saved = []

    obs = connect_obs(cfg)
    if obs.call("GetRecordStatus").get("outputActive"):
        obs.close()
        raise RuntimeError("O OBS ja esta gravando. Pare a gravacao no OBS e tente de novo.")
    prev_scene = obs.call("GetCurrentProgramScene").get("currentProgramSceneName")
    switched = False
    if scene and prev_scene != scene:
        if obs.call("GetStreamStatus").get("outputActive"):
            log(f"Transmissao ao vivo ativa: a cena nao sera trocada (gravando '{prev_scene}').")
        else:
            ensure_scene(obs, scene)
            obs.call("SetCurrentProgramScene", {"sceneName": scene})
            switched = True
            time.sleep(2)

    try:
        for count, idx in enumerate(chosen, 1):
            if stop.is_set():
                log("Parado.")
                break
            h = analysis["highlights"][idx]
            n = idx + 1
            assists = h.get("assists", 0)
            log(f"[{count}/{len(chosen)}] #{n} {h['clock']} {h['player']} ({h['hero']}) - {h['kills']} abates"
                + (f", {assists} assist." if assists else ""))
            if progress:
                progress(count - 1, len(chosen))
            pos = game.log_pos()
            game.send(f"demo_gototick {h['tick_start']}")
            if not game.wait_log(pos, rf"Skipping finished at tick {h['tick_start']}", 40, stop):
                if stop.is_set():
                    break
                log("   O jogo nao confirmou o pulo. A demo esta aberta e o console fechado? Pulando este.")
                continue
            jumped_at = time.time()
            time.sleep(0.5)
            game.send("demo_resume", "spec_autodirector 0", "spec_mode 1",
                      f'spec_player "{h["player"]}"', f"citadel_spec_lock_to_accountid {h['account_id']}")
            time.sleep(1.0)
            obs.call("StartRecord")
            end = jumped_at + (h["tick_last"] - h["tick_start"]) / rate + after_s
            while time.time() < end and not stop.is_set():
                time.sleep(0.2)
            out = obs.call("StopRecord").get("outputPath", "")
            try:
                game.send("demo_pause")  # congela o replay entre um clipe e outro (e no fim)
            except RuntimeError as e:
                log(f"   nao consegui pausar a demo: {e}")
            time.sleep(1.5)
            if out and Path(out).exists():
                dest = Path(out).with_name(
                    f"{match}_{n:02d}_{h['clock'].replace(':', '-')}_{safe(h['player'])}_{h['kills']}kills"
                    + (f"_{assists}assists" if assists else "") + Path(out).suffix)
                for _ in range(10):
                    try:
                        Path(out).rename(dest)
                        break
                    except OSError:
                        time.sleep(0.5)
                else:
                    dest = Path(out)
                saved.append(dest)
                log(f"   salvo: {dest.name}")
            else:
                log(f"   gravacao terminou: {out or '(o OBS nao informou o arquivo)'}")
        if progress:
            progress(len(chosen), len(chosen))
    finally:
        try:
            if obs.call("GetRecordStatus").get("outputActive"):
                obs.call("StopRecord")
            if switched:
                obs.call("SetCurrentProgramScene", {"sceneName": prev_scene})
        finally:
            obs.close()
    return saved
