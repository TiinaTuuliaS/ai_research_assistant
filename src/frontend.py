"""Serve the production SPA without swallowing unknown API routes."""
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def install_frontend(app, directory):
    root = Path(directory)
    if not (root / "index.html").is_file():
        raise RuntimeError("Frontend build is missing")
    app.mount("/static", StaticFiles(directory=root / "static"), name="frontend-static")

    def index():
        return FileResponse(root / "index.html")

    for route in ("/", "/login", "/signup", "/history"):
        app.add_api_route(route, index, methods=["GET"], include_in_schema=False)

    def asset_response(path):
        def asset():
            return FileResponse(path)
        return asset

    for name in ("favicon.ico", "robots.txt", "manifest.json"):
        if (root / name).is_file():
            app.add_api_route("/" + name, asset_response(root / name), methods=["GET"], include_in_schema=False)
