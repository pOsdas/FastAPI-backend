from auth_service.core.security import hash_password
from auth_service.core.schemas import AuthUser

# ### fake users db
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

usernames_to_password = {"demo_user": "demo_password"}
static_auth_token_to_username = {
    "90609ed991fcca984411d4b6e1ba7": "demo_user",
}
# ### never do like that
