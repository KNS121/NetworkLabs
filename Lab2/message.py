import time
from typing import Optional
from dataclasses import dataclass
from enum import Enum

class MessageType(Enum):
    HELLO = "HELLO"
    GET_NEIGHBORS = "GET_NEIGHBORS"
    SET_NEIGHBORS = "SET_NEIGHBORS"
    SET_TOPOLOGY = "SET_TOPOLOGY"
    DATA = "DATA"
    DISCONNECT = "DISCONNECT"

@dataclass
class Message:
    sender_id: int
    receiver_id: Optional[int]
    msg_type: MessageType
    data: any
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()