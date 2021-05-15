import requests, json, dateutil.parser, datetime
import addon.errors
from typing import List, Union


class User:
    """An addon user

    Attributes:
        points (str): The user's points
        premium_plan (str): Their premium plan or None if no premium plan
        register_date (datetime.datetime): The register date or None if they are really OG
        status (str): Their status, either "banned", "user", "mod", "admin"
        user_id (str): Their user id
        username (str): The username
    """

    def __init__(self, rjson, api):
        self.data = api.data
        self.headers = api.headers
        self.api_url = api.api_url
        self.user_id = rjson["user_id"]
        self.username = rjson["username"]
        self.status = rjson["status"]
        self.points = rjson["points"]
        self.register_date = None if rjson["register_date"].startswith("0") else dateutil.parser.parse(
            rjson["register_date"])
        self.premium_plan = None if rjson["premium_plan"] == "none" or not rjson["premium_plan"] else rjson[
            "premium_plan"]

    def send_points(self, points=50, description="") -> bool:
        """Send points to the user

        Args:
            points (int, optional): The amount of points you want to send (default 50)
            description (str, optional): The description with the transaction

        Returns:
            bool: True if successful

        Raises:
            errors.NoJsonResponse: The API didn't respond with a json response
            errors.NotEnoughPoints: You don't have enough points for this transaction
            errors.PointFormatWrong: The points need to be a multiple of 50 and between 50-100k
            errors.UnknownError: The error was not recognized, the response is printed out with the error
            errors.UserBanned: The user you are trying to send points to is banned
        """
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
            raise errors.NoJsonResponse(
                "Your API key is invalid or you didn't bind your ip correctly. Or addon is being ddossed.")

    def __str__(self):
        return self.username


class LoggedIp:
    """A logged ip

    Attributes:
        ip (str): The ip
        user_agent (str): The user agent used to visit the ip logger
    """

    def __init__(self, rjson):
        self.ip = rjson["ip"]
        self.user_agent = rjson["user_agent"]

    def geolocation(self):
        """Get the geolocation of the ip

        Returns:
            dict: A dict with the information about the ip
        """
        return requests.get(f"http://ip-api.com/json/" + self.ip).json()

    def __str__(self):
        return self.ip


class SteamUser:
    """Information about a steam user

    Attributes:
        ip (str): The ip of the steam user
        steam_id (str): The steam id
    """

    def __init__(self, user):
        self.ip = user["ip"]
        self.steam_id = user["steam_id"]

    def geolocation(self):
        """Get the geolocation of the ip

        Returns:
            dict: A dict with the information about the ip
        """
        return requests.get(f"http://ip-api.com/json/" + self.ip).json()

    def __str__(self):
        return self.ip


class Transaction:
    """A transaction

    Attributes:
        description (List[Union[str, bool]]): The description supplied with the transaction or None when no description was supplied
        points (str): The points sent
        sender_id (str): The id of the sender
    """

    def __init__(self, transaction, api):
        self.__api__ = api
        self.sender_id = transaction["from_user_id"]
        self.points = transaction["points"]
        self.description = None if not transaction["description"] else transaction["description"]

    def sender(self) -> User:
        """Returns the User object of the sender

        Returns:
            User: The sender
        """
        return self.__api__.get_user(self.sender_id)

    def __str__(self):
        return self.points


