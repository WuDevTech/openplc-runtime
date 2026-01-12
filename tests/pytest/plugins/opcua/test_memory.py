"""
Unit tests for OPC-UA memory access functions.

Tests the functions in opcua_memory.py:
- read_memory_direct()
- read_string_direct()
- write_string_direct()
- IEC_STRING structure
"""

import pytest
import ctypes
import sys
from pathlib import Path

# Add plugin path for imports
_plugin_dir = Path(__file__).parent.parent.parent.parent.parent / "core" / "src" / "drivers" / "plugins" / "python"
sys.path.insert(0, str(_plugin_dir / "opcua"))

from opcua_memory import (
    IEC_STRING,
    STR_MAX_LEN,
    STRING_TOTAL_SIZE,
    read_memory_direct,
    read_string_direct,
    write_string_direct,
)


class TestIECStringStructure:
    """Tests for the IEC_STRING ctypes structure."""

    def test_structure_size(self):
        """IEC_STRING should be 127 bytes (1 byte len + 126 bytes body)."""
        assert ctypes.sizeof(IEC_STRING) == STRING_TOTAL_SIZE
        assert ctypes.sizeof(IEC_STRING) == 127

    def test_str_max_len_constant(self):
        """STR_MAX_LEN should be 126."""
        assert STR_MAX_LEN == 126

    def test_structure_fields(self):
        """IEC_STRING should have len and body fields."""
        iec_string = IEC_STRING()
        assert hasattr(iec_string, 'len')
        assert hasattr(iec_string, 'body')

    def test_structure_initialization(self):
        """IEC_STRING should initialize with zeros."""
        iec_string = IEC_STRING()
        assert iec_string.len == 0
        assert all(b == 0 for b in iec_string.body)

    def test_structure_len_field(self):
        """len field should accept int8 values."""
        iec_string = IEC_STRING()
        iec_string.len = 10
        assert iec_string.len == 10

        iec_string.len = 126
        assert iec_string.len == 126

    def test_structure_body_field(self):
        """body field should accept byte values."""
        iec_string = IEC_STRING()
        iec_string.body[0] = ord('H')
        iec_string.body[1] = ord('i')
        assert iec_string.body[0] == ord('H')
        assert iec_string.body[1] == ord('i')


class TestReadStringDirect:
    """Tests for read_string_direct function using simulated memory."""

    def _create_iec_string_in_memory(self, text: str) -> tuple:
        """
        Create an IEC_STRING in memory and return (address, struct).

        Args:
            text: String to store

        Returns:
            Tuple of (memory_address, IEC_STRING_instance)
        """
        iec_string = IEC_STRING()

        # Encode and truncate
        encoded = text.encode('utf-8')[:STR_MAX_LEN]
        iec_string.len = len(encoded)

        # Copy bytes
        for i, b in enumerate(encoded):
            iec_string.body[i] = b

        # Get address
        address = ctypes.addressof(iec_string)
        return address, iec_string

    def test_read_empty_string(self):
        """Should read empty string correctly."""
        address, iec_string = self._create_iec_string_in_memory("")
        result = read_string_direct(address)
        assert result == ""

    def test_read_short_string(self):
        """Should read short string correctly."""
        address, iec_string = self._create_iec_string_in_memory("Hello")
        result = read_string_direct(address)
        assert result == "Hello"

    def test_read_medium_string(self):
        """Should read medium-length string correctly."""
        text = "Hello OPC-UA World!"
        address, iec_string = self._create_iec_string_in_memory(text)
        result = read_string_direct(address)
        assert result == text

    def test_read_max_length_string(self):
        """Should read maximum length string correctly."""
        text = "A" * STR_MAX_LEN
        address, iec_string = self._create_iec_string_in_memory(text)
        result = read_string_direct(address)
        assert result == text
        assert len(result) == STR_MAX_LEN

    def test_read_string_with_spaces(self):
        """Should handle strings with spaces."""
        text = "Hello World Test"
        address, iec_string = self._create_iec_string_in_memory(text)
        result = read_string_direct(address)
        assert result == text

    def test_read_string_with_numbers(self):
        """Should handle strings with numbers."""
        text = "Value: 12345"
        address, iec_string = self._create_iec_string_in_memory(text)
        result = read_string_direct(address)
        assert result == text


