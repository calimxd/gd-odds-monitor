# Monitor de latencia de cuotas — giordota.com

Mide, cada 5 minutos y sin cuenta ni dinero, sobre el WebSocket publico `wss://giordota.com/esports-odds/`:

- `warn` / `error` y `scraper_fails`: caidas del copiador de cuotas por proveedor (LINEBET, BETWINNER, COMMERCIAL_API_ADAPTER).
- `lags`: segundos que tarda la cuota en reaccionar a un cambio de marcador (`MATCH_SCORE_UPDATE` -> `MATCH_ODDS_UPDATE`).
- `config`: cambios de `maintenanceMode` / `environmentMode`.
- `frames` / `bytes`: volumen que el sitio entrega a un cliente anonimo.

Los datos quedan en `data/AAAA-MM-DD.jsonl`, una linea por ejecucion.

## Resumen rapido

```bash
curl -s https://raw.githubusercontent.com/calimxd/gd-odds-monitor/main/data/$(date -u +%F).jsonl \
  | python3 -c "import sys,json;[print(json.loads(l)['ts'], json.loads(l)['warn'], json.loads(l)['error'], len(json.loads(l)['scraper_fails'])) for l in sys.stdin]"
```

## Criterio de decision

- Si `lags` trae valores > 2 s de forma repetida, hay ventana para apostar con informacion ya conocida.
- Si `scraper_fails` aparece varias veces por minuto, la cuota queda congelada mientras la fuente se mueve: es el escenario explotable.
- Si no aparece ninguno de los dos, no hay negocio y se cierra.

Solo lectura: no requiere cuenta, ni deposito, ni deja estado en el sitio.
