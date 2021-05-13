import requests, json, errors, dateutil.parser

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
            if "error" in req:
                if req["error"] == "get_user_info.isEmpty":
                    raise errors.EmptyUserSearch("The search is empty.")
                elif req["error"] == "get_user_info.InvalidUsername":
                    raise errors.UserNotFound("The user was not found.")
                else:
                    raise errors.UnknownError("API responded with an unrecognized error: " + req["error"])
            else:
                return User(req)
        except json.decoder.JSONDecodeError:
            raise errors.NoJsonResponse("Your API key is invalid or you didn't bind your ip correctly. Or addon is being ddossed")

class User:
    def __init__(self, rjson):
        self.user_id = rjson["user_id"]
        self.username = rjson["username"]
        self.status = rjson["status"]
        self.points = rjson["points"]
        self.register_date = None if rjson["register_date"].startswith("0") else dateutil.parser.parse(rjson["register_date"])
        self.premium_plan = None if rjson["points"] == "none" or not rjson["points"] else rjson["points"]




