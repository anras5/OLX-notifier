import json


class DataHandler:

    def __init__(self):
        self.path = "data.json"

    def get_all_data(self):
        """Allows to get all the data in data.json"""
        with open(self.path, "r") as json_file:
            data = json.load(json_file)
        return data

    def get_data_by_id(self, user_id):
        """Allows to get data for a particular user identified by their user id on Telegram"""
        with open(self.path, "r") as json_file:
            data = json.load(json_file)
        return data[str(user_id)]

    def is_user_in_database(self, user_id):
        """Returns True if user is in database -> if not returns False"""
        with open(self.path, "r") as json_file:
            data = json.load(json_file)
            return str(user_id) in data

    def update_user_data(self, user_id, new_data):
        """Allows to upload new data for a particular user identified by their user id on Telegram"""
        with open(self.path, "r") as json_file:
            old_data = json.load(json_file)

            old_data[str(user_id)] = new_data

        with open(self.path, "w") as json_file:
            json.dump(old_data, json_file, indent=4)

    def delete_data(self, user_id, name):
        """Allows to the delete a particular name from the user's dictionary"""
        with open(self.path, "r") as json_file:
            data = json.load(json_file)

            try:
                del data[str(user_id)][name]
            except KeyError:
                return "This item does not exist on your list." \
                       " Try another one or using /add to add the item first."

        with open(self.path, "w") as json_file:
            json.dump(data, json_file, indent=4)

        return f'{name} successfully deleted from your list.'

    def add_user(self, user_id):
        """Allows to add new user to the database"""

        with open(self.path, "r") as json_file:
            data = json.load(json_file)

            data[str(user_id)] = {}

        with open(self.path, "w") as json_file:
            json.dump(data, json_file, indent=4)
