from auth_service.core.security import hash_password
from auth_service.core.schemas import AuthUser

# ### fake users db
john = AuthUser(
    user_id=1,
    username="john",
    password=hash_password("qwerty"),
    email="john@example.com",
    is_active=True,
    refresh_token="dummy_refresh_token"
)

sam = AuthUser(
    user_id=2,
    username="sam",
    password=hash_password("secret"),
    is_active=True,
    refresh_token="second_dummy_refresh_token"
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
