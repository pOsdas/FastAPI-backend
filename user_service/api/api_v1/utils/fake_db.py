from datetime import datetime

fake_users_db = {
    1: {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    },
    2: {
        "id": 2,
        "username": "thomas",
        "email": "thomas@example.com",
        "is_active": False,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    },
    # Можно добавить и других пользователей
}
