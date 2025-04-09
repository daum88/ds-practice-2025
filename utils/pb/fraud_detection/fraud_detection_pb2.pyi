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

class FraudCheckRequest(_message.Message):
    __slots__ = ("order_id", "transaction_id", "payment", "amount")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    PAYMENT_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    transaction_id: str
    payment: PaymentInfo
    amount: int
    def __init__(self, order_id: _Optional[str] = ..., transaction_id: _Optional[str] = ..., payment: _Optional[_Union[PaymentInfo, _Mapping]] = ..., amount: _Optional[int] = ...) -> None: ...

class FraudCheckResponse(_message.Message):
    __slots__ = ("is_fraudulent", "message")
    IS_FRAUDULENT_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    is_fraudulent: bool
    message: str
    def __init__(self, is_fraudulent: bool = ..., message: _Optional[str] = ...) -> None: ...

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

class OrderEventRequest(_message.Message):
    __slots__ = ("order_id", "vector_clock")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    VECTOR_CLOCK_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    vector_clock: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, order_id: _Optional[str] = ..., vector_clock: _Optional[_Iterable[int]] = ...) -> None: ...

class OrderEventResponse(_message.Message):
    __slots__ = ("success", "message", "updated_vc")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    UPDATED_VC_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    updated_vc: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., updated_vc: _Optional[_Iterable[int]] = ...) -> None: ...

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
