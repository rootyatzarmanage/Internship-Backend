from enum import Enum


class UserStatus(str, Enum):
    ACTIVE = "Active"
    OFFLINE = "Offline"
    DEACTIVE = "Deactive"