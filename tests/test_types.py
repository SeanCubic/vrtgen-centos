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

import pytest

from vrtgen.types import cif0, cif1
from vrtgen.types import basic

@pytest.mark.parametrize(
    'name,bit',
    [
        ('Context Field Change Indicator', 31),
        ('Reference Point Identifier', 30),
        ('Bandwidth', 29),
        ('IF Reference Frequency', 28),
        ('RF Reference Frequency', 27),
        ('RF Reference Frequency Offset', 26),
        ('IF Band Offset', 25),
        ('Reference Level', 24),
        ('Gain', 23),
        ('Over-range Count', 22),
        ('Sample Rate', 21),
        ('Timestamp Adjustment', 20),
        ('Timestamp Calibration Time', 19),
        ('Temperature', 18),
        ('Device Identifier', 17),
        ('State/Event Indicators', 16),
        ('Signal Data Packet Payload Format', 15),
        ('Formatted GPS', 14),
        ('Formatted INS', 13),
        ('ECEF Ephemeris', 12),
        ('Relative Ephemeris', 11),
        ('Ephemeris Reference ID', 10),
        ('GPS ASCII', 9),
        ('Context Association Lists', 8),
        ('Field Attributes Enable', 7),
        ('CIF 3 Enable', 3),
        ('CIF 2 Enable', 2),
        ('CIF 1 Enable', 1),
    ]
)
def test_cif0_enables(name, bit):
    field = cif0.CIF0.Enables.get_field(name)
    assert field.position.bit == bit

@pytest.mark.parametrize(
    'name,bit',
    [
        ('Phase Offset', 31),
        ('Polarization', 30),
        ('3-D Pointing Vector', 29),
        ('3-D Pointing Vector Structure', 28),
        ('Spatial Scan Type', 27),
        ('Spatial Reference Type', 26),
        ('Beam Widths', 25),
        ('Range', 24),
        ('Eb/No BER', 20),
        ('Threshold', 19),
        ('Compression Point', 18),
        ('Intercept Points', 17),
        ('SNR/Noise Figure', 16),
        ('Aux Frequency', 15),
        ('Aux Gain', 14),
        ('Aux Bandwidth', 13),
        ('Array of CIFS', 11),
        ('Spectrum', 10),
        ('Sector Scan/Step', 9),
        ('Index List', 7),
        ('Discrete I/O 32', 6),
        ('Discrete I/O 64', 5),
        ('Health Status', 4),
        ('V49 Spec Compliance', 3),
        ('Version and Build Code', 2),
        ('Buffer Size', 1),
    ]
)
def test_cif1_enables(name, bit):
    field = cif1.CIF1.Enables.get_field(name)
    assert field.position.bit == bit


NonZero6 = basic.NonZeroSize.create(6)

@pytest.mark.parametrize(
    "value",
    [0, 65]
)
def test_size_range(value):
    with pytest.raises(ValueError):
        NonZero6(value)

@pytest.mark.parametrize(
    "input,expected",
    [ (1, 0), (12, 11), (64, 63)]
)
def test_size_to_binary(input,expected):
    assert NonZero6(input).to_binary() == expected
