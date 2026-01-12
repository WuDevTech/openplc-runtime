"""
Unit tests for OPC-UA type conversion functions.

Tests the functions in opcua_utils.py:
- map_plc_to_opcua_type()
- convert_value_for_opcua()
- convert_value_for_plc()
- infer_var_type()
"""

import pytest
import struct
import sys
from pathlib import Path

# Add plugin path for imports
_plugin_dir = Path(__file__).parent.parent.parent.parent.parent / "core" / "src" / "drivers" / "plugins" / "python"
sys.path.insert(0, str(_plugin_dir / "opcua"))

from opcua_utils import (
    map_plc_to_opcua_type,
    convert_value_for_opcua,
    convert_value_for_plc,
    infer_var_type,
)
from asyncua import ua


class TestMapPlcToOpcuaType:
    """Tests for map_plc_to_opcua_type function."""

    def test_bool_mapping(self):
        """BOOL should map to Boolean."""
        assert map_plc_to_opcua_type("BOOL") == ua.VariantType.Boolean
        assert map_plc_to_opcua_type("bool") == ua.VariantType.Boolean
        assert map_plc_to_opcua_type("Bool") == ua.VariantType.Boolean

    def test_byte_mapping(self):
        """BYTE should map to Byte."""
        assert map_plc_to_opcua_type("BYTE") == ua.VariantType.Byte
        assert map_plc_to_opcua_type("byte") == ua.VariantType.Byte

    def test_int_mapping(self):
        """INT should map to Int16."""
        assert map_plc_to_opcua_type("INT") == ua.VariantType.Int16
        assert map_plc_to_opcua_type("int") == ua.VariantType.Int16

    def test_dint_mapping(self):
        """DINT should map to Int32."""
        assert map_plc_to_opcua_type("DINT") == ua.VariantType.Int32
        assert map_plc_to_opcua_type("dint") == ua.VariantType.Int32

    def test_int32_mapping(self):
        """INT32 should map to Int32."""
        assert map_plc_to_opcua_type("INT32") == ua.VariantType.Int32
        assert map_plc_to_opcua_type("int32") == ua.VariantType.Int32

    def test_lint_mapping(self):
        """LINT should map to Int64."""
        assert map_plc_to_opcua_type("LINT") == ua.VariantType.Int64
        assert map_plc_to_opcua_type("lint") == ua.VariantType.Int64

    def test_float_mapping(self):
        """FLOAT should map to Float."""
        assert map_plc_to_opcua_type("FLOAT") == ua.VariantType.Float
        assert map_plc_to_opcua_type("float") == ua.VariantType.Float

    def test_real_mapping(self):
        """REAL should map to Float (IEC 61131-3 REAL = 32-bit float)."""
        assert map_plc_to_opcua_type("REAL") == ua.VariantType.Float
        assert map_plc_to_opcua_type("real") == ua.VariantType.Float

    def test_string_mapping(self):
        """STRING should map to String."""
        assert map_plc_to_opcua_type("STRING") == ua.VariantType.String
        assert map_plc_to_opcua_type("string") == ua.VariantType.String

    def test_unknown_type_mapping(self):
        """Unknown types should map to Variant."""
        assert map_plc_to_opcua_type("UNKNOWN") == ua.VariantType.Variant
        assert map_plc_to_opcua_type("CUSTOM") == ua.VariantType.Variant


