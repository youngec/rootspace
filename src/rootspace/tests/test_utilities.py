# -*- coding: utf-8 -*-

import pytest
import logging
import weakref
import uuid

from rootspace.utilities import underscore_to_camelcase, \
    camelcase_to_underscore, get_log_level, configure_logger, \
    Loggers, to_ref, to_uuid


@pytest.mark.parametrize(("underscore", "camelcase"), (
    ("some_complicated_name", "SomeComplicatedName"),
    ("some_name", "SomeName"),
    ("some", "Some"),
))
def test_case_conversion(underscore, camelcase):
    assert underscore_to_camelcase(underscore) == camelcase
    assert camelcase_to_underscore(camelcase) == underscore


def test_to_ref():
    class SomeClass(object):
        pass

    value = SomeClass()
    wr = weakref.ref(value)
    assert to_ref(wr) is wr
    assert to_ref(None) is None
    assert isinstance(to_ref(value), weakref.ReferenceType)


def test_to_uuid():
    value = uuid.uuid4()
    assert to_uuid(value) is value
    assert to_uuid(str(value)) == value
    assert to_uuid(None) is None


@pytest.mark.parametrize(("verbosity", "expected"), (
    (0, logging.ERROR),
    (1, logging.WARN),
    (2, logging.INFO),
    (3, logging.DEBUG)
))
def test_get_log_level(verbosity, expected):
    assert get_log_level(verbosity) == expected


def test_configure_logger():
    assert isinstance(configure_logger("test", logging.ERROR), Loggers)
