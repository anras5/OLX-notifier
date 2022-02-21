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
                return "This entry does not exist in your database\." \
                       " Try another one or using ` /add ` to firstly add an item\."

        with open(self.path, "w") as json_file:
            json.dump(data, json_file, indent=4)

        return f'{name} successfully deleted from your database\.'

    def add_user(self, user_id):
        """Allows to add new user to the database"""

        with open(self.path, "r") as json_file:
            data = json.load(json_file)

            if user_id not in data.keys():
                data[user_id] = {}

        with open(self.path, "w") as json_file:
            json.dump(data, json_file, indent=4)
