""""""

from app.utils.auth import get_password_hash, verify_passwordsecurity = HTTPBearer()
from app.utils.jwt import create_access_token, verify_tokenrouter = APIRouter()
from app.models.session import UserSession
from app.models.user import Userfrom app.services.auth_service import AuthService
from app.db import get_dbfrom app.models.user import User
from app.utils.jwt import create_access_token, verify_token
import loggingfrom app.db import get_db
from typing import Optional
from datetime import datetime, timedeltafrom datetime import datetime, timedelta
from sqlalchemy.orm import Sessionfrom sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestFormfrom fastapi.security import HTTPBearer
from fastapi import APIRouter, Depends, HTTPException, status, Formfrom fastapi import APIRouter, Depends, HTTPException, status
Authentication routes for KMRL Document Management SystemAuthentication routes

""""""


logger = logging.getLogger(__name__)@router.post("/login")


async def login(credentials: dict, db: Session = Depends(get_db)):

router = APIRouter(prefix="/api/auth", tags=["Authentication"])    """

    User login endpoint

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")    """

    try:


@router.post("/register")        auth_service = AuthService(db)
async def register_user(user=auth_service.authenticate_user(

    username: str=Form(...),            credentials.get("email"),

    email: str=Form(...),            credentials.get("password")

    password: str=Form(...),)

    full_name: str = Form(...),

    department: str = Form(...), if not user:

    role: str = Form(default="staff"), raise HTTPException(

    db: Session=Depends(get_db)                status_code=status.HTTP_401_UNAUTHORIZED,

):                detail = "Invalid credentials"

    """Register a new user""")

    # Check if user already exists        access_token = create_access_token(data={"sub": user.email})

    existing_user = db.query(User).filter(

        (User.username == username) | (User.email == email) return {

    ).first()            "access_token": access_token,

                "token_type": "bearer",

    if existing_user:            "user": {

        raise HTTPException("id": user.id,

            status_code=400,                "email": user.email,

            detail="Username or email already registered"                "name": user.name

        )}

            }

    # Create new user    except Exception as e:

    user = User(raise HTTPException(

        username=username,            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

        email=email,            detail=str(e)

        full_name=full_name,)

        department=department,

        role=role, @ router.post("/register")

        is_active=Trueasync def register(user_data: dict, db: Session=Depends(get_db)):

    )    """

    user.set_password(password)    User registration endpoint

        """

    db.add(user) try:

    db.commit()        auth_service = AuthService(db)

    db.refresh(user)        user = auth_service.create_user(

                email=user_data.get("email"),

    logger.info(f"New user registered: {username} ({email})")            password=user_data.get("password"),

                name=user_data.get("name")

    return {)

        "success": True,

        "message": "User registered successfully", return {

        "data": {"message": "User created successfully",

            "user_id": user.id,            "user": {

            "username": user.username,                "id": user.id,

            "email": user.email                "email": user.email,

        }                "name": user.name

    }}

        }


@router.post("/token") except Exception as e:
async def login_for_access_token(raise HTTPException(

    form_data: OAuth2PasswordRequestForm=Depends(),            status_code=status.HTTP_400_BAD_REQUEST,

    db: Session=Depends(get_db)            detail=str(e)

): )
    """Login and get access token"""

    @router.post("/logout")
    # Authenticate userasync def logout(token: str = Depends(security)):
    user = db.query(User).filter(User.username == form_data.username).first()    """

        User logout endpoint

    if not user or not user.verify_password(form_data.password):    """

        raise HTTPException(    # In a real implementation, you might want to blacklist the token

            status_code=status.HTTP_401_UNAUTHORIZED, return {"message": "Logged out successfully"}

            detail="Incorrect username or password",

            headers={"WWW-Authenticate": "Bearer"}, @ router.get("/me")

        )async def get_current_user(token: str=Depends(security), db: Session=Depends(get_db)):

        """

    if not user.is_active:    Get current user information

        raise HTTPException(    """

            status_code = status.HTTP_401_UNAUTHORIZED, try:

            detail = "User account is deactivated"        payload = verify_token(token.credentials)

        )        email = payload.get("sub")



    # Create access token        if email is None:

    access_token_expires = timedelta(minutes=480)  # 8 hours            raise HTTPException(

    access_token= create_access_token(status_code=status.HTTP_401_UNAUTHORIZED,

        data = {"sub": user.username, "user_id": user.id},                detail = "Invalid token"

        expires_delta = access_token_expires)

    )

            user = db.query(User).filter(User.email == email).first()

    # Create session        if user is None:

    session= UserSession(user_id=user.id) raise HTTPException(

    db.add(session)                status_code=status.HTTP_404_NOT_FOUND,

                    detail="User not found"

    # Update user last login            )

    user.last_login=datetime.utcnow()

    user.failed_login_attempts=0 return {

                "id": user.id,

    db.commit()            "email": user.email,

                "name": user.name

    logger.info(f"User logged in: {user.username}")}

        except Exception as e:

    return {raise HTTPException(

        "access_token": access_token,            status_code=status.HTTP_401_UNAUTHORIZED,

        "token_type": "bearer",            detail="Invalid token"

        "expires_in": 28800,  # 8 hours in seconds        )
        "user": user.to_dict()
    }


@router.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Alternative login endpoint"""

    # Authenticate user
    user = db.query(User).filter(User.username == username).first()

    if not user or not user.verify_password(password):
        # Increment failed attempts
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            db.commit()

        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=401,
            detail="Account is temporarily locked due to too many failed attempts"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User account is deactivated"
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )

    # Create session
    session = UserSession(user_id=user.id)
    db.add(session)

    # Update user
    user.last_login = datetime.utcnow()
    user.failed_login_attempts = 0
    user.locked_until = None

    db.commit()

    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user.to_dict()
        }
    }


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Logout and invalidate session"""

    try:
        payload = verify_token(token)
        user_id = payload.get("user_id")

        if user_id:
            # Terminate active sessions
            sessions = db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            ).all()

            for session in sessions:
                session.terminate()

            db.commit()

        return {
            "success": True,
            "message": "Logged out successfully"
        }

    except:
        return {
            "success": True,
            "message": "Logged out"
        }


@router.get("/me")
async def get_current_user_info(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get current user information"""

    try:
        payload = verify_token(token)
        username = payload.get("sub")

        if not username:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        user = db.query(User).filter(User.username == username).first()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )

        return {
            "success": True,
            "data": user.to_dict(include_sensitive=True)
        }

    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


@router.post("/refresh")
async def refresh_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Refresh access token"""

    try:
        payload = verify_token(token)
        username = payload.get("sub")
        user_id = payload.get("user_id")

        if not username or not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.username == username).first()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=401, detail="User not found or inactive")

        # Create new token
        new_token = create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )

        return {
            "success": True,
            "data": {
                "access_token": new_token,
                "token_type": "bearer"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/sessions")
async def get_user_sessions(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get user's active sessions"""

    try:
        payload = verify_token(token)
        user_id = payload.get("user_id")

        sessions = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        ).all()

        return {
            "success": True,
            "data": [session.to_dict() for session in sessions]
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.delete("/sessions/{session_id}")
async def terminate_session(
    session_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Terminate a specific session"""

    try:
        payload = verify_token(token)
        user_id = payload.get("user_id")

        session = db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.user_id == user_id
        ).first()

        if session:
            session.terminate()
            db.commit()

        return {
            "success": True,
            "message": "Session terminated"
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")
