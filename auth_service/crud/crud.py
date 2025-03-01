from auth_service.core.security import hash_password
from auth_service.core.schemas import AuthUser

# ### fake users db
john = AuthUser(
    user_id=1,
    password=hash_password("qwerty"),
    email="john@example.com",
    is_active=True,
    refresh_token="dummy_refresh_token"
)

sam = AuthUser(
    user_id=2,
    password=hash_password("secret"),
    is_active=True,
    refresh_token="second_dummy_refresh_token"
)

test = AuthUser(
    user_id=3,
    password=hash_password("test"),
    is_active=True,
    refresh_token="second_dummy_refresh_token"
)

users_db: dict[int, AuthUser] = {
    john.user_id: john,
    sam.user_id: sam,
}
user_id_to_password = {"3": "test"}
static_auth_token_to_user_id = {
    "90609ed991fcca984411d4b6e1ba7": john.user_id,
}
# ### never do like that
