from enum import Enum

class Granularity(str, Enum):
    day = "day"
    week = "week"
    month = "month"

class HeadlineSearchSpace(str, Enum):
    headline = "headline"
    headlinewithlead = "headlinewithlead"