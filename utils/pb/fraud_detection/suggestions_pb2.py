# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: suggestions.proto
# Protobuf Python Version: 4.25.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x11suggestions.proto\x12\x0bsuggestions\",\n\tOrderData\x12\x0f\n\x07orderId\x18\x01 \x01(\t\x12\x0e\n\x06userId\x18\x02 \x01(\t\"@\n\x13SuggestionsResponse\x12)\n\x0esuggestedBooks\x18\x01 \x03(\x0b\x32\x11.suggestions.Book\"5\n\x04\x42ook\x12\x0e\n\x06\x62ookId\x18\x01 \x01(\t\x12\r\n\x05title\x18\x02 \x01(\t\x12\x0e\n\x06\x61uthor\x18\x03 \x01(\t2Y\n\x0bSuggestions\x12J\n\x0eGetSuggestions\x12\x16.suggestions.OrderData\x1a .suggestions.SuggestionsResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'suggestions_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_ORDERDATA']._serialized_start=34
  _globals['_ORDERDATA']._serialized_end=78
  _globals['_SUGGESTIONSRESPONSE']._serialized_start=80
  _globals['_SUGGESTIONSRESPONSE']._serialized_end=144
  _globals['_BOOK']._serialized_start=146
  _globals['_BOOK']._serialized_end=199
  _globals['_SUGGESTIONS']._serialized_start=201
  _globals['_SUGGESTIONS']._serialized_end=290
# @@protoc_insertion_point(module_scope)
