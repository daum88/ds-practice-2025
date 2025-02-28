from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PaymentInfo(_message.Message):
    __slots__ = ("credit_card_number", "expiration_date", "cvv")
    CREDIT_CARD_NUMBER_FIELD_NUMBER: _ClassVar[int]
    EXPIRATION_DATE_FIELD_NUMBER: _ClassVar[int]
    CVV_FIELD_NUMBER: _ClassVar[int]
    credit_card_number: str
    expiration_date: str
    cvv: str
    def __init__(self, credit_card_number: _Optional[str] = ..., expiration_date: _Optional[str] = ..., cvv: _Optional[str] = ...) -> None: ...

class OrderDetails(_message.Message):
    __slots__ = ("books", "total_amount")
    BOOKS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_AMOUNT_FIELD_NUMBER: _ClassVar[int]
    books: _containers.RepeatedScalarFieldContainer[str]
    total_amount: float
    def __init__(self, books: _Optional[_Iterable[str]] = ..., total_amount: _Optional[float] = ...) -> None: ...

class FraudCheckRequest(_message.Message):
    __slots__ = ("transaction_id", "payment", "order", "amount")
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    PAYMENT_FIELD_NUMBER: _ClassVar[int]
    ORDER_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    transaction_id: str
    payment: PaymentInfo
    order: OrderDetails
    amount: float
    def __init__(self, transaction_id: _Optional[str] = ..., payment: _Optional[_Union[PaymentInfo, _Mapping]] = ..., order: _Optional[_Union[OrderDetails, _Mapping]] = ..., amount: _Optional[float] = ...) -> None: ...

class FraudCheckResponse(_message.Message):
    __slots__ = ("is_fraudulent", "message")
    IS_FRAUDULENT_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    is_fraudulent: bool
    message: str
    def __init__(self, is_fraudulent: bool = ..., message: _Optional[str] = ...) -> None: ...
