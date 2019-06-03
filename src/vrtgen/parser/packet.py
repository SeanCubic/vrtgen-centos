"""
Parser classes for generating VITA 49 packet configurations from Python
dictionaries.
"""

import logging

from vrtgen.model import config
from vrtgen.types.prologue import Header, ContextHeader, Prologue
from vrtgen.types.trailer import Trailer

from . import field
from .cif import CIFPayloadParser
from .section import SectionParser

def unimplemented_parser(name):
    """
    Creates a parser function that logs a 'not implemented' warning.
    """
    def parser(log, *args):
        # pylint: disable=unused-argument
        log.warn('%s not implemented', name)
    return parser

class TrailerParser(SectionParser):
    """
    Parser for Data Packet Trailer configuration.
    """

TrailerParser.add_field_parser(Trailer.calibrated_time)
TrailerParser.add_field_parser(Trailer.valid_data)
TrailerParser.add_field_parser(Trailer.reference_lock)
TrailerParser.add_field_parser(Trailer.agc_mgc)
TrailerParser.add_field_parser(Trailer.detected_signal)
TrailerParser.add_field_parser(Trailer.spectral_inversion)
TrailerParser.add_field_parser(Trailer.over_range)
TrailerParser.add_field_parser(Trailer.sample_loss)
TrailerParser.add_field_parser(Trailer.sample_frame)
TrailerParser.add_parser(Trailer.user_defined.name, unimplemented_parser('User-defined bits'))
TrailerParser.add_field_parser(Trailer.associated_context_packets)

class PrologueParser(SectionParser):
    """
    Base parser for packet prologue configuration.
    """

PrologueParser.add_field_parser(Prologue.stream_id, alias='Stream ID')
PrologueParser.add_field_parser(Prologue.class_id, field.ClassIDParser(), alias='Class ID')
PrologueParser.add_field_parser(Header.tsi)
PrologueParser.add_field_parser(Header.tsf)
PrologueParser.add_field_parser(Prologue.integer_timestamp)
PrologueParser.add_field_parser(Prologue.fractional_timestamp)

class PacketParser:
    """
    Base class for parsers that create and configure VITA 49 packets.
    """
    def __init__(self, name):
        self.name = name
        self.log = logging.getLogger(name)

    def create_packet(self, name):
        """
        Creates a default packet configuration.
        """
        raise NotImplementedError()

    def _get_parser(self):
        raise NotImplementedError()

    def parse(self, value):
        """
        Creates a packet configuration from a Python dictionary.
        """
        packet = self.create_packet(self.name)
        parser = self._get_parser()
        parser(self.log, packet, value)
        return packet

# Data Packet parser classes

class DataSectionParser(SectionParser):
    """
    Parser for Data Packet configuration sections.
    """

DataSectionParser.add_parser('Prologue', PrologueParser())
DataSectionParser.add_parser('Trailer', TrailerParser())

class DataPacketParser(PacketParser):
    """
    Parser for Data Packet configuration.
    """
    def create_packet(self, name):
        return config.DataPacketConfiguration(name)

    def _get_parser(self):
        return DataSectionParser()

# Context Packet parser classes

class ContextPrologueParser(PrologueParser):
    """
    Parser for context packet prologue configuration.
    """

ContextPrologueParser.add_field_parser(ContextHeader.timestamp_mode)

class ContextSectionParser(SectionParser):
    """
    Parser for Context Packet configuration sections.
    """

ContextSectionParser.add_parser('Prologue', ContextPrologueParser())
ContextSectionParser.add_parser('Payload', CIFPayloadParser())

class ContextPacketParser(PacketParser):
    """
    Parser for Context Packet configuration.
    """
    def create_packet(self, name):
        return config.ContextPacketConfiguration(name)

    def _get_parser(self):
        return ContextSectionParser()

# Command Packet parser classes

class CommandSectionParser(SectionParser):
    """
    Parser for Command Packet configuration sections.
    """

CommandSectionParser.add_parser('Prologue', PrologueParser())
CommandSectionParser.add_parser('Payload', CIFPayloadParser())

class CommandPacketParser(PacketParser):
    """
    Parser for Command Packet configuration.
    """
    def create_packet(self, name):
        return config.CommandPacketConfiguration(name)

    def _get_parser(self):
        return CommandSectionParser()
