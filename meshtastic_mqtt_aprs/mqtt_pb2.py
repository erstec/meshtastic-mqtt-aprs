# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: mqtt.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import meshtastic_mqtt_aprs.mesh_pb2 as mesh__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='mqtt.proto',
  package='',
  syntax='proto3',
  serialized_options=b'\n\023com.geeksville.meshB\nMQTTProtosH\003Z!github.com/meshtastic/gomeshproto',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\nmqtt.proto\x1a\nmesh.proto\"V\n\x0fServiceEnvelope\x12\x1b\n\x06packet\x18\x01 \x01(\x0b\x32\x0b.MeshPacket\x12\x12\n\nchannel_id\x18\x02 \x01(\t\x12\x12\n\ngateway_id\x18\x03 \x01(\tBF\n\x13\x63om.geeksville.meshB\nMQTTProtosH\x03Z!github.com/meshtastic/gomeshprotob\x06proto3'
  ,
  dependencies=[mesh__pb2.DESCRIPTOR,])




_SERVICEENVELOPE = _descriptor.Descriptor(
  name='ServiceEnvelope',
  full_name='ServiceEnvelope',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='packet', full_name='ServiceEnvelope.packet', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='channel_id', full_name='ServiceEnvelope.channel_id', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='gateway_id', full_name='ServiceEnvelope.gateway_id', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=26,
  serialized_end=112,
)

_SERVICEENVELOPE.fields_by_name['packet'].message_type = mesh__pb2._MESHPACKET
DESCRIPTOR.message_types_by_name['ServiceEnvelope'] = _SERVICEENVELOPE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

ServiceEnvelope = _reflection.GeneratedProtocolMessageType('ServiceEnvelope', (_message.Message,), {
  'DESCRIPTOR' : _SERVICEENVELOPE,
  '__module__' : 'mqtt_pb2'
  # @@protoc_insertion_point(class_scope:ServiceEnvelope)
  })
_sym_db.RegisterMessage(ServiceEnvelope)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