class API:
    """The API object used to communicate with the api
        
    Args:
        key (str): Your addon api key
        api_url (str, optional): The current addon api url
        user_agent (str, optional): The addon user agent
    """

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
            raise errors.NoJsonResponse(
                "Your API key is invalid or you didn't bind your ip correctly. Or addon is being ddossed.")

    def get_user(self, user):
        """Get a user via username or discord id
        
        Args:
            user (str): User search
        
        Returns:
            User: A user object
        
        Raises:
            errors.EmptySearch: The search can't be empty
            errors.UnknownError: The error was not recognized, the response is printed out with the error
            errors.UserNotFound: The searched user was not found
        """
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

    def redeem_voucher(self, voucher: str) -> List[str]:
        """Redeem a voucher
        
        Args:
            voucher (str): The voucher you want to redeem
        
        Returns:
            List[str]: Returns a list with the username and points, respectively
        
        Raises:
            errors.InvalidVoucherFormat: Not a valid voucher format
            errors.UnknownError: The error was not recognized, the response is printed out with the error
            errors.VoucherAlreadyRedeemed: The supplied voucher is already redeemed
        """
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

    def create_voucher(self, points: int) -> str:
        """Create a voucher
        
        Args:
            points (int): The size of the voucher
        
        Returns:
            str: The created voucher
        
        Raises:
            errors.NotEnoughPoints: You don't have enough points to create this voucher
            errors.PointFormatWrong: The points need to be a multiple of 50 and between 50-100k.
            errors.UnknownError: The error was not recognized, the response is printed out with the error
        """
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

    def giftbox(self) -> str:
        """Try to spin the gift box
        
        Returns:
            str: Returns the points you won
        
        Raises:
            errors.GiftboxOnCooldown: The gift box is on cooldown
            errors.UnknownError: The error was not recognized, the response is printed out with the error
        """
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

    def transactions(self, receive_transactions_only=False, send_transactions_only=False) -> List[Transaction]:
        """Get a list of the last 25 transactions
        
        Args:
            receive_transactions_only (bool, optional): Get only the received transactions
            send_transactions_only (bool, optional): Get only the send transactions
        
        Returns:
            List[Transaction]: A list of all the transactions
        
        Raises:
            errors.UnknownError: The error was not recognized, the response is printed out with the error
        """
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

    # def flood_email(self, email: str) -> bool:
    #     """Flood an email address, you need premium+ or 10k points
        
    #     Args:
    #         email (str): The email to flood
        
    #     Returns:
    #         bool: True if it was successful
        
    #     Raises:
    #         errors.NoPremiumPlus: You need premium+ or 10k points
    #         errors.UnknownError: The error was not recognized, the response is printed out with the error
    #     """
    #     data = self.data
    #     data["action"] = "flood_email"
    #     data["email_to_flood"] = email
    #     del data["value"]
    #     req = requests.post(self.api_url, data=data, headers=self.headers)
    #     req = self.__handle_req__(req)
    #     if "error" in req:
    #         if req["error"] == "email_flood.youNeedPremiumPlus":
    #             raise errors.NoPremiumPlus("You need premium plus or 10k points.")
    #         else:
    #             raise errors.UnknownError("API responded with an unrecognized error: " + req["error"])
    #     else:
    #         return True

    # def steam_to_ip(self, search: str) -> List[SteamUser]:
    #     """Search breached/leaked server databases to get an ip from a username or steam id, you need premium+ or 10k points
        
    #     Args:
    #         search (str): A username or ip or steam id
        
    #     Returns:
    #         List[SteamUser]: A list with all the results
        
    #     Raises:
    #         errors.EmptySearch: Your search is empty
    #         errors.NoPremiumPlus: You need premium+ or 10k points
    #         errors.UnknownError: The error was not recognized, the response is printed out with the error
    #     """
    #     if not search:
    #         raise errors.EmptySearch("The search is empty.")
    #     data = self.data
    #     data["action"] = "steam_to_ip"
    #     data["value"] = search
    #     req = requests.post(self.api_url, data=data, headers=self.headers)
    #     req = self.__handle_req__(req)
    #     if "error" in req:
    #         if req["error"] == "steamToIp.premiumPlusRequired":
    #             raise errors.NoPremiumPlus("You need premium plus or 10k points")
    #         else:
    #             raise errors.UnknownError("API responded with an unrecognized error: " + req["error"])
    #     else:
    #         return [SteamUser(user) for user in req["output"]]

    # def create_ip_logger(self, redirect_url="") -> str:
    #     """Create a new ip logger url, you need premium+ or 10k points
        
    #     Args:
    #         redirect_url (str, optional): The redirect url
        
    #     Returns:
    #         str: The ip logger url
        
    #     Raises:
    #         errors.NoPremiumPlus: You need premium or 10k points
    #         errors.UnknownError: The error was not recognized, the response is printed out with the error
    #     """
    #     data = self.data
    #     data["action"] = "ip_logger"
    #     data["value"] = "3"  # generate new link
    #     req = requests.post(self.api_url, data=data, headers=self.headers)
    #     req = self.__handle_req__(req)
    #     if "error" in req:
    #         if req["error"] == "ipLogger.premiumPlusIsRequired":
    #             raise errors.NoPremiumPlus("You need premium plus or 10k points")
    #         else:
    #             raise errors.UnknownError("API responded with an unrecognized error: " + req["error"])
    #     else:
    #         url = req["output"]
    #         if redirect_url:
    #             data["value"] = "5"  # set redirect url
    #             data["url"] = redirect_url
    #             req = requests.post(self.api_url, data=data, headers=self.headers)
    #             req = self.__handle_req__(req)
    #             if "error" in req:
    #                 raise errors.UnknownError("API responded with an unrecognized error: " + req["error"])

    #         return url

    # def ip_logger_url(self) -> str:
    #     """Get the current ip logger url
        
    #     Returns:
    #         str: The corrent ip logger url
        
    #     Raises:
    #         errors.NoPremiumPlus: You need premium or 10k points
    #         errors.UnknownError: The error was not recognized, the response is printed out with the error
    #     """
    #     data = self.data
    #     data["action"] = "ip_logger"
    #     data["value"] = "1"  # get ip logger url
    #     req = requests.post(self.api_url, data=data, headers=self.headers)
    #     req = self.__handle_req__(req)
    #     if "error" in req:
    #         if req["error"] == "ipLogger.premiumPlusIsRequired":
    #             raise errors.NoPremiumPlus("You need premium plus or 10k points")
    #         else:
    #             raise errors.UnknownError("API responded with an unrecognized error: " + req["error"])
    #     else:
    #         return req["output"]

    # def set_ip_logger_redirect(self, redirect_url: str) -> bool:
    #     """Set the redirect for the ip logger
        
    #     Args:
    #         redirect_url (str): The redirect url to redirect to
        
    #     Returns:
    #         bool: True if successful
        
    #     Raises:
    #         errors.NoPremiumPlus: You need premium or 10k points
    #         errors.UnknownError: The error was not recognized, the response is printed out with the error
    #     """
    #     data = self.data
    #     data["value"] = "5"  # set redirect url
    #     data["url"] = redirect_url
    #     req = requests.post(self.api_url, data=data, headers=self.headers)
    #     req = self.__handle_req__(req)
    #     if "error" in req:
    #         if req["error"] == "ipLogger.premiumPlusIsRequired":
    #             raise errors.NoPremiumPlus("You need premium plus or 10k points")
    #         else:
    #             raise errors.UnknownError("API responded with an unrecognized error: " + req["error"])
    #     else:
    #         return True

    # def delete_ip_logs(self) -> bool:
    #     """Delete the logged ips
        
    #     Returns:
    #         bool: True if successful
        
    #     Raises:
    #         errors.NoPremiumPlus: You need premium or 10k points
    #         errors.UnknownError: The error was not recognized, the response is printed out with the error
    #     """
    #     data = self.data
    #     data["value"] = "2"  # delete logged ips
    #     req = requests.post(self.api_url, data=data, headers=self.headers)
    #     req = self.__handle_req__(req)
    #     if "error" in req:
    #         if req["error"] == "ipLogger.premiumPlusIsRequired":
    #             raise errors.NoPremiumPlus("You need premium plus or 10k points")
    #         else:
    #             raise errors.UnknownError("API responded with an unrecognized error: " + req["error"])
    #     else:
    #         return True

    # def get_ip_logs(self) -> List[LoggedIp]:
    #     """Get all logged ips in a list
        
    #     Returns:
    #         List[LoggedIp]: A list with all the logged ips
        
    #     Raises:
    #         errors.NoPremiumPlus: You need premium or 10k points
    #         errors.UnknownError: The error was not recognized, the response is printed out with the error
    #     """
    #     data = self.data
    #     data["value"] = "4"  # get logged ips
    #     req = requests.post(self.api_url, data=data, headers=self.headers)
    #     req = self.__handle_req__(req)
    #     if "error" in req:
    #         if req["error"] == "ipLogger.premiumPlusIsRequired":
    #             raise errors.NoPremiumPlus("You need premium plus or 10k points")
    #         else:
    #             raise errors.UnknownError("API responded with an unrecognized error: " + req["error"])
    #     else:
    #         return [LoggedIp(ip) for ip in req["output"]]
