from bs4 import BeautifulSoup
import requests
from data_handler import DataHandler

COOLDOWN = 6


def olx_checker(url: str) -> int:
    """This function returns current number of offers for a URL"""
    headers_mobile = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X)'
                      ' AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B137 Safari/601.1'}
    response = requests.get(url, headers=headers_mobile)
    soup = BeautifulSoup(response.text, "html.parser")

    offer = soup.find(name="span", class_="css-xkzsoo")
    if offer is not None:
        number_of_offers = int(offer.getText().split()[1])
        return number_of_offers
    else:
        return 0


def message_maker(user_id: str) -> str:
    """This function creates a message that is supposed to be send.
     It checks if the previous number of offers for an item is lower than the current one.
     If so, it concatenates new info to the 'content' string which is returned at the end.
     It contains all the valuable information and will be send as the message to the user."""

    data_handler = DataHandler()
    data = data_handler.get_data_by_id(user_id=user_id)

    content = ""

    for name, values in data.items():
        if values["Counter"] > 0:
            values["Counter"] -= 1
        else:
            previous_number_offer = values["Number"]
            url = values["Url"]
            current_number_offer = olx_checker(url=url)
            if current_number_offer > previous_number_offer:
                content += f"New offers {name}. " \
                           f"Difference {current_number_offer - previous_number_offer} " \
                           f"URL: {url}\n"
            values["Number"] = current_number_offer
            values["Counter"] = COOLDOWN

    data_handler.update_user_data(user_id, new_data=data)

    return content
