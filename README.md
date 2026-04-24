# Cafeteria Farmacia UV

Projecte Python per a extraure i mostrar el menú de la cafeteria de Farmàcia UV.

## Requisits

- Python 3.10 o superior
- `venv` (normalment inclòs amb Python)

## Configuració de l'entorn virtual

1. Crear l'entorn virtual:

```bash
python3 -m venv .venv
```

2. Activar l'entorn virtual:

```bash
source .venv/bin/activate
```

3. Instal·lar dependències:

```bash
pip install -r requirements.txt
```

## Executar scripts

Amb l'entorn virtual activat:

```bash
python farmacafe_menu.py
```

Per a eixida estructurada en JSON:

```bash
python farmacafe_menu.py --json
```

El JSON inclou claus com `primers`, `segons`, `preu`, `data_menu` i `url`.

També el pots executar directament amb el Python del `venv`:

```bash
.venv/bin/python farmacafe_menu.py
```

L'eixida de la versió bàsica mostra al final la URL del menú per a ampliar informació.

Versió més detallada (extracció estructurada i eixida completa):

```bash
python farmacafe_menu_ext.py
```

Nova versió completa amb detecció de canvis (ignorant la data mostrada al web):

```bash
python farmacafe_menu_plus.py
```

JSON complet (inclou seccions, plats, intoleràncies, metadades i detector de canvis):

```bash
python farmacafe_menu_plus.py --json
```

Forçar codi d'eixida quan detecta canvi respecte a l'últim snapshot:

```bash
python farmacafe_menu_plus.py --exit-code-on-change 10
```

El fitxer d'estat es guarda en `.state/farmacafe_menu_plus_state.json` i es pot canviar amb `--state-file`.

Per a no modificar l'estat (mode només lectura):

```bash
python farmacafe_menu_plus.py --no-state-update
```

Per incloure també el HTML cru dins del JSON (pot ser gran):

```bash
python farmacafe_menu_plus.py --json --include-html
```

## Parser separat i reparació sota demanda

El parsing de la web està separat i reduït en `farmacafe_parser.py`.

Per preparar un paquet de diagnòstic (HTML + codi parser + eixida/error) pensat per enviar a OpenAI API només quan falle o sota demanda:

```bash
python farmacafe_parser_repair_helper.py --report-file parser_repair_context.json
```

Si el parser falla, el script torna codi `2` i deixa el JSON llest per analitzar i corregir el parser automàticament.

## Execució aïllada amb Podman

Per executar els scripts en un contenidor mínim, sense accés al sistema de fitxers local (sense bind mounts), usa:

```bash
./farmacafe_podman_launcher.sh --build -- --json --state-file /tmp/farmacafe_state.json
```

Característiques de l'aïllament:

- Sense muntatges de directoris locals.
- Root filesystem en mode només lectura (`--read-only`).
- Només `/tmp` i `/run` en `tmpfs` efímer.
- Sense capacitats Linux (`--cap-drop=ALL`) i amb `no-new-privileges`.
- Límits de CPU, memòria i PIDs.

Executar helper de reparació dins del contenidor:

```bash
./farmacafe_podman_launcher.sh --script farmacafe_parser_repair_helper.py -- --report-file /tmp/parser_repair_context.json
```

Opcionalment pots desactivar xarxa:

```bash
./farmacafe_podman_launcher.sh --no-network -- --json --no-state-update
```

## Comandament `farmacaf`

El projecte inclou el script executable `farmacaf`, que força l'ús del `venv` local i executa sempre la versió bàsica.

Execució directa des del projecte:

```bash
./farmacaf
```

Per a tindre'l en el PATH:

```bash
chmod +x farmacaf
ln -sf "$(pwd)/farmacaf" ~/.local/bin/farmacaf
```

Després podràs executar:

```bash
farmacaf
```

Per a JSON des de `farmacaf`:

```bash
farmacaf --json
```

## Eixida d'exemple

Exemple real de la versió bàsica en data 20-04-2026:

```text
=== 20-4-2026 ===

Primers plats:
	- ENSALADA DE QUESO DE CABRA
	- ARROZ NEGRO
	- ESPINACAS SALTEADAS
	- SOPA CASTELLANA

Segons plats:
	- MILHOJAS DE PATATA
	- SALMON A LA PLANCHA
	- PECHUGA A LA CREMA

PREU: 7,80 €/Persona

Més informació: https://www.qrcarta.com/restaurant/burjassot/cafeteria-de-farmacia-uv/3616/?type=menu
```

## Dependències

Les dependències del projecte es gestionen amb [requirements.txt](requirements.txt).

- bs4
- requests
