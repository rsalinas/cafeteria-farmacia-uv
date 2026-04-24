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

### Workflow de confiança

La confiança en els scripts determina el mode d'execució:

1. **Scripts de confiança** (código nostre, sense flags especials):
   - `farmacafe_menu_plus.py`: ext. normal, pot escriure estat
   - `farmacafe_parser_repair_helper.py`: ext. normal, prepara contexte de reparació

2. **Parsers reparats per IA** (amb `--sandbox-mode`):
   - Filesystem de només lectura per aïllar codi potencialment no fiable

### Execució normal (script de confiança)

```bash
./bin/farmacafe_podman_launcher.sh --auto-build -- --json
```

Característiques:
- Filesystem escrivible (per a estat `.state/`)
- `tmpfs` efímer per a `/tmp` i `/run`
- Sense capacitats Linux (`--cap-drop=ALL`)
- Límits de CPU (1), memòria (256M), PIDs (128)
- Xarxa per defecte (sense internet si `--no-network`)

### Execució amb sandbox mode (parser de confiança baixa)

Per a parsers reparats per IA (codi no de confiar):

```bash
./bin/farmacafe_podman_launcher.sh --build --sandbox-mode -- --json --no-state-update
```

`--sandbox-mode` activa:
- Root filesystem de només lectura
- No pot mutate cap fit local
- Aïllament total de codi potencialment maligne

### Workflow complet de reparació

1. Executar menú i detectar error:
   ```bash
   ./bin/farmacafe_podman_launcher.sh -- --json
   ```

2. Generar context de reparació (script de confiança):
   ```bash
   python src/farmacafe_parser_repair_helper.py --report-file repair_context.json
   ```

3. Enviar `repair_context.json` a OpenAI API per reparar `src/farmacafe_parser.py`

4. Testar parser reparatdu sense confiar (aïllat en sandbox):
   ```bash
   ./bin/farmacafe_podman_launcher.sh --sandbox-mode -- --json --no-state-update
   ```

5. Si funciona, acceptar canvi. Si no, repetir reparació.

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
