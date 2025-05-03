from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ReadRequest(_message.Message):
    __slots__ = ("title",)
    TITLE_FIELD_NUMBER: _ClassVar[int]
    title: str
    def __init__(self, title: _Optional[str] = ...) -> None: ...

class ReadResponse(_message.Message):
    __slots__ = ("stock", "version")
    STOCK_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    stock: int
    version: int
    def __init__(self, stock: _Optional[int] = ..., version: _Optional[int] = ...) -> None: ...

class WriteRequest(_message.Message):
    __slots__ = ("title", "new_stock")
    TITLE_FIELD_NUMBER: _ClassVar[int]
    NEW_STOCK_FIELD_NUMBER: _ClassVar[int]
    title: str
    new_stock: int
    def __init__(self, title: _Optional[str] = ..., new_stock: _Optional[int] = ...) -> None: ...

class WriteResponse(_message.Message):
    __slots__ = ("success", "version")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    success: bool
    version: int
    def __init__(self, success: bool = ..., version: _Optional[int] = ...) -> None: ...

class DecrementRequest(_message.Message):
    __slots__ = ("title", "amount")
    TITLE_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    title: str
    amount: int
    def __init__(self, title: _Optional[str] = ..., amount: _Optional[int] = ...) -> None: ...

class CASRequest(_message.Message):
    __slots__ = ("title", "amount", "expect_version")
    TITLE_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    EXPECT_VERSION_FIELD_NUMBER: _ClassVar[int]
    title: str
    amount: int
    expect_version: int
    def __init__(self, title: _Optional[str] = ..., amount: _Optional[int] = ..., expect_version: _Optional[int] = ...) -> None: ...

class DecrementResponse(_message.Message):
    __slots__ = ("success", "stock", "version")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    STOCK_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    success: bool
    stock: int
    version: int
    def __init__(self, success: bool = ..., stock: _Optional[int] = ..., version: _Optional[int] = ...) -> None: ...

class IncrementRequest(_message.Message):
    __slots__ = ("title", "amount")
    TITLE_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    title: str
    amount: int
    def __init__(self, title: _Optional[str] = ..., amount: _Optional[int] = ...) -> None: ...

class IncrementResponse(_message.Message):
    __slots__ = ("success", "stock", "version")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    STOCK_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    success: bool
    stock: int
    version: int
    def __init__(self, success: bool = ..., stock: _Optional[int] = ..., version: _Optional[int] = ...) -> None: ...

class CompareRequest(_message.Message):
    __slots__ = ("title", "threshold")
    TITLE_FIELD_NUMBER: _ClassVar[int]
    THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    title: str
    threshold: int
    def __init__(self, title: _Optional[str] = ..., threshold: _Optional[int] = ...) -> None: ...

class CompareResponse(_message.Message):
    __slots__ = ("enough", "stock")
    ENOUGH_FIELD_NUMBER: _ClassVar[int]
    STOCK_FIELD_NUMBER: _ClassVar[int]
    enough: bool
    stock: int
    def __init__(self, enough: bool = ..., stock: _Optional[int] = ...) -> None: ...
