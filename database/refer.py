import pymongo
from info import DATABASE_URI, DATABASE_NAME
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Database connection
try:
    myclient = pymongo.MongoClient(DATABASE_URI)
    mydb = myclient[DATABASE_NAME]
    logger.info("Connected to MongoDB successfully.")
except Exception as e:
    logger.exception("Failed to connect to MongoDB!", exc_info=True)


class UserTracker:
    def __init__(self):
        self.user_collection = mydb["referusers"]
        self.refer_collection = mydb["refers"]

    def add_user(self, user_id: int):
        """Adds a user if they are not already in the list."""
        try:
            if not self.is_user_in_list(user_id):
                self.user_collection.insert_one({'user_id': user_id})
                logger.info(f"User {user_id} added to referusers.")
        except Exception as e:
            logger.exception(f"Error adding user {user_id}!", exc_info=True)

    def remove_user(self, user_id: int):
        """Removes a user from the list."""
        try:
            self.user_collection.delete_one({'user_id': user_id})
            logger.info(f"User {user_id} removed from referusers.")
        except Exception as e:
            logger.exception(f"Error removing user {user_id}!", exc_info=True)

    def is_user_in_list(self, user_id: int) -> bool:
        """Checks if a user is already in the list."""
        try:
            return bool(self.user_collection.find_one({'user_id': user_id}))
        except Exception as e:
            logger.exception(f"Error checking user {user_id}!", exc_info=True)
            return False

    def add_refer_points(self, user_id: int, points: int):
        """Adds points to the user's referral balance."""
        try:
            self.refer_collection.update_one(
                {'user_id': user_id},
                {'$inc': {'points': points}},  # Increments points instead of overwriting
                upsert=True
            )
            logger.info(f"Added {points} points to user {user_id}.")
        except Exception as e:
            logger.exception(f"Error adding points for user {user_id}!", exc_info=True)

    def get_refer_points(self, user_id: int) -> int:
        """Retrieves the referral points for a given user."""
        try:
            user = self.refer_collection.find_one({'user_id': user_id})
            return user.get('points', 0) if user else 0
        except Exception as e:
            logger.exception(f"Error retrieving points for user {user_id}!", exc_info=True)
            return 0


# Initialize the tracker
referdb = UserTracker()
