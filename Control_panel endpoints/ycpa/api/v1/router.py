from fastapi import APIRouter

from ycpa.api.v1.endpoints import (
    auth,
    cognito,
    users,
    control_panel,
    support_tickets,
    ticket_list,
    ticket_reply
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(cognito.router)
api_router.include_router(users.router)
api_router.include_router(control_panel.router)

api_router.include_router(support_tickets.router)
api_router.include_router(ticket_list.router)
api_router.include_router(ticket_reply.router)
