import logging

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ycpa.core.exceptions import AppException
from ycpa.services.error_mail import send_error_alert

logger = logging.getLogger(__name__)


async def app_exception_handler(
    request: Request,
    exc: AppException,
):
    await send_error_alert(
        request=request,
        status_code=exc.status_code,
        exception=exc,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({
            "detail": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
        }),
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    await send_error_alert(
        request=request,
        status_code=exc.status_code,
        exception=exc,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({
            "detail": exc.detail,
        }),
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    await send_error_alert(
        request=request,
        status_code=422,
        exception=exc,
    )

    return JSONResponse(
        status_code=422,
        content={
            "detail": jsonable_encoder(exc.errors()),
        },
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
):
    await send_error_alert(
        request=request,
        status_code=500,
        exception=exc,
    )

    logger.error(
        "Unhandled application exception",
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
        },
    )