import requests, json, errors

class API:
    def __init__(self, key, api_url="https://addon.to/tools/api.php", user_agent="addon.to-beta-api - request v1.0"):
        self.headers = {'User-agent': user_agent}
        self.data = {'apikey': key, 'action': '', 'value': 'admin'}
        self.api_url = api_url
        self.key = key

    def get_user_info(self, user):
        self.data["action"] = "get_user_info"
        req = requests.post(self.api_url, data=self.data)
        try:
            req = req.json()
        except json.decoder.JSONDecodeError:
            raise errors.NoJsonResponse("Your API key is invalid or you didn't bind your ip correctly. Or addon is being ddossed")

class User:
    def __init__(self, rjson):
        self.user_id = rjson["user_id"]


