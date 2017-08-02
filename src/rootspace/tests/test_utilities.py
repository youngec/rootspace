# -*- coding: utf-8 -*-

import pytest
import logging

from rootspace.utilities import get_log_level, configure_logger


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
