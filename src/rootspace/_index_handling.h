#ifndef INDEX_HANDLING_H
#define INDEX_HANDLING_H
#define PY_SSIZE_T_CLEAN
#include <Python.h>

Py_ssize_t linearize_scalar_indices(Py_ssize_t N, Py_ssize_t M, int transposed, Py_ssize_t i, Py_ssize_t j);

PyObject* li_int_int(Py_ssize_t N, Py_ssize_t M, int transposed, Py_ssize_t i, Py_ssize_t j);

PyObject* li_int_tuple(Py_ssize_t N, Py_ssize_t M, int transposed, Py_ssize_t i, PyObject* j);

PyObject* li_int_slice(Py_ssize_t N, Py_ssize_t M, int transposed, Py_ssize_t i, PyObject* j);

PyObject* li_tuple_int(Py_ssize_t N, Py_ssize_t M, int transposed, PyObject* i, Py_ssize_t j);

PyObject* li_tuple_tuple(Py_ssize_t N, Py_ssize_t M, int transposed, PyObject* i, PyObject* j);

PyObject* li_tuple_slice(Py_ssize_t N, Py_ssize_t M, int transposed, PyObject* i, PyObject* j);

PyObject* li_slice_int(Py_ssize_t N, Py_ssize_t M, int transposed, PyObject* i, Py_ssize_t j);

PyObject* li_slice_tuple(Py_ssize_t N, Py_ssize_t M, int transposed, PyObject* i, PyObject* j);

PyObject* li_slice_slice(Py_ssize_t N, Py_ssize_t M, int transposed, PyObject* i, PyObject* j);

PyObject* get_sub_shape(Py_ssize_t N, Py_ssize_t M, int transposed, PyObject* indices);

PyObject* linearize_indices(Py_ssize_t N, Py_ssize_t M, int transposed, PyObject* indices);

PyObject* complete_indices(PyObject* indices);

PyObject* select_all(Py_ssize_t N, Py_ssize_t M, int transposed);
#endif
