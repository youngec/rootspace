# coding:utf-8

"""Docstring"""

import config.generic


class TestConfig(object):
    """
    Test the configuration file.
    """

    def test_runmode(self):
        """
        The RUN_MODE must be a string, either 'debug', 'release' or 'production'.

        :return:
        """

        assert config.generic.RUN_MODE in ("debug", "release", "production")

    def test_log(self):
        """
        All LOG_* variables must be strings.

        :return:
        """

        assert isinstance(config.generic.LOG_DIR, str)
        assert isinstance(config.generic.LOG_FILE, str)
        assert isinstance(config.generic.LOG_FORMAT, str)

    def test_delta_time(self):
        """
        The DELTA_TIME must be a number between 0 and 1. Same goes for FRAME_TIME_MAX and EPS

        :return:
        """

        assert config.generic.DELTA_TIME > 0
        assert config.generic.DELTA_TIME <= 1

        assert config.generic.FRAME_TIME_MAX > 0
        assert config.generic.FRAME_TIME_MAX <= 1

        assert config.generic.EPS > 0
        assert config.generic.EPS <= 1

    def test_sdl_params(self):
        """
        The following SDL2 parameters must be set according to requirements of SDL2.

        :return:
        """

        assert isinstance(config.generic.WINDOW_TITLE, str)

        assert isinstance(config.generic.WINDOW_SHAPE, tuple) and len(config.generic.WINDOW_SHAPE) == 2
        assert all([isinstance(a, int) for a in config.generic.WINDOW_SHAPE])

        assert isinstance(config.generic.RESOURCE_DIR, str)

        assert isinstance(config.generic.CLEAR_COLOR, tuple) and len(config.generic.CLEAR_COLOR) == 4
        assert all([isinstance(a, int) for a in config.generic.CLEAR_COLOR])