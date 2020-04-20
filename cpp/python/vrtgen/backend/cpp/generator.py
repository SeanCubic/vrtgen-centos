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

import os

import jinja2

from vrtgen.model.config import PacketType
from vrtgen.model.field import Scope
from vrtgen.types import enums
from vrtgen.types import struct
from vrtgen.types import prologue
from vrtgen.types import cif0
from vrtgen.types import cif1
from vrtgen.types import control

from vrtgen.backend.generator import Generator, GeneratorOption

from . import types as cpptypes
from .jinja import JINJA_OPTIONS, do_namespace
from .struct import CppStruct

CIFS = (
    cif0.CIF0,
    cif1.CIF1,
)

def optional_type(typename):
    return 'vrtgen::optional<{}>'.format(typename)

def get_enabled_accessors(name):
    identifier = cpptypes.name_to_identifier(name)
    getter = 'is{}Enabled'.format(identifier)
    setter = 'set{}Enabled'.format(identifier)
    return (getter, setter)

def get_accessors(field, name=None):
    if name is None:
        name = field.name
    if struct.is_enable(field):
        return get_enabled_accessors(name)

    identifier = cpptypes.name_to_identifier(name)
    getter = 'get' + identifier
    setter = 'set' + identifier
    return (getter, setter)

class CppPacket:
    def __init__(self, name, packet, header_class):
        self.name = name
        self.helper = name + 'Helper'
        self.namespace = ''
        self.type = cpptypes.enum_value(packet.packet_type_code)
        self.header = {
            'type': 'vrtgen::packing::' + header_class,
            'fields': [],
        }
        self.set_header_field(prologue.Header.packet_type, cpptypes.enum_value(packet.packet_type_code))
        self.set_header_field(prologue.Header.tsi, cpptypes.enum_value(packet.tsi))
        self.set_header_field(prologue.Header.tsf, cpptypes.enum_value(packet.tsf))
        self.set_header_field(
            prologue.Header.class_id_enable,
            str(packet.class_id.is_enabled).lower(),
            getter='isClassIdentifierEnabled',
            setter='setClassIdentifierEnabled',
        )

        self.prologue = []
        self.cam = None
        self.cifs = []
        self.add_cif(0)
        self.add_cif(1)
        self.fields = []
        self.members = []
        self.class_id = None
        self.structs = []

    @property
    def is_variable_length(self):
        return any(field.get('optional', False) for field in self.fields)

    def add_class_id(self, packet):
        self.class_id = self.create_packing_field(packet.class_id, namespaced=False)
        for field in packet.class_id.get_fields():
            if field.is_disabled or field.is_constant:
                continue
            field_type = cpptypes.value_type(field.type)
            self.add_member(field.name, field_type)
        self.prologue.append(self.class_id)

    def add_cif(self, number):
        self.cifs.append({
            'number': number,
            'header': 'vrtgen::packing::CIF{}Enables'.format(number),
            'enabled': False,
        })

    def set_header_field(self, field, value=None, getter=None, setter=None):
        name = cpptypes.name_to_identifier(field.name)
        if getter is None:
            getter = 'get' + name
        if setter is None:
            setter = 'set' + name
        if value is None:
            value = cpptypes.literal(field.value, field.type)
        self.header['fields'].append({
            'name': name,
            'title': field.name,
            'getter': getter,
            'setter': setter,
            'value': value,
        })

    def add_prologue_field(self, field):
        field_type = cpptypes.value_type(field.type)
        self.add_member(field.name, field_type)
        identifier = cpptypes.name_to_identifier(field.name)
        self.prologue.append({
            'name': identifier,
            'type': 'vrtgen::packing::' + identifier
        })

    def create_packing_field(self, field, namespaced=True):
        identifier = cpptypes.name_to_identifier(field.name)
        packing = {
            'name': identifier,
            'title': field.name,
            'attr': field.field.attr,
            'optional': field.is_optional,
        }
        if struct.is_struct(field.type):
            packing['struct'] = True
            packing['fields'] = []
            if field.is_user_defined:
                namespace = self.name + '::'
            else:
                namespace = 'vrtgen::packing::'
            packing['type'] = namespace + cpptypes.name_to_identifier(field.type.__name__)
            for subfield in field.get_fields():
                if subfield.is_disabled:
                    continue
                if namespaced:
                    subfield_name = field.name + subfield.name
                else:
                    subfield_name = subfield.name
                sub_get, sub_set = get_accessors(subfield, name=subfield_name)
                src_get, src_set = get_accessors(subfield, name=subfield.name)
                subfield_dict = {
                    'name': subfield_name,
                    'getter': sub_get,
                    'setter': sub_set,
                    'src': {
                        'getter': src_get,
                        'setter': src_set,
                    },
                    'title': subfield.name,
                }
                if subfield.is_constant:
                    subfield_dict['value'] = cpptypes.literal(subfield.value, subfield.type)
                if subfield.is_optional:
                    subfield_dict['optional'] = True
                    subfield_dict['check'] = sub_get.replace('get', 'has')
                    getter, setter = get_enabled_accessors(subfield.name)
                    subfield_dict['src']['enable'] = {
                        'setter': setter,
                        'getter': getter,
                    }
                packing['fields'].append(subfield_dict)
        else:
            packing['type'] = 'vrtgen::packing::' + identifier
        return packing

    def add_field(self, field):
        cif = self.cifs[CIFS.index(field.field.owner)]
        if not cif['enabled']:
            cif['enabled'] = True

        cif_field = self.create_packing_field(field)
        cif_field['cif'] = cif['number']
        self.fields.append(cif_field)

        if struct.is_struct(field.type):
            for subfield in field.get_fields():
                if subfield.is_disabled or subfield.is_constant:
                    continue
                subfield_name = field.name + ' ' + subfield.name
                self.add_member_from_field(subfield, name=subfield_name)
        else:
            self.add_member_from_field(field)

    def add_member(self, name, datatype, optional=False, value=None):
        identifier = cpptypes.name_to_identifier(name)
        if optional:
            member_type = optional_type(datatype)
        else:
            member_type = datatype

        member = {
            'name': name,
            'identifier': identifier,
            'optional': optional,
            'type': datatype,
            'member': {
                'identifier': 'm_'+identifier,
                'type': member_type,
            },
        }
        if value is not None:
            member['value'] = value
        self.members.append(member)

    def add_member_from_field(self, field, name=None, optional=None):
        if name is None:
            name = field.name
        if field.value is not None:
            value = cpptypes.literal(field.value, field.type)
        else:
            value = None
        if optional is None:
            optional = field.is_optional
        self.add_member(name, cpptypes.value_type(field.type), optional, value)

    def add_cam(self):
        self.cam = {
            'name' : 'ControlAcknowledgeMode',
            'attr': 'cam',
            'type' : 'vrtgen::packing::ControlAcknowledgeMode',
            'struct': True,
            'fields': [],
        }
        self.prologue.append(self.cam)

    def set_cam_field(self, field, value=None):
        assert self.cam is not None
        getter, setter = get_accessors(field)
        cam_field = {
            'name': cpptypes.name_to_identifier(field.name),
            'getter': getter,
            'setter': setter,
            'src': {
                'getter': getter,
                'setter': setter,
            },
            'title': field.name,
        }
        if value is not None:
            cam_field['value'] = cpptypes.literal(value, field.type)
        self.cam['fields'].append(cam_field)

    def add_cam_field(self, field):
        if field.is_optional:
            # In the context of CAM, "optional" fields mean that the value can
            # vary (e.g., warnings might be set or not set on an AckV packet),
            # not that its presence is optional.
            self.add_member_from_field(field, optional=False)
            value = None
        else:
            value = field.value
            if value is None:
                value = field.type()
        self.set_cam_field(field.field, value)

    def add_struct(self, structdef):
        self.structs.append(structdef)

