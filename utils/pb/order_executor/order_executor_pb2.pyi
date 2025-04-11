from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ElectionRequest(_message.Message):
    __slots__ = ("candidate_id",)
    CANDIDATE_ID_FIELD_NUMBER: _ClassVar[int]
    candidate_id: int
    def __init__(self, candidate_id: _Optional[int] = ...) -> None: ...

class ElectionResponse(_message.Message):
    __slots__ = ("ok",)
    OK_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    def __init__(self, ok: bool = ...) -> None: ...

class CoordinatorRequest(_message.Message):
    __slots__ = ("coordinator_id",)
    COORDINATOR_ID_FIELD_NUMBER: _ClassVar[int]
    coordinator_id: int
    def __init__(self, coordinator_id: _Optional[int] = ...) -> None: ...

class HeartbeatRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HeartbeatResponse(_message.Message):
    __slots__ = ("alive", "leader_status")
    ALIVE_FIELD_NUMBER: _ClassVar[int]
    LEADER_STATUS_FIELD_NUMBER: _ClassVar[int]
    alive: bool
    leader_status: str
    def __init__(self, alive: bool = ..., leader_status: _Optional[str] = ...) -> None: ...

class HealthRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: str
    def __init__(self, status: _Optional[str] = ...) -> None: ...
