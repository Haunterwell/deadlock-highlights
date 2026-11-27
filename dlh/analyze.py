"""Le um replay (.dem) com o boon-deadlock e acha os multi-kills."""
from pathlib import Path

STEAM64_BASE = 76561197960265728


def find_highlights(demo_path, window_s=20.0, min_kills=2, before_s=8.0, min_assists=0):
    """Devolve {"demo", "match", "tick_rate", "total_kills", "players", "highlights": [...]}.

    Um destaque e uma sequencia de abates e assistencias do mesmo jogador, com no maximo `window_s`
    segundos entre um e outro, que tenha pelo menos `min_kills` abates e `min_assists` assistencias.
    Com min_assists = 0 as assistencias nem entram na conta (so multi-kills).
    """
    count_assists = min_assists > 0
    import boon  # importado aqui: demora um pouco e so e preciso na analise

    demo = boon.Demo(str(demo_path))
    rate = demo.tick_rate
    players = {r["hero_id"]: r for r in demo.players.iter_rows(named=True)}
    try:
        hero_names = boon.hero_names()
    except Exception:
        hero_names = {}

    def name(hid):
        p = players.get(hid)
        return p["player_name"] if p else f"heroi {hid}"

    def clock(tick):
        try:
            c = demo.tick_to_match_clock(tick)
        except Exception:
            c = None
        return c or demo.tick_to_clock_time(tick)

    kills = demo.kills.sort("tick")
    # eventos por jogador: (tick, vitima, "kill" ou "assist")
    events = {}
    for k in kills.iter_rows(named=True):
        vic, att = k["victim_hero_id"], k["attacker_hero_id"]
        if att in players and att != vic:
            events.setdefault(att, []).append({"tick": k["tick"], "victim": vic, "kind": "kill"})
        if count_assists:
            for a in k.get("assister_hero_ids") or []:
                if a in players and a not in (att, vic):
                    events.setdefault(a, []).append({"tick": k["tick"], "victim": vic, "kind": "assist"})

    found = []
    for att, ks in events.items():
        ks.sort(key=lambda e: e["tick"])
        group = [ks[0]]
        for k in ks[1:] + [None]:
            if k is not None and (k["tick"] - group[-1]["tick"]) / rate <= window_s:
                group.append(k)
                continue
            n_kills = sum(g["kind"] == "kill" for g in group)
            if n_kills >= min_kills and len(group) - n_kills >= min_assists and len(group) >= 1:
                t0, t1 = group[0]["tick"], group[-1]["tick"]
                sid = players[att].get("steam_id") or 0
                found.append({
                    "player": name(att),
                    "account_id": sid - STEAM64_BASE if sid > STEAM64_BASE else sid,
                    "hero": hero_names.get(att, str(att)) if isinstance(hero_names, dict) else str(att),
                    "kills": n_kills,
                    "assists": len(group) - n_kills,
                    "victims": [name(g["victim"]) + ("" if g["kind"] == "kill" else " (assist.)")
                                for g in group],
                    "clock": clock(t0),
                    "span_s": round((t1 - t0) / rate, 1),
                    "tick_first": t0,
                    "tick_last": t1,
                    "tick_start": max(0, int(t0 - before_s * rate)),
                })
            if k is not None:
                group = [k]
    found.sort(key=lambda f: f["tick_first"])
    return {
        "demo": str(Path(demo_path).resolve()),
        "match": Path(demo_path).stem,
        "tick_rate": rate,
        "total_kills": kills.height,
        "players": len(players),
        "highlights": found,
    }