class CppGenerator(Generator):
    """
    Generates C++ packet classes.
    """

    def __init__(self):
        loader = jinja2.PackageLoader(__package__, 'templates')
        self.env = jinja2.Environment(loader=loader, **JINJA_OPTIONS)
        self.env.filters['namespace'] = do_namespace
        self.output_dir = os.getcwd()
        self.header = None
        self.implfile = None
        self.packets = []
        self.namespace = ''

    output_dir = GeneratorOption(
        '--dir',
        doc="output directory for generated files",
        dtype=str
    )

    source_ext = GeneratorOption(
        '--source-ext',
        doc="file extension for source [.cpp]",
        dtype=str,
        defval='cpp'
    )

    header_ext = GeneratorOption(
        '--header-ext',
        doc="file extension for headers [.hpp]",
        dtype=str,
        defval='hpp'
    )

    def start_file(self, filename):
        basename, _ = os.path.splitext(os.path.basename(filename))
        self.header = basename + '.' + self.header_ext
        self.implfile = basename + '.' + self.source_ext

    def end_file(self):
        os.makedirs(self.output_dir, exist_ok=True)
        context = {
            'packets':self.packets,
            'namespace': self.namespace,
        }
        template = self.env.get_template('header.hpp')
        with open(os.path.join(self.output_dir, self.header), 'w') as fp:
            fp.write(template.render(context))

        context['header'] = self.header
        template = self.env.get_template('packet.cpp')
        with open(os.path.join(self.output_dir, self.implfile), 'w') as fp:
            fp.write(template.render(context))

    def generate_prologue(self, cppstruct, packet):
        if not packet.stream_id.is_disabled:
            cppstruct.add_prologue_field(prologue.Prologue.stream_id)

        if not packet.class_id.is_disabled:
            cppstruct.add_class_id(packet)

        if packet.tsi != enums.TSI.NONE:
            cppstruct.add_prologue_field(prologue.Prologue.integer_timestamp)

        if packet.tsf != enums.TSF.NONE:
            cppstruct.add_prologue_field(prologue.Prologue.fractional_timestamp)

    def generate_payload(self, cppstruct, packet):
        for field in packet.get_fields(Scope.CIF0, Scope.CIF1):
            if field.is_disabled:
                continue
            if field.is_user_defined:
                cppstruct.add_struct(CppStruct(field.type))
            cppstruct.add_field(field)

    def generate_data(self, cppstruct, packet):
        cppstruct.set_header_field(prologue.DataHeader.trailer_included, 'false')
        for field in packet.get_fields(Scope.HEADER):
            cppstruct.set_header_field(field)

        self.generate_prologue(cppstruct, packet)

        for field in packet.get_fields(Scope.TRAILER):
            if field.is_disabled:
                continue
            cppstruct.add_member_from_field(field)

    def generate_context(self, cppstruct, packet):
        for field in packet.get_fields(Scope.HEADER):
            cppstruct.set_header_field(field)
        cppstruct.cifs[0]['enabled'] = True

        self.generate_prologue(cppstruct, packet)
        self.generate_payload(cppstruct, packet)

    def generate_command_prologue(self, cppstruct, packet):
        cppstruct.cifs[0]['enabled'] = True

        self.generate_prologue(cppstruct, packet)

        # Add CAM configuration
        cppstruct.add_cam()
        for field in packet.get_fields(Scope.CAM):
            cppstruct.add_cam_field(field)

        cppstruct.add_prologue_field(control.CommandPrologue.message_id)

        controllee_enable = packet.controllee is not None
        cppstruct.set_cam_field(control.ControlAcknowledgeMode.controllee_enable, controllee_enable)
        if controllee_enable:
            cppstruct.set_cam_field(control.ControlAcknowledgeMode.controllee_format, packet.controllee)
            if packet.controllee == enums.IdentifierFormat.WORD:
                cppstruct.add_prologue_field(control.CommandPrologue.controllee_id)
            # TODO: UUID support

        controller_enable = packet.controller is not None
        cppstruct.set_cam_field(control.ControlAcknowledgeMode.controller_enable, controller_enable)
        if controller_enable:
            cppstruct.set_cam_field(control.ControlAcknowledgeMode.controller_format, packet.controller)
            if packet.controller == enums.IdentifierFormat.WORD:
                cppstruct.add_prologue_field(control.CommandPrologue.controller_id)
            # TODO: UUID support

    def generate_control(self, cppstruct, packet):
        cppstruct.set_header_field(prologue.CommandHeader.acknowledge_packet, 'false')
        cppstruct.set_header_field(prologue.CommandHeader.cancellation_packet, 'false')
        self.generate_command_prologue(cppstruct, packet)
        self.generate_payload(cppstruct, packet)

    def generate_acks(self, cppstruct, packet):
        cppstruct.set_header_field(prologue.CommandHeader.acknowledge_packet, 'true')
        cppstruct.set_header_field(prologue.CommandHeader.cancellation_packet, 'false')
        self.generate_command_prologue(cppstruct, packet)
        self.generate_payload(cppstruct, packet)

    def generate_ackvx(self, cppstruct, packet):
        cppstruct.set_header_field(prologue.CommandHeader.acknowledge_packet, 'true')
        cppstruct.set_header_field(prologue.CommandHeader.cancellation_packet, 'false')
        self.generate_command_prologue(cppstruct, packet)
        # Don't include CIFs as-is
        cppstruct.cifs[0]['enabled'] = False
        # TODO: Add warning/error indicators

    def generate(self, packet):
        name = cpptypes.name_to_identifier(packet.name)
        if packet.packet_type == PacketType.DATA:
            model = CppPacket(name, packet, 'DataHeader')
            self.generate_data(model, packet)
        elif packet.packet_type == PacketType.CONTEXT:
            model = CppPacket(name, packet, 'ContextHeader')
            self.generate_context(model, packet)
        elif packet.packet_type == PacketType.CONTROL:
            model = CppPacket(name, packet, 'CommandHeader')
            self.generate_control(model, packet)
        elif packet.packet_type == PacketType.ACKS:
            model = CppPacket(name, packet, 'CommandHeader')
            self.generate_acks(model, packet)
        elif packet.packet_type in (PacketType.ACKV, PacketType.ACKX):
            model = CppPacket(name, packet, 'CommandHeader')
            self.generate_ackvx(model, packet)
        else:
            raise NotImplementedError(packet.packet_type)

        self.packets.append(model)