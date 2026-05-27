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

### Recuperació ràpida del venv

Si canvia Python del sistema o el monitor comença a fallar per dependències, recrea el venv amb:

```bash
./bin/farmacafe_recreate_venv.sh --restart-timer
```

Per forçar una versió concreta de Python:

```bash
./bin/farmacafe_recreate_venv.sh --python /usr/bin/python3.12 --restart-timer
```

## Ús ràpid

### Lanzadores principals

```bash
# 1. Executar menú (local, sense Podman)
./bin/farmacafe --json

# 2. Executar menú (aïllat en Podman)
./bin/farmacafe_podman_launcher.sh -- --json

# 3. Generar context per a reparar parser (IA)
./bin/farmacafe_repair --report-file repair_context.json
```

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
python src/farmacafe_menu_plus.py --state-file /tmp/state.json --stability-polls 2 --exit-code-on-change 10
```

- Eixida `0`: sense canvi.
- Eixida `10`: canvi estabilitzat detectat (el nou menú s'ha vist en `N` sondejos consecutius).
- Eixida `1/2`: error d'execució/parsing.

Paràmetres rellevants:

- `--stability-polls N`: nombre de sondejos consecutius necessaris per confirmar un canvi.
- Valor per defecte: `2`.
- `--stability-polls 1`: comportament immediat (retrocompatible amb el model anterior).

### Parser separat i reparació sota demanda

Parser principal:

```text
src/farmacafe_parser.py
```

Generar context complet per a reparar parser amb IA només quan calga:

```bash
# Opció 1: Amb lanzador
./bin/farmacafe_repair --report-file parser_repair_context.json

# Opció 2: Directe
python src/farmacafe_parser_repair_helper.py --report-file parser_repair_context.json
```

El fitxer inclou `html_content`, `parser_source`, `parse_output` i `parse_error`.

Workflow complet:

```bash
# 1. Executar menú (si falla → error del parser)
./bin/farmacafe_podman_launcher.sh -- --json

# 2. Generar context per a IA
./bin/farmacafe_repair --report-file repair_context.json

# 3. [Enviar repair_context.json a OpenAI per reparar parser]

# 4. [Actualitzar src/farmacafe_parser.py amb parser reparador]

# 5. Testar parser (aïllat en sandbox, sense confiança)
./bin/farmacafe_podman_launcher.sh --sandbox-mode -- --json --no-state-update

# 6. Si funciona → acceptar canvi. Si no → repetir reparació.
```

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

El timer s'executa només dilluns-divendres, cada 10 minuts, entre 08:01 i 14:51.

Per defecte, el monitor usa estabilització de 2 sondejos consecutius abans d'enviar notificacions.
Es pot ajustar amb variable d'entorn:

```bash
STABILITY_POLLS=2 ./bin/farmacafe_monitor_run.sh
```

Exemple d'escenari:

- Poll 1 detecta un nou menú `B` (venint de `A`): no notifica, queda com a candidat.
- Poll 2 detecta `C`: reinicia candidat a `C`, encara sense notificar.
- Poll 3 detecta `C` altra vegada: com que `C` es repeteix 2 vegades, notifica.

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

### Notificacions personalitzades

El hook `bin/farmacafe_on_change.sh` gestiona notificacions automàtiques quan hi ha canvi.

#### Configuració requerida

1. **Mail (SMTP local)**
   ```bash
   # Instal·lar mailutils
   sudo apt install mailutils

   # Configurar adreça predeterminada (opcional)
   export EMAIL_TO="rausalinas@gmail.com"
   ```

2. **Telegram**
   ```bash
   # Obtenir token del bot (que no guardar en el repo!)
   export TELEGRAM_TOKEN=""

   # Obtenir Chat ID del canal/grup
   # Opció 1: Manual - Enviar un missatge al bot i obtenir l'ID dels updates
   curl "https://api.telegram.org/bot$TELEGRAM_TOKEN/getUpdates" | jq '.result[].message.chat.id'

   # Opció 2: Automatitzat - Script per detectar
   ./bin/get_telegram_chat_id.sh

   export TELEGRAM_CHAT_ID="ID_aqui"
   ```

#### Configurar variables d'entorn (persistent per a systemd)

```bash
# Per a l'usuari actual (systemd user-level)
mkdir -p ~/.config/environment.d
cat > ~/.config/environment.d/farmacafe.conf <<EOF
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=123456789
EMAIL_TO=rausalinas@gmail.com
STABILITY_POLLS=2
EOF

# Recarregar systemd per aplicar variables
systemctl --user daemon-reload

# Reiniciar timer per aplicar nous valors
systemctl --user restart farmacafe-monitor.timer
```

#### Com obtenir Chat ID de Telegram

1. **Si tens un canal**: El bot necessita ser membre del canal
   ```bash
   # Enviar un missatge al canal, llavors:
   curl "https://api.telegram.org/bot$TELEGRAM_TOKEN/getUpdates" | jq '.result[] | select(.channel_post) | .channel_post.chat.id'
   ```

2. **Si tens un grup privat**: Enviar un missatge dins del grup
   ```bash
   curl "https://api.telegram.org/bot$TELEGRAM_TOKEN/getUpdates" | jq '.result[] | select(.message.chat.type=="group") | .message.chat.id'
   ```

3. **Script automàtic** (crear `bin/get_telegram_chat_id.sh`):
   ```bash
   #!/bin/bash
   # Detectar l'últim chat ID on hi ha activitat
   TELEGRAM_TOKEN="${1:-$TELEGRAM_TOKEN}"
   if [[ -z "$TELEGRAM_TOKEN" ]]; then
     echo "Usa: $0 <token_o_variable_TELEGRAM_TOKEN>"
     exit 1
   fi
   curl -s "https://api.telegram.org/bot$TELEGRAM_TOKEN/getUpdates" | \
     jq -r '.result[-1].message.chat.id // .result[-1].channel_post.chat.id // empty'
   ```

#### Testar notificacions

```bash
# Generar menú de prueba
./bin/farmacafe_podman_launcher.sh -- --json > /tmp/test_menu.json

# Probar hook manualmente
TELEGRAM_TOKEN="..." TELEGRAM_CHAT_ID="..." ./bin/farmacafe_on_change.sh /tmp/test_menu.json
```

#### Personalitzar el hook

Edita `bin/farmacafe_on_change.sh` per afegir més canals o lògica personalitzada.

Exemples:
- Guardar historial a base de dades
- Enviar a múltiples adresses de mail
- Integrar amb webhooks (Slack, Discord, etc.)
- Generar alerta sonora local

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
