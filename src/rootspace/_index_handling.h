#ifndef INDEX_HANDLING_H
#define INDEX_HANDLING_H
#define PY_SSIZE_T_CLEAN
#include <Python.h>

/// For two integral multi-dimensional indices, calculate the corresponding
/// linear index. Raises an IndexError if indices are out of bounds.
Py_ssize_t linearize_scalar_indices(Py_ssize_t N, Py_ssize_t M, int transposed, Py_ssize_t i, Py_ssize_t j);

/// For a tuple of int, tuple[Any], or slice, calculate the shape of the
/// resulting sub-matrix. Raises a TypeError if the indices parameter is not
/// a tuple, a ValueError if its length is lot 2, and a TypeError if its
/// elements are neither int, tuple, or slice.
PyObject* get_sub_shape(Py_ssize_t N, Py_ssize_t M, int transposed, PyObject* indices);

/// For a tuple of int, tuple[int], or slice, calculate the corresponding
/// tuple of linear indices. Raises a TypeError if the indices parameter is
/// not a tuple, a ValueError if its length is not 2, and a TypeError if its
/// elements are neither int, tuple, or slice. Furthermore, raises a TypeError
/// if the elements of a tuple index are not of type int. Uses
/// linearize_scalar_indices(.) internally.
PyObject* linearize_indices(Py_ssize_t N, Py_ssize_t M, int transposed, PyObject* indices);

/// For a given int, tuple[int] or slice, return a corresponding two-tuple of
/// the form (indices, slice(None, None, None)).
PyObject* complete_indices(PyObject* indices);

/// For a given matrix shape and transposition flag, return a tuple of linear
/// indices that select all elements.
PyObject* select_all(Py_ssize_t N, Py_ssize_t M, int transposed);

/// The following functions provide python-level access to the above index
/// handling functions.
PyObject* math_get_sub_shape(PyObject* self, PyObject* args);
PyObject* math_linearize_indices(PyObject* self, PyObject* args);
PyObject* math_complete_indices(PyObject* self, PyObject* args);
PyObject* math_select_all(PyObject* self, PyObject* args);
#endif
