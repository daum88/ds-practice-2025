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

class User(_message.Message):
    __slots__ = ("name", "email", "contact", "address_line1", "city", "state", "zip_code", "country")
    NAME_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    CONTACT_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_LINE1_FIELD_NUMBER: _ClassVar[int]
    CITY_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    ZIP_CODE_FIELD_NUMBER: _ClassVar[int]
    COUNTRY_FIELD_NUMBER: _ClassVar[int]
    name: str
    email: str
    contact: str
    address_line1: str
    city: str
    state: str
    zip_code: str
    country: str
    def __init__(self, name: _Optional[str] = ..., email: _Optional[str] = ..., contact: _Optional[str] = ..., address_line1: _Optional[str] = ..., city: _Optional[str] = ..., state: _Optional[str] = ..., zip_code: _Optional[str] = ..., country: _Optional[str] = ...) -> None: ...

class FraudCheckRequest(_message.Message):
    __slots__ = ("transaction_id", "payment", "order", "amount", "user", "creditCard", "userComment", "billingAddress", "shippingMethod", "giftWrapping", "termsAccepted")
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    PAYMENT_FIELD_NUMBER: _ClassVar[int]
    ORDER_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    CREDITCARD_FIELD_NUMBER: _ClassVar[int]
    USERCOMMENT_FIELD_NUMBER: _ClassVar[int]
    BILLINGADDRESS_FIELD_NUMBER: _ClassVar[int]
    SHIPPINGMETHOD_FIELD_NUMBER: _ClassVar[int]
    GIFTWRAPPING_FIELD_NUMBER: _ClassVar[int]
    TERMSACCEPTED_FIELD_NUMBER: _ClassVar[int]
    transaction_id: str
    payment: PaymentInfo
    order: OrderDetails
    amount: float
    user: User
    creditCard: str
    userComment: str
    billingAddress: BillingAddress
    shippingMethod: str
    giftWrapping: bool
    termsAccepted: bool
    def __init__(self, transaction_id: _Optional[str] = ..., payment: _Optional[_Union[PaymentInfo, _Mapping]] = ..., order: _Optional[_Union[OrderDetails, _Mapping]] = ..., amount: _Optional[float] = ..., user: _Optional[_Union[User, _Mapping]] = ..., creditCard: _Optional[str] = ..., userComment: _Optional[str] = ..., billingAddress: _Optional[_Union[BillingAddress, _Mapping]] = ..., shippingMethod: _Optional[str] = ..., giftWrapping: bool = ..., termsAccepted: bool = ...) -> None: ...

class BillingAddress(_message.Message):
    __slots__ = ("street", "city", "state", "zip", "country")
    STREET_FIELD_NUMBER: _ClassVar[int]
    CITY_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    ZIP_FIELD_NUMBER: _ClassVar[int]
    COUNTRY_FIELD_NUMBER: _ClassVar[int]
    street: str
    city: str
    state: str
    zip: str
    country: str
    def __init__(self, street: _Optional[str] = ..., city: _Optional[str] = ..., state: _Optional[str] = ..., zip: _Optional[str] = ..., country: _Optional[str] = ...) -> None: ...

class FraudCheckResponse(_message.Message):
    __slots__ = ("is_fraudulent", "message")
    IS_FRAUDULENT_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    is_fraudulent: bool
    message: str
    def __init__(self, is_fraudulent: bool = ..., message: _Optional[str] = ...) -> None: ...