class TestConvertValueForOpcua:
    """Tests for convert_value_for_opcua function."""

    # BOOL conversions
    def test_bool_from_true(self):
        """True values should convert to True."""
        assert convert_value_for_opcua("BOOL", True) is True
        assert convert_value_for_opcua("BOOL", 1) is True
        assert convert_value_for_opcua("BOOL", 100) is True

    def test_bool_from_false(self):
        """False/zero values should convert to False."""
        assert convert_value_for_opcua("BOOL", False) is False
        assert convert_value_for_opcua("BOOL", 0) is False

    # BYTE conversions
    def test_byte_normal_values(self):
        """Normal byte values should pass through."""
        assert convert_value_for_opcua("BYTE", 0) == 0
        assert convert_value_for_opcua("BYTE", 128) == 128
        assert convert_value_for_opcua("BYTE", 255) == 255

    def test_byte_clamping(self):
        """Byte values should be clamped to 0-255."""
        assert convert_value_for_opcua("BYTE", -1) == 0
        assert convert_value_for_opcua("BYTE", 256) == 255
        assert convert_value_for_opcua("BYTE", 1000) == 255

    # INT conversions
    def test_int_normal_values(self):
        """Normal INT values should pass through."""
        assert convert_value_for_opcua("INT", 0) == 0
        assert convert_value_for_opcua("INT", 1000) == 1000
        assert convert_value_for_opcua("INT", -1000) == -1000

    def test_int_boundary_values(self):
        """INT boundary values should be preserved."""
        assert convert_value_for_opcua("INT", 32767) == 32767
        assert convert_value_for_opcua("INT", -32768) == -32768

    def test_int_clamping(self):
        """INT values outside range should be clamped."""
        assert convert_value_for_opcua("INT", 40000) == 32767
        assert convert_value_for_opcua("INT", -40000) == -32768

    # DINT conversions
    def test_dint_normal_values(self):
        """Normal DINT values should pass through."""
        assert convert_value_for_opcua("DINT", 0) == 0
        assert convert_value_for_opcua("DINT", 100000) == 100000
        assert convert_value_for_opcua("DINT", -100000) == -100000

    def test_dint_boundary_values(self):
        """DINT boundary values should be preserved."""
        assert convert_value_for_opcua("DINT", 2147483647) == 2147483647
        assert convert_value_for_opcua("DINT", -2147483648) == -2147483648

    def test_int32_alias(self):
        """INT32 should behave same as DINT."""
        assert convert_value_for_opcua("INT32", 100000) == 100000
        assert convert_value_for_opcua("Int32", -100000) == -100000

    # LINT conversions
    def test_lint_normal_values(self):
        """Normal LINT values should pass through."""
        assert convert_value_for_opcua("LINT", 0) == 0
        assert convert_value_for_opcua("LINT", 1000000000) == 1000000000
        assert convert_value_for_opcua("LINT", -1000000000) == -1000000000

    def test_lint_large_values(self):
        """Large LINT values should be preserved."""
        assert convert_value_for_opcua("LINT", 9223372036854775807) == 9223372036854775807

    # FLOAT/REAL conversions
    def test_float_from_float(self):
        """Float values should pass through."""
        result = convert_value_for_opcua("FLOAT", 3.14159)
        assert abs(result - 3.14159) < 0.0001

    def test_float_from_int_representation(self):
        """Float stored as int representation should be unpacked."""
        # Pack 3.14159 as int representation
        int_repr = struct.unpack('I', struct.pack('f', 3.14159))[0]
        result = convert_value_for_opcua("FLOAT", int_repr)
        assert abs(result - 3.14159) < 0.0001

    def test_float_zero(self):
        """Zero float should work correctly."""
        assert convert_value_for_opcua("FLOAT", 0.0) == 0.0
        assert convert_value_for_opcua("FLOAT", 0) == 0.0

    def test_float_negative(self):
        """Negative floats should work correctly."""
        result = convert_value_for_opcua("FLOAT", -273.15)
        assert abs(result - (-273.15)) < 0.01

    # REAL conversions (IEC 61131-3 REAL = 32-bit float)
    def test_real_from_float(self):
        """REAL values should pass through as float."""
        result = convert_value_for_opcua("REAL", 3.14159)
        assert abs(result - 3.14159) < 0.0001

    def test_real_from_int_representation(self):
        """REAL stored as int representation should be unpacked."""
        # Pack 3.14159 as int representation
        int_repr = struct.unpack('I', struct.pack('f', 3.14159))[0]
        result = convert_value_for_opcua("REAL", int_repr)
        assert abs(result - 3.14159) < 0.0001

    # STRING conversions
    def test_string_normal(self):
        """String values should pass through."""
        assert convert_value_for_opcua("STRING", "Hello") == "Hello"
        assert convert_value_for_opcua("STRING", "") == ""

    def test_string_from_other_types(self):
        """Non-string values should be converted to string."""
        assert convert_value_for_opcua("STRING", 123) == "123"


