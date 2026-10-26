from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.responses import HTMLResponse


def install_swagger_file_picker(app: FastAPI) -> None:
    """Use native multi-selection for binary arrays in the existing Swagger UI."""
    plugin = Path(__file__).with_name("swagger_file_arrays.js").read_text(encoding="utf-8")

    @app.get("/docs", include_in_schema=False)
    async def swagger_docs(request: Request) -> HTMLResponse:
        root_path = request.scope.get("root_path", "").rstrip("/")
        redirect = app.swagger_ui_oauth2_redirect_url
        response = get_swagger_ui_html(
            openapi_url=root_path + app.openapi_url,
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=root_path + redirect if redirect else None,
            swagger_ui_parameters=app.swagger_ui_parameters,
            init_oauth=app.swagger_ui_init_oauth,
        )
        # FastAPI's helper JSON-encodes settings; plugin functions must be
        # supplied as JavaScript. Keep its default assets and initialization.
        html = response.body.decode().replace(
            "const ui = SwaggerUIBundle({",
            plugin + "\nconst ui = SwaggerUIBundle({\nplugins: [BinaryFileArrayPlugin],",
            1,
        )
        return HTMLResponse(html)

    if app.swagger_ui_oauth2_redirect_url:
        app.add_api_route(
            app.swagger_ui_oauth2_redirect_url,
            get_swagger_ui_oauth2_redirect_html,
            include_in_schema=False,
        )
