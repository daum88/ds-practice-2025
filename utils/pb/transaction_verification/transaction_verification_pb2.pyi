from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

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

class PaymentInfo(_message.Message):
    __slots__ = ("credit_card_number", "expiration_date", "cvv")
    CREDIT_CARD_NUMBER_FIELD_NUMBER: _ClassVar[int]
    EXPIRATION_DATE_FIELD_NUMBER: _ClassVar[int]
    CVV_FIELD_NUMBER: _ClassVar[int]
    credit_card_number: str
    expiration_date: str
    cvv: str
    def __init__(self, credit_card_number: _Optional[str] = ..., expiration_date: _Optional[str] = ..., cvv: _Optional[str] = ...) -> None: ...

class ShippingInfo(_message.Message):
    __slots__ = ("shippingMethod", "gift_wrapping")
    SHIPPINGMETHOD_FIELD_NUMBER: _ClassVar[int]
    GIFT_WRAPPING_FIELD_NUMBER: _ClassVar[int]
    shippingMethod: str
    gift_wrapping: bool
    def __init__(self, shippingMethod: _Optional[str] = ..., gift_wrapping: bool = ...) -> None: ...

class Book(_message.Message):
    __slots__ = ("name", "quantity", "author")
    NAME_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    name: str
    quantity: int
    author: str
    def __init__(self, name: _Optional[str] = ..., quantity: _Optional[int] = ..., author: _Optional[str] = ...) -> None: ...

class OrderDetails(_message.Message):
    __slots__ = ("books", "total_amount", "comment")
    BOOKS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_AMOUNT_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    books: _containers.RepeatedCompositeFieldContainer[Book]
    total_amount: float
    comment: str
    def __init__(self, books: _Optional[_Iterable[_Union[Book, _Mapping]]] = ..., total_amount: _Optional[float] = ..., comment: _Optional[str] = ...) -> None: ...

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

class TransactionValidationRequest(_message.Message):
    __slots__ = ("transaction_id", "user", "payment", "shippingMethod", "order", "creditCard", "userComment", "items", "billingAddress", "giftWrapping", "termsAccepted", "author")
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    PAYMENT_FIELD_NUMBER: _ClassVar[int]
    SHIPPINGMETHOD_FIELD_NUMBER: _ClassVar[int]
    ORDER_FIELD_NUMBER: _ClassVar[int]
    CREDITCARD_FIELD_NUMBER: _ClassVar[int]
    USERCOMMENT_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    BILLINGADDRESS_FIELD_NUMBER: _ClassVar[int]
    GIFTWRAPPING_FIELD_NUMBER: _ClassVar[int]
    TERMSACCEPTED_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    transaction_id: str
    user: User
    payment: PaymentInfo
    shippingMethod: str
    order: OrderDetails
    creditCard: str
    userComment: str
    items: _containers.RepeatedCompositeFieldContainer[Book]
    billingAddress: BillingAddress
    giftWrapping: bool
    termsAccepted: bool
    author: str
    def __init__(self, transaction_id: _Optional[str] = ..., user: _Optional[_Union[User, _Mapping]] = ..., payment: _Optional[_Union[PaymentInfo, _Mapping]] = ..., shippingMethod: _Optional[str] = ..., order: _Optional[_Union[OrderDetails, _Mapping]] = ..., creditCard: _Optional[str] = ..., userComment: _Optional[str] = ..., items: _Optional[_Iterable[_Union[Book, _Mapping]]] = ..., billingAddress: _Optional[_Union[BillingAddress, _Mapping]] = ..., giftWrapping: bool = ..., termsAccepted: bool = ..., author: _Optional[str] = ...) -> None: ...

class TransactionValidationResponse(_message.Message):
    __slots__ = ("valid", "message")
    VALID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    valid: bool
    message: str
    def __init__(self, valid: bool = ..., message: _Optional[str] = ...) -> None: ...
