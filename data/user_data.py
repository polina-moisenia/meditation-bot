class UserData:
    def __init__(self, user_id, user_name):
        self.user_id = user_id
        self.user_name = user_name
        self.trainings = {}

    def mark_training_done(self, date):
        self.trainings[date] = True

    def has_done_training(self, date):
        return self.trainings.get(date, False)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'user_name': self.user_name,
            'trainings': self.trainings
        }

    @staticmethod
    def from_dict(data):
        user_data = UserData(data['user_id'], data['user_name'])
        user_data.trainings = data.get('trainings', {})
        return user_data