class TestConvertValueForPlc:
    """Tests for convert_value_for_plc function."""

    # BOOL conversions
    def test_bool_from_python_bool(self):
        """Python bool should convert to int 0/1."""
        assert convert_value_for_plc("BOOL", True) == 1
        assert convert_value_for_plc("BOOL", False) == 0

    def test_bool_from_int(self):
        """Integer should convert to 0/1."""
        assert convert_value_for_plc("BOOL", 1) == 1
        assert convert_value_for_plc("BOOL", 0) == 0
        assert convert_value_for_plc("BOOL", 100) == 1

    def test_bool_from_string(self):
        """String bool representations should convert."""
        assert convert_value_for_plc("BOOL", "true") == 1
        assert convert_value_for_plc("BOOL", "false") == 0
        assert convert_value_for_plc("BOOL", "1") == 1
        assert convert_value_for_plc("BOOL", "0") == 0

    # BYTE conversions
    def test_byte_normal_values(self):
        """Normal byte values should pass through."""
        assert convert_value_for_plc("BYTE", 0) == 0
        assert convert_value_for_plc("BYTE", 128) == 128
        assert convert_value_for_plc("BYTE", 255) == 255

    def test_byte_clamping(self):
        """Byte values should be clamped to 0-255."""
        assert convert_value_for_plc("BYTE", -1) == 0
        assert convert_value_for_plc("BYTE", 256) == 255

    # INT conversions
    def test_int_normal_values(self):
        """Normal INT values should pass through."""
        assert convert_value_for_plc("INT", 0) == 0
        assert convert_value_for_plc("INT", 1000) == 1000
        assert convert_value_for_plc("INT", -1000) == -1000

    def test_int_clamping(self):
        """INT values outside range should be clamped."""
        assert convert_value_for_plc("INT", 40000) == 32767
        assert convert_value_for_plc("INT", -40000) == -32768

    # DINT conversions
    def test_dint_normal_values(self):
        """Normal DINT values should pass through."""
        assert convert_value_for_plc("DINT", 0) == 0
        assert convert_value_for_plc("DINT", 100000) == 100000
        assert convert_value_for_plc("DINT", -100000) == -100000

    # LINT conversions
    def test_lint_normal_values(self):
        """Normal LINT values should pass through."""
        assert convert_value_for_plc("LINT", 0) == 0
        assert convert_value_for_plc("LINT", 1000000000) == 1000000000

    # FLOAT conversions
    def test_float_to_int_representation(self):
        """Float should be packed to int representation for PLC storage."""
        result = convert_value_for_plc("FLOAT", 3.14159)
        # Verify by unpacking back
        unpacked = struct.unpack('f', struct.pack('I', result))[0]
        assert abs(unpacked - 3.14159) < 0.0001

    def test_float_zero(self):
        """Zero float should pack correctly."""
        result = convert_value_for_plc("FLOAT", 0.0)
        unpacked = struct.unpack('f', struct.pack('I', result))[0]
        assert unpacked == 0.0

    # REAL conversions (IEC 61131-3 REAL = 32-bit float)
    def test_real_to_int_representation(self):
        """REAL should be packed to int representation for PLC storage."""
        result = convert_value_for_plc("REAL", 3.14159)
        # Verify by unpacking back
        unpacked = struct.unpack('f', struct.pack('I', result))[0]
        assert abs(unpacked - 3.14159) < 0.0001

    # STRING conversions
    def test_string_normal(self):
        """String values should pass through."""
        assert convert_value_for_plc("STRING", "Hello") == "Hello"
        assert convert_value_for_plc("STRING", "") == ""


