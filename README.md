# Cafeteria Farmacia UV

Projecte Python per a extraure i monitoritzar el menú de la cafeteria de Farmàcia UV.

## Estructura del projecte

- `src/`: implementació actual activa.
- `bin/`: scripts executables (launcher, monitor, instal·lador).
- `systemd/`: plantilles de servei i timer.
- `legacy/implementations/`: implementacions antigues, només per referència històrica.

## Requisits

- Python 3.10 o superior
- `venv` (normalment inclòs amb Python)

## Configuració inicial

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ús ràpid

### Script principal (comandament curt)

```bash
./bin/farmacafe --json
```

Per posar-lo al PATH:

```bash
chmod +x bin/farmacafe
ln -sf "$(pwd)/bin/farmacafe" ~/.local/bin/farmacafe
farmacafe --json
```

### Extracció completa en JSON

```bash
python src/farmacafe_menu_plus.py --json
```

### Detecció de canvis (ignora la data visible del dia)

```bash
python src/farmacafe_menu_plus.py --state-file /tmp/state.json --exit-code-on-change 10
```

- Eixida `0`: sense canvi.
- Eixida `10`: canvi detectat.
- Eixida `1/2`: error d'execució/parsing.

### Parser separat i reparació sota demanda

Parser principal:

```text
src/farmacafe_parser.py
```

Generar context complet per a reparar parser amb IA només quan calga:

```bash
python src/farmacafe_parser_repair_helper.py --report-file parser_repair_context.json
```

El fitxer inclou `html_content`, `parser_source`, `parse_output` i `parse_error`.

## Execució aïllada amb Podman

```bash
./bin/farmacafe_podman_launcher.sh --build -- --json --state-file /tmp/farmacafe_state.json
```

Característiques:

- Sense bind mounts a fitxers locals.
- Root filesystem només lectura.
- `tmpfs` efímer per a `/tmp` i `/run`.
- Sense capacitats Linux (`--cap-drop=ALL`).
- Límits de CPU, memòria i PIDs.

Helper de reparació dins del contenidor:

```bash
./bin/farmacafe_podman_launcher.sh --script farmacafe_parser_repair_helper.py -- --report-file /tmp/parser_repair_context.json
```

## Automatització amb systemd (dl-dv)

Instal·lar i activar timer (usuari):

```bash
chmod +x bin/install_systemd_monitor.sh
./bin/install_systemd_monitor.sh
```

El timer s'executa només dilluns-divendres, cada 5 minuts, entre 12:01 i 13:56.

Execució manual del runner:

```bash
./bin/farmacafe_monitor_run.sh
```

Logs:

```bash
systemctl --user status farmacafe-monitor.timer
systemctl --user status farmacafe-monitor.service
journalctl --user -u farmacafe-monitor.service -n 100 --no-pager
```

Personalitza notificacions en:

```text
bin/farmacafe_on_change.sh
```

## Qualitat de codi amb pre-commit

S'ha configurat `.pre-commit-config.yaml` amb regles per:

- exigir executabilitat en scripts amb shebang,
- exigir shebang en fitxers executables,
- format i higiene bàsica de fitxers,
- detecció de conflictes/keys/fitxers massa grans,
- lint i format Python amb Ruff.

Instal·lació i ús:

```bash
source .venv/bin/activate
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Dependències

Les dependències del projecte es gestionen amb [requirements.txt](requirements.txt).
