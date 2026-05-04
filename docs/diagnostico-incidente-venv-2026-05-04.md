# Diagnostico del incidente: dependencia del venv respecto al sistema

Fecha: 2026-05-04

## Resumen ejecutivo

El sistema de monitorizacion no estaba ejecutandose en contenedor. Estaba ejecutandose en el host mediante `systemd --user` y usando el Python del venv local (`.venv/bin/python`).

Tras cambios en el sistema operativo y/o en el Python del host, el venv quedo en estado inconsistente respecto a sus dependencias. El servicio fallo repetidamente con `ModuleNotFoundError: No module named 'requests'` hasta que se recreo el venv e instalaron dependencias otra vez.

## Evidencias

1. El servicio activo ejecuta el runner local del repositorio (host), no el lanzador de Podman.
   - Unidad instalada: `ExecStart=/home/raulsa8/git/cafeteria-farmacia-uv/bin/farmacafe_monitor_run.sh`
2. El runner local usa por defecto el Python del venv del host.
   - `PYTHON_BIN="${PYTHON_BIN:-$REPO_DIR/.venv/bin/python}"`
3. El journal del servicio muestra fallo por dependencia no disponible en el entorno.
   - `ModuleNotFoundError: No module named 'requests'`
4. Tras recrear el venv e instalar `requirements.txt`, el servicio vuelve a estado correcto (`No change detected`).

## Por que el contenedor no te protegio aqui

Tener un contenedor construido solo protege los procesos que realmente se ejecutan dentro de ese contenedor.

En este proyecto, el flujo de produccion de `systemd` estaba ligado al script local `bin/farmacafe_monitor_run.sh`, que ejecuta Python del host virtualenv, y no al script `bin/farmacafe_podman_launcher.sh`.

Por eso la robustez de imagen (`Containerfile.sandbox`) no aplicaba al servicio monitor.

## Causa raiz

1. Acoplamiento operativo del servicio a `.venv/bin/python` del host.
2. Falta de verificacion de salud previa del venv (imports criticos) antes de ejecutar el watcher.
3. Ausencia de automatismo de reparacion o alerta especifica para fallo de entorno Python.

## Solucion aplicada

1. Se recreo el venv y se reinstalaron dependencias (`requirements.txt`).
2. Se verifica que el servicio vuelve a ejecutar sin error de import.
3. Se anade script de recuperacion automatizable: `bin/farmacafe_recreate_venv.sh`.

## Solucion recomendada (definitiva)

### Opcion A: Mantener ejecucion en host (minimo cambio)

1. Usar siempre `bin/farmacafe_recreate_venv.sh` para reconstruccion.
2. Anadir `ExecStartPre` en la unidad para validar venv e imports (`requests`, `bs4`).
3. Configurar `OnFailure` para notificar por correo/Telegram cuando falle por entorno.

### Opcion B: Pasar monitor a contenedor (maxima reproducibilidad)

1. Cambiar `ExecStart` a `bin/farmacafe_podman_launcher.sh --auto-build -- --json ...`.
2. Gestionar estado persistente con volumen (ya contemplado en `.state`).
3. Mantener version base de Python en imagen (actualmente `python:3.12-alpine`).

## Playbook de recuperacion

```bash
./bin/farmacafe_recreate_venv.sh --restart-timer
```

Si quieres forzar version concreta de Python:

```bash
./bin/farmacafe_recreate_venv.sh --python /usr/bin/python3.12 --restart-timer
```

## Conclusiones

- La expectativa de "entorno reproducible" no se cumplia para el monitor porque la ruta real de ejecucion era host+venv.
- El contenedor era opcional y no estaba en el camino critico de `systemd`.
- Con un script de reconstruccion y chequeos previos, el riesgo baja mucho; con ejecucion en contenedor, se reduce aun mas.
