# -*- coding: utf-8 -*-

import pytest

from rootspace.utilities import as_range, slice_length, linearize_scalar_indices, normalize_slice, get_sub_shape, \
    linearize_indices


def test_as_range(mocker):
    mocker_normalize_slice = mocker.patch("rootspace.utilities.normalize_slice")
    as_range(slice(None), 0, 100)
    mocker_normalize_slice.assert_called_once_with(slice(None), 0, 100)


def test_slice_length(mocker):
    assert slice_length(slice(None), 0, 100) == 100

    mock_as_range = mocker.patch("rootspace.utilities.as_range")
    slice_length(slice(1, 5, 1), 0, 6)
    mock_as_range.assert_called_once_with(slice(1, 5, 1), 0, 6)


def test_normalize_slice():
    assert normalize_slice(slice(None), 0, 100) == slice(0, 100, 1)


def test_get_sub_shape():
    shape = (4, 4)
    assert get_sub_shape(shape, 4) == (1, 1)
    assert get_sub_shape(shape, 2, 2) == (1, 1)
    assert get_sub_shape(shape, 2, slice(4)) == (1, 4)
    assert get_sub_shape(shape, slice(4), 2) == (4, 1)
    assert get_sub_shape(shape, slice(4), slice(4)) == (4, 4)
    with pytest.raises(TypeError):
        get_sub_shape(shape, None)


def test_linearize_scalar_indices():
    assert linearize_scalar_indices((2, 4), 1, 3) == 7


def test_linearize_indices():
    assert linearize_indices((2, 4), 1, 3) == 7
    assert linearize_indices((2, 4), 1, slice(3)) == slice(4, 7, 1)
    assert linearize_indices((2, 4), slice(2), 1) == slice(1, 6, 4)
