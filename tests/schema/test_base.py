import pytest
from marshmallow import ValidationError
from opsy.schema import validate_ip


def test_validate_ip():
    # Test invalid IP
    with pytest.raises(ValidationError):
        validate_ip("invalid")
    # Test valid IPv4
    validate_ip("192.168.0.1")
    # Test valid IPv6
    validate_ip("::1")
