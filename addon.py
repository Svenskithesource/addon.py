import requests, json, errors, dateutil.parser

class API:
    def __init__(self, key, api_url="https://addon.to/tools/api.php", user_agent="addon.to-beta-api - request v1.0"):
        self.headers = {'User-agent': user_agent}
        self.data = {'apikey': key, 'action': '', 'value': ''}
        self.api_url = api_url
        self.key = key

    def __handle_req__(self, req):
        try:
            req = req.json()
            return req
        except json.decoder.JSONDecodeError:
            raise errors.NoJsonResponse("Your API key is invalid or you didn't bind your ip correctly. Or addon is being ddossed.")

    def get_user(self, user):
        data = self.data
        data["action"] = "get_user_info"
        data["value"] = user
        req = requests.post(self.api_url, data=data, headers=self.headers)
        req = self.__handle_req__(req)
        if "error" in req:
            if req["error"] == "get_user_info.isEmpty":
                raise errors.EmptySearch("The search is empty.")
            elif req["error"] == "get_user_info.InvalidUsername":
                raise errors.UserNotFound("The user was not found.")
            else:
                raise errors.UnknownError("API responded with an unrecognized error: " + req["error"])
        else:
            return User(req, self)


    def redeem_voucher(self, voucher):
        data = self.data
        data["action"] = "redeem_voucher"
        data["value"] = voucher
        req = requests.post(self.api_url, data=data, headers=self.headers)
        req = self.__handle_req__(req)
        if "error" in req:
            if req["error"] == "redeem_voucher.invalidFormat":
                raise errors.InvalidVoucherFormat("Invalid voucher format.")
            elif req["error"] == "redeem_voucher.alreadyInUse":
                raise errors.VoucherAlreadyRedeemed("Voucher is already redeemed!")
            else:
                raise errors.UnknownError("API responded with an unrecognized error: " + req["error"])
        else:
            return [req["msg"].strip().split(" ")[4], req["msg"].strip().split(" ")[-2]]
        

    def create_voucher(self, points):
        if not points or points % 50 or points > 100000 or points < 50:
            raise errors.PointFormatWrong("The points need to be a multiple of 50 and between 50-100k.")
        data = self.data
        data["action"] = "create_voucher"
        data["value"] = str(points)
        req = requests.post(self.api_url, data=data, headers=self.headers)
        if req.text == "null":
            raise errors.NotEnoughPoints(f"You don't have {points} points.")
        req = self.__handle_req__(req)
        if "error" in req:
            if req["error"] == "create_voucher.notEnoughPoints":
                raise errors.NotEnoughPoints(f"You don't have {points} points.")
            else:
                raise errors.UnknownError("API responded with an unrecognized error: " + req["error"])
        else:
            return req["voucher"]


    def giftbox(self):
        data = self.data
        data["action"] = "gift_box"
        del data["value"]
        req = requests.post(self.api_url, data=data, headers=self.headers)
        req = self.__handle_req__(req)
        if "error" in req:
            if req["error"] == "gift_box.12HourCooldown":
                raise errors.GiftboxOnCooldown("Giftbox is on a 12h cooldown.")
            else:
                raise errors.UnknownError("API responded with an unrecognized error: " + req["error"])
        else:
            return req["msg"].split(" ")[-2]


    def get_transactions(self, receive_transactions_only=False, send_transactions_only=False):
        kind = 1 if receive_transactions_only and not send_transactions_only else 2 if send_transactions_only and not receive_transactions_only else 0
        data = self.data
        data["action"] = "get_transactions"
        data["value"] = str(kind)
        req = requests.post(self.api_url, data=data, headers=self.headers)
        req = self.__handle_req__(req)
        if "transactions" not in req:
            raise errors.UnknownError("API responded with an unexpected response: " + req)
        else:
            return [Transaction(transaction, self) for transaction in req["transactions"]]


    def flood_email(self, email):
        data = self.data
        data["action"] = "flood_email"
        data["email_to_flood"] = email
        del data["value"]
        req = requests.post(self.api_url, data=data, headers=self.headers)
        req = self.__handle_req__(req)
        if "error" in req:
            if req["error"] == "email_flood.youNeedPremiumPlus":
                raise errors.NoPremiumPlus("You need premium plus or 10k points.")
            else:
                raise errors.UnknownError("API responded with an unrecognized error: " + req["error"])
        else:
            return True

    def steam_to_ip(self, search):
        if not search:
            raise errors.EmptySearch("The search is empty.")
        data = self.data
        data["action"] = "steam_to_ip"
        data["value"] = search
        req = requests.post(self.api_url, data=data, headers=self.headers)
        req = self.__handle_req__(req)
        if "error" in req:
            if req["error"] == "steamToIp.premiumPlusRequired":
                raise errors.NoPremiumPlus("You need premium plus or 10k points")
            else:
                raise errors.UnknownError("API responded with an unrecognized error: " + req["error"])
        else:
            return [SteamUser(user) for user in req["output"]]
        
class SteamUser:
    def __init__(self, user):
        self.ip = user["ip"]
        self.steam_id = user["steam_id"]

    def geolocation(self):
        return requests.get(f"http://ip-api.com/json/" + self.ip).json()

    def __str__(self):
        return self.ip

class Transaction:
    def __init__(self, transaction, api):
        self.__api__ = api
        self.sender_id = transaction["from_user_id"]
        self.points = transaction["points"]
        self.description = transaction["description"]

    def sender(self):
        return self.api.get_user(sender_id)

    def __str__(self):
        return self.points



class User:
    def __init__(self, rjson, api:API):
        self.data = api.data
        self.headers = api.headers
        self.api_url = api.api_url
        self.user_id = rjson["user_id"]
        self.username = rjson["username"]
        self.status = rjson["status"]
        self.points = rjson["points"]
        self.register_date = None if rjson["register_date"].startswith("0") else dateutil.parser.parse(rjson["register_date"])
        self.premium_plan = None if rjson["points"] == "none" or not rjson["points"] else rjson["points"]


    def send_points(self, points=50, description=""):
        if self.status == "banned":
            raise errors.UserBanned("User is banned.")
        if not points or points % 50 or points > 100000 or points < 50:
            raise errors.PointFormatWrong("The points need to be a multiple of 50 and between 50-100k.")
        data = self.data
        data["action"] = "send_points"
        data["value"] = str(points)
        data["to_user_id"] = str(self.user_id)
        data["description"] = description
        req = requests.post(self.api_url, data=data, headers=self.headers)
        try:
            req = req.json()
            if "error" in req:
                if req["error"] == "send_points.notEnoughPoints":
                    raise errors.NotEnoughPoints(f"You don't have {points} points.")
                else:
                    raise errors.UnknownError("API responded with an unrecognized error: " + req["error"])
            else:
                return True

        except json.decoder.JSONDecodeError:
            raise errors.NoJsonResponse("Your API key is invalid or you didn't bind your ip correctly. Or addon is being ddossed.")

    def __str__(self):
        return self.username
