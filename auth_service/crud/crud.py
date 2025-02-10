from auth_service.core.security import hash_password
from auth_service.core.schemas import AuthUser

# fake users db

john = AuthUser(
    username="john",
    password=hash_password("qwerty"),
    email="john@example.com"
)
sam = AuthUser(
    username="sam",
    password=hash_password("secret"),
)
users_db: dict[str, AuthUser] = {
    john.username: john,
    sam.username: sam,
}