from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Book(_message.Message):
    __slots__ = ("title", "author")
    TITLE_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    title: str
    author: str
    def __init__(self, title: _Optional[str] = ..., author: _Optional[str] = ...) -> None: ...

class BookSuggestionsRequest(_message.Message):
    __slots__ = ("order_id", "num_books")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    NUM_BOOKS_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    num_books: int
    def __init__(self, order_id: _Optional[str] = ..., num_books: _Optional[int] = ...) -> None: ...

class BookSuggestionsResponse(_message.Message):
    __slots__ = ("books",)
    BOOKS_FIELD_NUMBER: _ClassVar[int]
    books: _containers.RepeatedCompositeFieldContainer[Book]
    def __init__(self, books: _Optional[_Iterable[_Union[Book, _Mapping]]] = ...) -> None: ...

class OrderInitRequest(_message.Message):
    __slots__ = ("order_id", "order_data")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    ORDER_DATA_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    order_data: str
    def __init__(self, order_id: _Optional[str] = ..., order_data: _Optional[str] = ...) -> None: ...

class OrderInitResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class GenerateSuggestionsRequest(_message.Message):
    __slots__ = ("order_id", "num_books", "vector_clock")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    NUM_BOOKS_FIELD_NUMBER: _ClassVar[int]
    VECTOR_CLOCK_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    num_books: int
    vector_clock: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, order_id: _Optional[str] = ..., num_books: _Optional[int] = ..., vector_clock: _Optional[_Iterable[int]] = ...) -> None: ...

class GenerateSuggestionsResponse(_message.Message):
    __slots__ = ("success", "message", "books", "updated_vc")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    BOOKS_FIELD_NUMBER: _ClassVar[int]
    UPDATED_VC_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    books: _containers.RepeatedCompositeFieldContainer[Book]
    updated_vc: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., books: _Optional[_Iterable[_Union[Book, _Mapping]]] = ..., updated_vc: _Optional[_Iterable[int]] = ...) -> None: ...

class ClearOrderRequest(_message.Message):
    __slots__ = ("order_id", "final_vc")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    FINAL_VC_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    final_vc: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, order_id: _Optional[str] = ..., final_vc: _Optional[_Iterable[int]] = ...) -> None: ...

class ClearOrderResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...
