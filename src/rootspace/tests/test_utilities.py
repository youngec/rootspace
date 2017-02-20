# -*- coding: utf-8 -*-

from rootspace.utilities import as_range, slice_length, linearize_indices, normalize_slice


def test_as_range(mocker):
    mocker_normalize_slice = mocker.patch("rootspace.utilities.normalize_slice")
    as_range(slice(None), 0, 100)
    mocker_normalize_slice.assert_called_once_with(slice(None), 0, 100)


def test_slice_length(mocker):
    assert slice_length(slice(None), 0, 100) == 100

    mock_as_range = mocker.patch("rootspace.utilities.as_range")
    slice_length(slice(1, 5, 1), 0, 6)
    mock_as_range.assert_called_once_with(slice(1, 5, 1), 0, 6)


def test_linearize_indices():
    assert linearize_indices((2, 4), 1, 3) == 7


def test_normalize_slice():
    assert normalize_slice(slice(None), 0, 100) == slice(0, 100, 1)
