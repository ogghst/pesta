from typing import Any

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import User, UserCreate, UserUpdate, UserUpdateMe
from app.services.entity_versioning import (
    create_entity_with_version,
    update_entity_with_version,
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    # Ensure entity_id matches the logical identifier for consistency
    if hasattr(db_obj, "entity_id"):
        db_obj.entity_id = db_obj.id
    create_entity_with_version(session=session, entity=db_obj, entity_type="user")
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(
    *, session: Session, db_user: User, user_in: UserUpdate | UserUpdateMe
) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)

    # Handle password hashing
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        user_data["hashed_password"] = hashed_password
        user_data.pop("password", None)

    # Handle OpenAI API key encryption
    from app.core.encryption import encrypt_api_key

    plain_key = user_data.pop("openai_api_key", None)
    if plain_key is not None:  # Explicitly check if key was provided
        if plain_key:
            # Encrypt API key before storage
            user_data["openai_api_key_encrypted"] = encrypt_api_key(plain_key)
        else:
            # Empty string means clear the API key
            user_data["openai_api_key_encrypted"] = None

    updated_user = update_entity_with_version(
        session=session,
        entity_class=User,
        entity_id=db_user.id,
        update_data=user_data,
        entity_type="user",
    )
    session.commit()
    session.refresh(updated_user)
    return updated_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user
