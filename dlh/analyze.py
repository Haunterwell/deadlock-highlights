"""Le um replay (.dem) com o boon-deadlock e acha os multi-kills."""
from pathlib import Path

STEAM64_BASE = 76561197960265728


def find_highlights(demo_path, window_s=20.0, min_kills=2, before_s=8.0):
    """Devolve {"demo", "match", "tick_rate", "total_kills", "players", "highlights": [...]}."""
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
    by_attacker = {}
    for k in kills.iter_rows(named=True):
        att = k["attacker_hero_id"]
        if att in players and att != k["victim_hero_id"]:
            by_attacker.setdefault(att, []).append(k)

    found = []
    for att, ks in by_attacker.items():
        group = [ks[0]]
        for k in ks[1:] + [None]:
            if k is not None and (k["tick"] - group[-1]["tick"]) / rate <= window_s:
                group.append(k)
                continue
            if len(group) >= min_kills:
                t0, t1 = group[0]["tick"], group[-1]["tick"]
                sid = players[att].get("steam_id") or 0
                found.append({
                    "player": name(att),
                    "account_id": sid - STEAM64_BASE if sid > STEAM64_BASE else sid,
                    "hero": hero_names.get(att, str(att)) if isinstance(hero_names, dict) else str(att),
                    "kills": len(group),
                    "victims": [name(g["victim_hero_id"]) for g in group],
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