class TestInferVarType:
    """Tests for infer_var_type function."""

    def test_size_1_byte(self):
        """1-byte variables could be BOOL or SINT."""
        assert infer_var_type(1) == "BOOL_OR_SINT"

    def test_size_2_bytes(self):
        """2-byte variables are likely UINT16/INT."""
        assert infer_var_type(2) == "UINT16"

    def test_size_4_bytes(self):
        """4-byte variables could be UINT32, DINT, or TIME."""
        assert infer_var_type(4) == "UINT32_OR_TIME"

    def test_size_8_bytes(self):
        """8-byte variables could be UINT64, LINT, or TIME."""
        assert infer_var_type(8) == "UINT64_OR_TIME"

    def test_size_127_bytes(self):
        """127-byte variables are IEC_STRING (1 byte len + 126 bytes body)."""
        assert infer_var_type(127) == "STRING"

    def test_unknown_size(self):
        """Unknown sizes should return UNKNOWN."""
        assert infer_var_type(3) == "UNKNOWN"
        assert infer_var_type(16) == "UNKNOWN"
        assert infer_var_type(0) == "UNKNOWN"


class TestRoundTripConversions:
    """
    Tests that verify values can be converted from PLC -> OPC-UA -> PLC
    without loss of data (within type constraints).
    """

    def test_bool_roundtrip(self):
        """BOOL values should survive round-trip conversion."""
        for val in [True, False]:
            opcua_val = convert_value_for_opcua("BOOL", int(val))
            plc_val = convert_value_for_plc("BOOL", opcua_val)
            assert plc_val == int(val)

    def test_byte_roundtrip(self):
        """BYTE values should survive round-trip conversion."""
        for val in [0, 1, 127, 128, 255]:
            opcua_val = convert_value_for_opcua("BYTE", val)
            plc_val = convert_value_for_plc("BYTE", opcua_val)
            assert plc_val == val

    def test_int_roundtrip(self):
        """INT values should survive round-trip conversion."""
        for val in [0, 1, -1, 1000, -1000, 32767, -32768]:
            opcua_val = convert_value_for_opcua("INT", val)
            plc_val = convert_value_for_plc("INT", opcua_val)
            assert plc_val == val

    def test_dint_roundtrip(self):
        """DINT values should survive round-trip conversion."""
        for val in [0, 100000, -100000, 2147483647, -2147483648]:
            opcua_val = convert_value_for_opcua("DINT", val)
            plc_val = convert_value_for_plc("DINT", opcua_val)
            assert plc_val == val

    def test_lint_roundtrip(self):
        """LINT values should survive round-trip conversion."""
        for val in [0, 1000000000, -1000000000]:
            opcua_val = convert_value_for_opcua("LINT", val)
            plc_val = convert_value_for_plc("LINT", opcua_val)
            assert plc_val == val

    def test_float_roundtrip(self):
        """FLOAT values should survive round-trip conversion (with float precision)."""
        for val in [0.0, 3.14159, -273.15, 1000000.5]:
            # First convert float to int representation (as stored in PLC)
            int_repr = struct.unpack('I', struct.pack('f', val))[0]
            # Convert to OPC-UA
            opcua_val = convert_value_for_opcua("FLOAT", int_repr)
            # Convert back to PLC
            plc_val = convert_value_for_plc("FLOAT", opcua_val)
            # Unpack and compare
            result = struct.unpack('f', struct.pack('I', plc_val))[0]
            assert abs(result - val) < 0.0001

    def test_real_roundtrip(self):
        """REAL values should survive round-trip conversion (same as FLOAT)."""
        for val in [0.0, 3.14159, -273.15, 1000000.5]:
            # First convert float to int representation (as stored in PLC)
            int_repr = struct.unpack('I', struct.pack('f', val))[0]
            # Convert to OPC-UA
            opcua_val = convert_value_for_opcua("REAL", int_repr)
            # Convert back to PLC
            plc_val = convert_value_for_plc("REAL", opcua_val)
            # Unpack and compare
            result = struct.unpack('f', struct.pack('I', plc_val))[0]
            assert abs(result - val) < 0.0001

    def test_string_roundtrip(self):
        """STRING values should survive round-trip conversion."""
        for val in ["", "Hello", "Test!@#$%", "OpenPLC Runtime"]:
            opcua_val = convert_value_for_opcua("STRING", val)
            plc_val = convert_value_for_plc("STRING", opcua_val)
            assert plc_val == val
