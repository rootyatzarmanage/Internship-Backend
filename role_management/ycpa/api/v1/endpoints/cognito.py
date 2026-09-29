# ycpa/api/v1/endpoints/cognito.py
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Response, status
from passlib.context import CryptContext
from jose import jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from ycpa.core.auth.dependencies import ACCESS_TOKEN_COOKIE, ID_TOKEN_COOKIE
from ycpa.core.config import get_settings
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.email import build_otp_email, send_email
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.schemas.requests.auth import ForgotPasswordRequest, VerifyOtpRequest, ResetPasswordRequest
from ycpa.models.roles import Role
from ycpa.models.user import User
from ycpa.models.storage_usage import StorageUsage
from ycpa.models.subscription import AimSubscription, PimSubscription
from ycpa.models.workspace import PimWorkspace, PimWorkspaceMember, PimProject, PimProjectMember
from ycpa.repositories.auth.users import UserRepository

logger = logging.getLogger(__name__)
settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/auth", tags=["Auth"])

OTP_EXPIRE_MINUTES = 10
_otp_store: dict[str, dict] = {}  # email -> { otp, expires_at }

COOKIE_SECURE   = settings.ENVIRONMENT not in ("local", "development")
COOKIE_SAMESITE = "none" if settings.ENVIRONMENT not in ("local", "development") else "lax"
COOKIE_MAX_AGE  = 60 * 60


def _hash_password(password: str) -> str:
    return pwd_context.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": user_id, "exp": expire, "jti": str(uuid.uuid4())},
        settings.JWT_SECRET.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )


def _generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"


def _store_otp(email: str, otp: str) -> None:
    _otp_store[email.lower()] = {
        "otp": pwd_context.hash(otp),
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES),
    }


def _verify_otp_from_store(email: str, otp: str) -> bool:
    record = _otp_store.get(email.lower())
    if not record:
        return False
    if datetime.now(timezone.utc) > record["expires_at"]:
        _otp_store.pop(email.lower(), None)
        return False
    if not pwd_context.verify(otp, record["otp"]):
        return False
    return True


@router.post(
    "/forgot-password",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Send OTP to email for password reset",
)
async def forgot_password(
    body: ForgotPasswordRequest,
    session: DatabaseSession,
) -> SuccessResponse:
    repo = UserRepository(session)
    user = await repo.get_by_email(body.email)
    if not user:
        return SuccessResponse(success=True, message="If the email exists, a reset code has been sent.")

    otp = _generate_otp()
    _store_otp(body.email, otp)

    html = build_otp_email(otp)
    sent = await send_email(body.email, "Your YCPA Password Reset Code", html)

    if not sent:
        _otp_store.pop(body.email.lower(), None)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification code. Please try again later.",
        )

    return SuccessResponse(success=True, message="A verification code has been sent to your email.")


@router.post(
    "/verify-otp",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify the OTP sent to email",
)
async def verify_otp(
    body: VerifyOtpRequest,
) -> SuccessResponse:
    if not _verify_otp_from_store(body.email, body.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")
    return SuccessResponse(success=True, message="OTP verified.")


@router.post(
    "/reset-password",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password using verified OTP",
)
async def reset_password(
    body: ResetPasswordRequest,
    session: DatabaseSession,
) -> SuccessResponse:
    if not _verify_otp_from_store(body.email, body.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")

    repo = UserRepository(session)
    user = await repo.get_by_email(body.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.password_hash = _hash_password(body.new_password)
    await session.commit()

    _otp_store.pop(body.email.lower(), None)

    return SuccessResponse(success=True, message="Password updated successfully.")


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class LocalLoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post(
    "/cognito-signup",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
)
async def signup(body: SignupRequest, session: DatabaseSession) -> SuccessResponse:
    repo = UserRepository(session)

    existing = await repo.get_by_email(body.email)
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = User(
        cognito_sub=str(uuid.uuid4()),   # placeholder — no longer used for auth
        email=body.email,
        full_name=body.full_name,
        password_hash=_hash_password(body.password),
        email_verified=True,
        platform_role="customer",
        is_active=True,
        is_onboarded=False,
        is_default_onboarding=True,
        login_count=0,
    )
    session.add(user)
    await session.flush()

    session.add(StorageUsage(user_id=user.id, bytes_used=0, bytes_limit=5_368_709_120, file_count=0))
    session.add(PimSubscription(
        user_id=user.id, plan="free", status="active",
        max_pim_workspaces=1, max_projects_per_pim_workspace=1,
        max_members_per_workspace=10, max_members_per_project=10,
        can_use_4d=False, can_use_5d=False, can_use_clash_detection=False,
        can_export_bcf=True, can_use_api=False,
    ))
    session.add(AimSubscription(
        user_id=user.id, plan="free", status="active",
        max_aim_workspaces=1, max_projects_per_aim_workspace=1,
        max_members_per_workspace=10, max_members_per_project=10,
        can_use_ai=False, can_use_api=False,
        can_use_maintenance=True, can_use_facility=True,
    ))

    # Auto-create default workspace 'IFC-Workspace' and project 'IFC-Project'
    workspace = PimWorkspace(
        owner_id=user.id,
        name="IFC-Workspace",
        description="Default workspace",
        is_active=True,
        created_by=user.id,
    )
    session.add(workspace)
    await session.flush()

    workspace_member = PimWorkspaceMember(
        workspace_id=workspace.id,
        user_id=user.id,
        role="admin",
        invited_by=user.id,
        created_by=user.id,
    )
    session.add(workspace_member)

    project = PimProject(
        workspace_id=workspace.id,
        name="IFC-Project",
        description="Default project",
        status="active",
        created_by=user.id,
    )
    session.add(project)
    await session.flush()

    bim_manager_role = await session.scalar(
        select(Role).where(Role.name == "BIM Manager", Role.is_active.is_(True), Role.deleted_at.is_(None))
    )
    project_member = PimProjectMember(
        project_id=project.id,
        user_id=user.id,
        role_id=bim_manager_role.id if bim_manager_role else None,
        invited_by=user.id,
        created_by=user.id,
    )
    session.add(project_member)

    await session.commit()

    logger.info("New user registered with default workspace and project", extra={
        "user_id": str(user.id),
        "email": user.email,
        "workspace_id": str(workspace.id),
        "project_id": str(project.id),
    })
    return SuccessResponse(
        success=True,
        message="Account created. You can now sign in.",
        data={
            "workspace_id": str(workspace.id),
            "project_id": str(project.id),
        },
    )


@router.post(
    "/cognito-login",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Login and get JWT tokens",
)
async def local_login(body: LocalLoginRequest, response: Response, session: DatabaseSession) -> SuccessResponse:
    repo = UserRepository(session)
    user = await repo.get_by_email(body.email)

    if not user or not user.password_hash or not _verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Your account has been deactivated.")

    token = _create_token(str(user.id))

    _set_cookies(response, token, token)

    return SuccessResponse(
        success=True,
        message="Login successful.",
        data={"id_token": token, "access_token": token},
    )


def _set_cookies(response: Response, id_token: str, access_token: str) -> None:
    _args = {
        "httponly": True,
        "secure": COOKIE_SECURE,
        "samesite": COOKIE_SAMESITE,
        "max_age": COOKIE_MAX_AGE,
        "path": "/",
    }
    response.set_cookie(key=ID_TOKEN_COOKIE, value=id_token, **_args)
    response.set_cookie(key=ACCESS_TOKEN_COOKIE, value=access_token, **_args)
 
