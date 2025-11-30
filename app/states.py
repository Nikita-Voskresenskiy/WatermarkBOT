# states.py
class UserState:
    WAITING_FOR_PHOTOS = 1
    WAITING_FOR_TEXT = 2


# User data storage (in production, use a database)
user_data = {}


def init_user_data(user_id):
    """Initialize or reset user data with all required fields"""
    user_data[user_id] = {
        "state": UserState.WAITING_FOR_PHOTOS,
        "photos": [],
        "watermarked_photos": [],
        "watermark_text": None,
    }
