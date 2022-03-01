class LinkCreator:

    def __init__(self):
        self.base = 'https://www.olx.pl/'
        self.price_from = '?search%5Bfilter_float_price%3Afrom%5D='
        self.price_to = '&search%5Bfilter_float_price%3Ato%5D='
        self.distance = 'search%5Bdist%5D='

    def create_link(self, data: dict) -> str:
        """Creates link based on the information provided by user"""
        question_mark = False
        base = self.base

        if 'category' in data:
            base += f'{data["category"]}/'
        if 'location' in data:
            base += f'{data["location"]}/'
        base += f'q-{data["name"].replace(" ", "-")}/'
        if 'price_from' in data and 'price_to' in data:
            base += f'{self.price_from}{data["price_from"]}'
            base += f'{self.price_to}{data["price_to"]}'
            question_mark = True
        if 'distance' in data:
            if question_mark:
                base += f'&{self.distance}{data["distance"]}'
            else:
                base += f'?{self.distance}{data["distance"]}'

        return base
