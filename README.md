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

També el pots executar directament amb el Python del `venv`:

```bash
.venv/bin/python farmacafe_menu.py
```

L'eixida de la versió bàsica mostra al final la URL del menú per a ampliar informació.

Versió més detallada (extracció estructurada i eixida completa):

```bash
python farmacafe_menu_ext.py
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

## Eixida d'exemple

Exemple real de la versió bàsica en data 20-04-2026:

```text
=== Menú diario: 20-4-2026 ===

Primeros platos:
	- ENSALADA DE QUESO DE CABRA
	- ARROZ NEGRO
	- ESPINACAS SALTEADAS
	- SOPA CASTELLANA

Segundos platos:
	- MILHOJAS DE PATATA
	- SALMON A LA PLANCHA
	- PECHUGA A LA CREMA

PREU: 7,80 €/Persona
```

## Dependències

Les dependències del projecte es gestionen amb [requirements.txt](requirements.txt).

- bs4
- requests
