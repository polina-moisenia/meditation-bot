import os
import json

from data.user_data import UserData


class DataStorage:
    def __init__(self, file_name):
        self.file_name = file_name
        self.data = self.load_data()

    def load_data(self):
        if not os.path.exists(self.file_name):
            self.save_data({})
            return {}

        with open(self.file_name, 'r') as f:
            try:
                raw_data = json.load(f)
                return {int(user_id): UserData.from_dict(info) for user_id, info in raw_data.items()}
            except json.JSONDecodeError:
                return {}

    def save_data(self, data=None):
        if data is None:
            data = self.data
        with open(self.file_name, 'w') as f:
            json.dump({user_id: user_data.to_dict() for user_id, user_data in data.items()}, f, indent=4)

    def get_user(self, user_id):
        return self.data.get(user_id)

    def add_user(self, user_data):
        if user_data.user_id not in self.data:
            self.data[user_data.user_id] = user_data
            self.save_data()

    def get_users_without_training(self, date):
        return [user_data.user_name for user_data in self.data.values() if not user_data.has_done_training(date)]

    def get_all_users(self):
        return [user_data.user_name for user_data in self.data.values()]
