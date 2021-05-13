class NoJsonResponse(Exception):
    pass

class EmptyUserSearch(Exception):
    pass

class UserNotFound(Exception):
    pass

class PointFormatWrong(Exception):
    pass

class InvalidVoucherFormat(Exception):
    pass

class VoucherAlreadyRedeemed(Exception):
    pass

class NotEnoughPoints(Exception):
    pass

class GiftboxOnCooldown(Exception):
    pass

class UserBanned(Exception):
    pass

class UnknownError(Exception):
    pass
