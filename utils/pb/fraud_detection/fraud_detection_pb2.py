# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: fraud_detection/fraud_detection.proto
# Protobuf Python Version: 4.25.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n%fraud_detection/fraud_detection.proto\x12\x0f\x66raud_detection\"\"\n\x0c\x46raudRequest\x12\x12\n\norder_json\x18\x01 \x01(\t\"&\n\rFraudResponse\x12\x15\n\ris_fraudulent\x18\x01 \x01(\x08\x32]\n\x0e\x46raudDetection\x12K\n\nCheckFraud\x12\x1d.fraud_detection.FraudRequest\x1a\x1e.fraud_detection.FraudResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'fraud_detection.fraud_detection_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_FRAUDREQUEST']._serialized_start=58
  _globals['_FRAUDREQUEST']._serialized_end=92
  _globals['_FRAUDRESPONSE']._serialized_start=94
  _globals['_FRAUDRESPONSE']._serialized_end=132
  _globals['_FRAUDDETECTION']._serialized_start=134
  _globals['_FRAUDDETECTION']._serialized_end=227
# @@protoc_insertion_point(module_scope)
