from auth_service.api.api_v1.utils import helpers
from auth_service.core.schemas import AuthUser

# fake users db

john = AuthUser(
    username="john",
    password=helpers.hash_password("qwerty"),
    email="john@example.com"
)
sam = AuthUser(
    username="sam",
    password=helpers.hash_password("secret"),
)
users_db: dict[str, AuthUser] = {
    john.username: john,
    sam.username: sam,
}