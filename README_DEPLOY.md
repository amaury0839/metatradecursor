# Despliegue: Local y Cloud

Resumen rápido: la repo soporta dos modos:
- `app/main.py` — UI local completa (usa MT5, para desarrollo local)
- `app/main_ui.py` — UI remota (sin trading), pensada para Streamlit Cloud

Requisitos locales

- Python 3.11+
- Instalar dependencias:

```bash
python -m pip install -r requirements.txt
```

Ejecución local (desarrollo)

1) Ejecutar bot + API (local trading):

```bash
python run_local_bot.py
# Esto levanta API en http://localhost:8000
```

2) Ejecutar UI local (opcional):

```bash
streamlit run app/main.py
# UI local completa (usa MT5 si está disponible)
```

Ejecutar con Docker (bot + UI)

Construir y levantar con `docker-compose`:

```bash
docker compose build
docker compose up -d
```

Servicios expuestos:
- Bot/API: http://localhost:8000
- Streamlit UI: http://localhost:8501

Despliegue en Streamlit Cloud

- En Streamlit Cloud configura el entrypoint a `app/main_ui.py` (no `app/main.py`).
- Asegura que los Secrets contengan `TRADING_BOT_API_URL` apuntando a tu API pública (o usa ngrok para tunelizar `http://localhost:8000`).
- Streamlit Cloud instalará `requirements.txt` automáticamente.

CI / CD con GitHub Actions

Se incluyen dos workflows automáticos:

### 1. `docker-build.yml`
Construye y publica imágenes Docker en GitHub Container Registry (GHCR):
- Se dispara en pushes a `main`/`develop` y en releases (tags `v*`)
- Builds dos imágenes:
  - `ghcr.io/tu-usuario/repo-bot:latest` (API + bot)
  - `ghcr.io/tu-usuario/repo-ui:latest` (Streamlit UI)

**Activación automática:** Solo requiere que GitHub Actions esté habilitado (sin secretos adicionales, usa `GITHUB_TOKEN`).

### 2. `tests.yml`
Ejecuta tests y linting:
- Pytest en Python 3.11 y 3.12
- Flake8, Black, isort para code quality
- Se dispara en PRs y pushes a `main`

**Uso:** Los tests corren automáticamente en PRs, permitiendo validar cambios antes de merge.

### Publicar a Docker Hub (opcional)
Para publicar a Docker Hub en lugar de GHCR, crea un secret `DOCKERHUB_TOKEN`:
1. En GitHub: Settings → Secrets and variables → Actions
2. Añade `DOCKERHUB_TOKEN` (tu token de Docker Hub)
3. Modifica `docker-build.yml`:
```yaml
- uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```
4. Cambia `${{ env.REGISTRY }}` a `docker.io/tu-usuario`
