# Copyright (C) 2019 Geon Technologies, LLC
#
# This file is part of vrtgen.
#
# vrtgen is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# vrtgen is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.

from vrtgen.types import enums
from vrtgen.model import config
from vrtgen import parser

def parse_single(document):
    packets = list(parser.parse_stream(document))
    assert len(packets) == 1
    return packets[0]

def test_data_defaults():
    document = """
TestData:
    type: data
"""
    packet = parse_single(document)
    assert packet.name == 'TestData'
    assert packet.packet_type == config.PacketType.DATA
    assert packet.packet_type_code == enums.PacketType.SIGNAL_DATA
    assert packet.tsi == enums.TSI.NONE
    assert packet.tsf == enums.TSF.NONE
    assert packet.stream_id.is_disabled
    assert packet.class_id.is_disabled

def test_data_stream_id():
    document = """
StreamIDTest:
    type: data
    stream id: required
"""
    packet = parse_single(document)
    assert packet.stream_id.is_required
    assert packet.packet_type == config.PacketType.DATA
    assert packet.packet_type_code == enums.PacketType.SIGNAL_DATA_STREAM_ID

def test_context_defaults():
    document = """
TestContext:
    type: context
"""
    packet = parse_single(document)
    assert packet.name == 'TestContext'
    assert packet.packet_type == config.PacketType.CONTEXT
    assert packet.packet_type_code == enums.PacketType.CONTEXT
    assert packet.tsi == enums.TSI.NONE
    assert packet.tsf == enums.TSF.NONE
    assert packet.stream_id.is_mandatory
    assert packet.class_id.is_disabled
    assert packet.timestamp_mode == enums.TSM.FINE

def test_context_timestamp_mode():
    document = """
TSMTest:
    type: context
    timestamp mode: coarse
"""
    packet = parse_single(document)
    assert packet.timestamp_mode == enums.TSM.COARSE

def test_control_defaults():
    document = """
TestControl:
    type: control
"""
    packet = parse_single(document)
    assert packet.name == 'TestControl'
    assert packet.packet_type == config.PacketType.CONTROL
    assert packet.packet_type_code == enums.PacketType.COMMAND
    assert packet.tsi == enums.TSI.NONE
    assert packet.tsf == enums.TSF.NONE
    assert packet.stream_id.is_mandatory
    assert packet.class_id.is_disabled
    assert not packet.ackv.value
    assert not packet.ackx.value
    assert not packet.acks.value

def test_ackv_defaults():
    document = """
TestAckV:
    type: AckV
"""
    packet = parse_single(document)
    assert packet.name == 'TestAckV'
    assert packet.packet_type == config.PacketType.ACKV
    assert packet.packet_type_code == enums.PacketType.COMMAND
    assert packet.tsi == enums.TSI.NONE
    assert packet.tsf == enums.TSF.NONE
    assert packet.stream_id.is_mandatory
    assert packet.class_id.is_disabled
    assert packet.ackv.value
    assert not packet.ackx.value
    assert not packet.acks.value

def test_ackx_defaults():
    document = """
TestAckX:
    type: AckX
"""
    packet = parse_single(document)
    assert packet.name == 'TestAckX'
    assert packet.packet_type == config.PacketType.ACKX
    assert packet.packet_type_code == enums.PacketType.COMMAND
    assert packet.tsi == enums.TSI.NONE
    assert packet.tsf == enums.TSF.NONE
    assert packet.stream_id.is_mandatory
    assert packet.class_id.is_disabled
    assert not packet.ackv.value
    assert packet.ackx.value
    assert not packet.acks.value

def test_acks_defaults():
    document = """
TestAckS:
    type: AckS
"""
    packet = parse_single(document)
    assert packet.name == 'TestAckS'
    assert packet.packet_type == config.PacketType.ACKS
    assert packet.packet_type_code == enums.PacketType.COMMAND
    assert packet.tsi == enums.TSI.NONE
    assert packet.tsf == enums.TSF.NONE
    assert packet.stream_id.is_mandatory
    assert packet.class_id.is_disabled
    assert not packet.ackv.value
    assert not packet.ackx.value
    assert packet.acks.value

def test_timestamp():
    document = """
TimestampTest:
    type: data
    timestamp:
        integer: utc
        fractional: picoseconds
"""
    packet = parse_single(document)
    assert packet.tsi == enums.TSI.UTC
    assert packet.tsf == enums.TSF.REAL_TIME
