#!/usr/bin/env python3
"""Monitor pasivo de latencia de cuotas de giordota.com (WebSocket publico).

Escribe UNA linea JSON por ejecucion con agregados y eventos. Sin cuenta, sin dinero.
"""
import asyncio, json, sys, time
import websockets

URL = "wss://giordota.com/esports-odds/"
DUR = int(sys.argv[1]) if len(sys.argv) > 1 else 240

async def main():
    t0 = time.time()
    agg = {"frames": 0, "bytes": 0, "score": 0, "odds": 0, "warn": 0, "error": 0,
           "config": [], "lags": [], "scraper_fails": [], "errors": []}
    pend = {}
    try:
        async with websockets.connect(URL, max_size=64 * 1024 * 1024, ping_interval=20) as ws:
            try:
                await ws.send(json.dumps({"op": "subscribe_match", "d": {"all": True}}))
            except Exception:
                pass
            while time.time() - t0 < DUR:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=max(1, DUR - (time.time() - t0)))
                except asyncio.TimeoutError:
                    break
                ts = time.time()
                agg["frames"] += 1
                agg["bytes"] += len(raw)
                try:
                    m = json.loads(raw)
                except Exception:
                    continue
                if m.get("op") == "SCRAPER_LOG":
                    d = m.get("d") or {}
                    lvl = d.get("level")
                    if lvl == "WARN":
                        agg["warn"] += 1
                    if lvl == "ERROR":
                        agg["error"] += 1
                    if lvl in ("WARN", "ERROR"):
                        agg["scraper_fails"].append({"t": round(ts - t0, 1), "lvl": lvl,
                                                     "prov": d.get("provider"), "act": d.get("action")})
                    continue
                d = m.get("d") or {}
                mid = d.get("matchId") or d.get("id") or (d.get("match") or {}).get("id")
                if d.get("type") == "MATCH_SCORE_UPDATE":
                    agg["score"] += 1
                    if mid:
                        pend[mid] = ts
                elif d.get("type") == "MATCH_ODDS_UPDATE":
                    agg["odds"] += 1
                    if mid in pend:
                        agg["lags"].append({"match": mid, "s": round(ts - pend.pop(mid), 2)})
                elif d.get("type") == "SYSTEM_CONFIG_UPDATE":
                    agg["config"].append({"t": round(ts - t0, 1), "maint": d.get("maintenanceMode"),
                                          "env": d.get("environmentMode")})
    except Exception as e:
        agg["errors"].append(repr(e)[:180])
    agg["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    agg["dur_s"] = round(time.time() - t0, 1)
    print(json.dumps(agg, ensure_ascii=False))

asyncio.run(main())