class TestWriteStringDirect:
    """Tests for write_string_direct function."""

    def _create_empty_iec_string(self) -> tuple:
        """Create an empty IEC_STRING and return (address, struct)."""
        iec_string = IEC_STRING()
        address = ctypes.addressof(iec_string)
        return address, iec_string

    def test_write_empty_string(self):
        """Should write empty string correctly."""
        address, iec_string = self._create_empty_iec_string()
        result = write_string_direct(address, "")
        assert result is True
        assert iec_string.len == 0

    def test_write_short_string(self):
        """Should write short string correctly."""
        address, iec_string = self._create_empty_iec_string()
        result = write_string_direct(address, "Test")
        assert result is True
        assert iec_string.len == 4
        assert bytes(iec_string.body[:4]) == b"Test"

    def test_write_max_length_string(self):
        """Should write maximum length string correctly."""
        address, iec_string = self._create_empty_iec_string()
        text = "B" * STR_MAX_LEN
        result = write_string_direct(address, text)
        assert result is True
        assert iec_string.len == STR_MAX_LEN

    def test_write_truncates_long_string(self):
        """Should truncate strings longer than STR_MAX_LEN."""
        address, iec_string = self._create_empty_iec_string()
        text = "C" * (STR_MAX_LEN + 50)
        result = write_string_direct(address, text)
        assert result is True
        assert iec_string.len == STR_MAX_LEN

    def test_write_then_read_roundtrip(self):
        """Should support write then read roundtrip."""
        address, iec_string = self._create_empty_iec_string()
        original = "OpenPLC Runtime"

        write_string_direct(address, original)
        result = read_string_direct(address)

        assert result == original


class TestReadMemoryDirectWithString:
    """Tests for read_memory_direct with STRING type (size 127)."""

    def _create_iec_string_in_memory(self, text: str) -> tuple:
        """Create an IEC_STRING in memory."""
        iec_string = IEC_STRING()
        encoded = text.encode('utf-8')[:STR_MAX_LEN]
        iec_string.len = len(encoded)
        for i, b in enumerate(encoded):
            iec_string.body[i] = b
        address = ctypes.addressof(iec_string)
        return address, iec_string

    def test_read_memory_direct_string_size(self):
        """read_memory_direct should handle size 127 as STRING."""
        address, iec_string = self._create_iec_string_in_memory("Direct Test")
        result = read_memory_direct(address, STRING_TOTAL_SIZE)
        assert result == "Direct Test"

    def test_read_memory_direct_string_empty(self):
        """read_memory_direct should handle empty STRING."""
        address, iec_string = self._create_iec_string_in_memory("")
        result = read_memory_direct(address, STRING_TOTAL_SIZE)
        assert result == ""


class TestReadMemoryDirectNumeric:
    """Tests for read_memory_direct with numeric types."""

    def test_read_uint8(self):
        """Should read 1-byte value correctly."""
        value = ctypes.c_uint8(42)
        address = ctypes.addressof(value)
        result = read_memory_direct(address, 1)
        assert result == 42

    def test_read_uint16(self):
        """Should read 2-byte value correctly."""
        value = ctypes.c_uint16(1000)
        address = ctypes.addressof(value)
        result = read_memory_direct(address, 2)
        assert result == 1000

    def test_read_uint32(self):
        """Should read 4-byte value correctly."""
        value = ctypes.c_uint32(100000)
        address = ctypes.addressof(value)
        result = read_memory_direct(address, 4)
        assert result == 100000

    def test_read_uint64(self):
        """Should read 8-byte value correctly."""
        value = ctypes.c_uint64(1000000000)
        address = ctypes.addressof(value)
        result = read_memory_direct(address, 8)
        assert result == 1000000000

    def test_unsupported_size_raises(self):
        """Should raise ValueError for unsupported sizes."""
        value = ctypes.c_uint8(0)
        address = ctypes.addressof(value)

        with pytest.raises(RuntimeError) as exc_info:
            read_memory_direct(address, 3)
        assert "Unsupported variable size" in str(exc_info.value)

        with pytest.raises(RuntimeError) as exc_info:
            read_memory_direct(address, 16)
        assert "Unsupported variable size" in str(exc_info.value)
