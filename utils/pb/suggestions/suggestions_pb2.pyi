from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class BookSuggestionsRequest(_message.Message):
    __slots__ = ("num_books",)
    NUM_BOOKS_FIELD_NUMBER: _ClassVar[int]
    num_books: int
    def __init__(self, num_books: _Optional[int] = ...) -> None: ...

class BookSuggestionsResponse(_message.Message):
    __slots__ = ("books",)
    BOOKS_FIELD_NUMBER: _ClassVar[int]
    books: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, books: _Optional[_Iterable[str]] = ...) -> None: ...
