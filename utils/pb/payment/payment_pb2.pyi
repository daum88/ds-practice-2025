from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class PreparePaymentRequest(_message.Message):
    __slots__ = ("id", "user_name", "user_contact", "amount")
    ID_FIELD_NUMBER: _ClassVar[int]
    USER_NAME_FIELD_NUMBER: _ClassVar[int]
    USER_CONTACT_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    id: str
    user_name: str
    user_contact: str
    amount: int
    def __init__(self, id: _Optional[str] = ..., user_name: _Optional[str] = ..., user_contact: _Optional[str] = ..., amount: _Optional[int] = ...) -> None: ...

class PreparePaymentResponse(_message.Message):
    __slots__ = ("ready",)
    READY_FIELD_NUMBER: _ClassVar[int]
    ready: bool
    def __init__(self, ready: bool = ...) -> None: ...

class FinalizePaymentRequest(_message.Message):
    __slots__ = ("id", "abort")
    ID_FIELD_NUMBER: _ClassVar[int]
    ABORT_FIELD_NUMBER: _ClassVar[int]
    id: str
    abort: bool
    def __init__(self, id: _Optional[str] = ..., abort: bool = ...) -> None: ...
