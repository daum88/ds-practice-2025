from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class OrderQueueRequest(_message.Message):
    __slots__ = ("order_id", "priority", "order_data")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    ORDER_DATA_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    priority: int
    order_data: str
    def __init__(self, order_id: _Optional[str] = ..., priority: _Optional[int] = ..., order_data: _Optional[str] = ...) -> None: ...

class OrderQueueResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class OrderQueueOrder(_message.Message):
    __slots__ = ("order_id", "priority", "order_data")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    ORDER_DATA_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    priority: int
    order_data: str
    def __init__(self, order_id: _Optional[str] = ..., priority: _Optional[int] = ..., order_data: _Optional[str] = ...) -> None: ...
