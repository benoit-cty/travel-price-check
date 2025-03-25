"""
Data models for the flight monitor application
"""
from dataclasses import dataclass

@dataclass
class Travel:
    flight: str
    url: str
    max_price: float