from enum import Enum


class Tags(Enum):
    work = 1,
    family = 2

    @classmethod
    def has_member(cls, value):
        return value in Tags._member_names_

    @classmethod
    def get_members_list(cls):
        return ', '.join(Tags._member_names_)