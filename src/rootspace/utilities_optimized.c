#define PY_SSIZE_T_CLEAN

#include <Python.h>

static Py_ssize_t linearize_scalar_indices(Py_ssize_t shape_i, Py_ssize_t shape_j, Py_ssize_t i, Py_ssize_t j) {
    return i * shape_j + j;
}

static PyObject* li_int_int(Py_ssize_t shape_i, Py_ssize_t shape_j, Py_ssize_t i, Py_ssize_t j) {
    Py_ssize_t lin_idx = linearize_scalar_indices(shape_i, shape_j, i, j);
    return Py_BuildValue("(n)", lin_idx);
}

static PyObject* li_int_tuple(Py_ssize_t shape_i, Py_ssize_t shape_j, Py_ssize_t i, PyObject* j) {
    Py_ssize_t length = PyTuple_Size(j);
    PyObject* r = PyTuple_New(length);

    Py_ssize_t r_idx;
    for (r_idx = 0; r_idx < length; r_idx++) {
        PyObject* j_element = PyTuple_GetItem(j, r_idx);
        if (PyLong_Check(j_element)) {
            Py_ssize_t j_element_value = PyLong_AsSsize_t(j_element);
            Py_ssize_t lin_idx = linearize_scalar_indices(shape_i, shape_j, i, j_element_value);
            PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
        } else {
            PyErr_SetString(PyExc_TypeError, "Expected integers as tuple elements.");
            return NULL;
        }
    }

    return r;
}

static PyObject* li_int_slice(Py_ssize_t shape_i, Py_ssize_t shape_j, Py_ssize_t i, PyObject* j) {
    Py_ssize_t start = 0;
    Py_ssize_t stop = shape_j;
    Py_ssize_t step = 1;
    Py_ssize_t length = shape_j;

    if (PySlice_GetIndicesEx(j, shape_j, &start, &stop, &step, &length) < 0) {
        return NULL;
    }

    PyObject* r = PyTuple_New(length);

    Py_ssize_t r_idx;
    for (r_idx = 0; r_idx < length; r_idx++) {
        Py_ssize_t j_idx = r_idx * step + start;
        Py_ssize_t lin_idx = linearize_scalar_indices(shape_i, shape_j, i, j_idx);
        PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
    }

    return r;
}

static PyObject* li_tuple_int(Py_ssize_t shape_i, Py_ssize_t shape_j, PyObject* i, Py_ssize_t j) {
    Py_ssize_t length = PyTuple_Size(i);
    PyObject* r = PyTuple_New(length);

    Py_ssize_t r_idx;
    for (r_idx = 0; r_idx < length; r_idx++) {
        PyObject* i_element = PyTuple_GetItem(i, r_idx);
        if (PyLong_Check(i_element)) {
            Py_ssize_t i_element_value = PyLong_AsSsize_t(i_element);
            Py_ssize_t lin_idx = linearize_scalar_indices(shape_i, shape_j, i_element_value, j);
            PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
        } else {
            PyErr_SetString(PyExc_TypeError, "Expected integers as tuple elements.");
            return NULL;
        }
    }

    return r;
}

static PyObject* li_tuple_tuple(Py_ssize_t shape_i, Py_ssize_t shape_j, PyObject* i, PyObject* j) {
    Py_ssize_t i_len = PyTuple_Size(i);
    Py_ssize_t j_len = PyTuple_Size(j);
    Py_ssize_t length = i_len * j_len;
    PyObject* r = PyTuple_New(length);

    Py_ssize_t i_idx;
    for (i_idx = 0; i_idx < i_len; i_idx++) {
        PyObject* i_element = PyTuple_GetItem(i, i_idx);
        if (PyLong_Check(i_element)) {
            Py_ssize_t i_element_value = PyLong_AsSsize_t(i_element);
            Py_ssize_t j_idx;
            for (j_idx = 0; j_idx < j_len; j_idx++) {
                PyObject* j_element = PyTuple_GetItem(j, j_idx);
                if (PyLong_Check(j_element)) {
                    Py_ssize_t j_element_value = PyLong_AsSsize_t(j_element);
                    Py_ssize_t lin_idx = linearize_scalar_indices(shape_i, shape_j, i_element_value, j_element_value);
                    Py_ssize_t r_idx = linearize_scalar_indices(i_len, j_len, i_idx, j_idx);
                    PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
                } else {
                    PyErr_SetString(PyExc_TypeError, "Expected integers as tuple elements.");
                    return NULL;
                }
            }
        } else {
            PyErr_SetString(PyExc_TypeError, "Expected integers as tuple elements.");
            return NULL;
        }
    }

    return r;
}

static PyObject* li_tuple_slice(Py_ssize_t shape_i, Py_ssize_t shape_j, PyObject* i, PyObject* j) {
    Py_ssize_t i_len = PyTuple_Size(i);
    Py_ssize_t j_start = 0;
    Py_ssize_t j_stop = shape_j;
    Py_ssize_t j_step = 1;
    Py_ssize_t j_len = shape_j;

    if (PySlice_GetIndicesEx(j, shape_j, &j_start, &j_stop, &j_step, &j_len) < 0) {
        return NULL;
    }

    PyObject* r = PyTuple_New(i_len * j_len);

    Py_ssize_t i_idx;
    for (i_idx = 0; i_idx < i_len; i_idx++) {
        PyObject* i_element = PyTuple_GetItem(i, i_idx);
        if (PyLong_Check(i_element)) {
            Py_ssize_t i_element_value = PyLong_AsSsize_t(i_element);
            Py_ssize_t j_idx;
            for (j_idx = 0; j_idx < j_len; j_idx++) {
                Py_ssize_t j_element_value = j_idx * j_step + j_start;
                Py_ssize_t lin_idx = linearize_scalar_indices(shape_i, shape_j, i_element_value, j_element_value);
                Py_ssize_t r_idx = linearize_scalar_indices(i_len, j_len, i_idx, j_idx);
                PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
            }
        } else {
            PyErr_SetString(PyExc_TypeError, "Expected integers as tuple elements.");
            return NULL;
        }
    }

    return r;
}

static PyObject* li_slice_int(Py_ssize_t shape_i, Py_ssize_t shape_j, PyObject* i, Py_ssize_t j) {
    Py_ssize_t start = 0;
    Py_ssize_t stop = shape_i;
    Py_ssize_t step = 1;
    Py_ssize_t length = shape_i;

    if (PySlice_GetIndicesEx(i, shape_i, &start, &stop, &step, &length) < 0) {
        return NULL;
    }

    PyObject* r = PyTuple_New(length);

    Py_ssize_t r_idx;
    for (r_idx = 0; r_idx < length; r_idx++) {
        Py_ssize_t i_idx = r_idx * step + start;
        Py_ssize_t lin_idx = linearize_scalar_indices(shape_i, shape_j, i_idx, j);
        PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
    }

    return r;
}

static PyObject* li_slice_tuple(Py_ssize_t shape_i, Py_ssize_t shape_j, PyObject* i, PyObject* j) {
    Py_ssize_t i_start = 0;
    Py_ssize_t i_stop = shape_i;
    Py_ssize_t i_step = 1;
    Py_ssize_t i_len = shape_i;
    Py_ssize_t j_len = PyTuple_Size(j);

    if (PySlice_GetIndicesEx(i, shape_i, &i_start, &i_stop, &i_step, &i_len) < 0) {
        return NULL;
    }

    PyObject* r = PyTuple_New(i_len * j_len);

    Py_ssize_t i_idx;
    for (i_idx = 0; i_idx < i_len; i_idx++) {
        Py_ssize_t i_element_value = i_idx * i_step + i_start;
        Py_ssize_t j_idx;
        for (j_idx = 0; j_idx < j_len; j_idx++) {
            PyObject* j_element = PyTuple_GetItem(j, j_idx);
            if (PyLong_Check(j_element)) {
                Py_ssize_t j_element_value = PyLong_AsSsize_t(j_element);
                Py_ssize_t lin_idx = linearize_scalar_indices(shape_i, shape_j, i_element_value, j_element_value);
                Py_ssize_t r_idx = linearize_scalar_indices(i_len, j_len, i_idx, j_idx);
                PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
            } else {
                PyErr_SetString(PyExc_TypeError, "Expected integers as tuple elements.");
                return NULL;
            }
        }
    }

    return r;

}

static PyObject* li_slice_slice(Py_ssize_t shape_i, Py_ssize_t shape_j, PyObject* i, PyObject* j) {
    Py_ssize_t i_start = 0;
    Py_ssize_t i_stop = shape_i;
    Py_ssize_t i_step = 1;
    Py_ssize_t i_len = shape_i;
    Py_ssize_t j_start = 0;
    Py_ssize_t j_stop = shape_j;
    Py_ssize_t j_step = 1;
    Py_ssize_t j_len = shape_j;

    if (PySlice_GetIndicesEx(i, shape_i, &i_start, &i_stop, &i_step, &i_len) < 0) {
        return NULL;
    }

    if (PySlice_GetIndicesEx(j, shape_j, &j_start, &j_stop, &j_step, &j_len) < 0) {
        return NULL;
    }

    PyObject* r = PyTuple_New(i_len * j_len);

    Py_ssize_t i_idx;
    for (i_idx = 0; i_idx < i_len; i_idx++) {
        Py_ssize_t i_element_value = i_idx * i_step + i_start;
        Py_ssize_t j_idx;
        for (j_idx = 0; j_idx < j_len; j_idx++) {
            Py_ssize_t j_element_value = j_idx * j_step + j_start;
            Py_ssize_t lin_idx = linearize_scalar_indices(shape_i, shape_j, i_element_value, j_element_value);
            Py_ssize_t r_idx = linearize_scalar_indices(i_len, j_len, i_idx, j_idx);
            PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
        }
    }

    return r;
}

static PyObject* utilities_get_sub_shape(PyObject* self, PyObject* args) {
    Py_ssize_t shape_i = 0;
    Py_ssize_t shape_j = 0;
    PyObject* indices = NULL;

    if (!PyArg_ParseTuple(args, "(nn)O!", &shape_i, &shape_j, &PyTuple_Type, &indices)) {
        return NULL;
    }

    Py_ssize_t idx_len = PyTuple_Size(indices);
    if (idx_len != 2) {
        PyErr_SetString(PyExc_ValueError, "The number of multidimensional indices is not 2.");
        return NULL;
    }

    PyObject* result = PyTuple_New(idx_len);
    Py_ssize_t idx;
    for (idx = 0; idx < idx_len; idx++) {
        Py_ssize_t shape = 1;
        if (idx == 0) {
            shape = shape_i;
        } else if (idx == 1) {
            shape = shape_j;
        }

        PyObject* i = PyTuple_GetItem(indices, idx);
        if (i == NULL) {
            return NULL;
        } else if (PyLong_Check(i)) {
            PyTuple_SetItem(result, idx, PyLong_FromSsize_t(1));
        } else if (PyTuple_Check(i)) {
            PyTuple_SetItem(result, idx, PyLong_FromSsize_t(PyTuple_Size(i)));
        } else if (PySlice_Check(i)) {
            Py_ssize_t i_start = 0;
            Py_ssize_t i_stop = shape;
            Py_ssize_t i_step = 1;
            Py_ssize_t i_len = shape;
            if (PySlice_GetIndicesEx(i, shape, &i_start, &i_stop, &i_step, &i_len) < 0) {
                return NULL;
            }
            PyTuple_SetItem(result, idx, PyLong_FromSsize_t(i_len));
        } else {
            PyErr_SetString(PyExc_TypeError, "Expected the indices to be either int, tuple or slice.");
            return NULL;
        }
    }

    if (result == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "Unknown error in get_sub_shape().");
    }

    return result;
}

static PyObject* utilities_linearize_indices(PyObject* self, PyObject* args) {
    Py_ssize_t shape_i = 0;
    Py_ssize_t shape_j = 0;
    PyObject* indices = NULL;
    PyObject* result = NULL;

    if (!PyArg_ParseTuple(args, "(nn)O!", &shape_i, &shape_j, &PyTuple_Type, &indices)) {
        return NULL;
    }

    PyObject* i = PyTuple_GetItem(indices, 0);
    PyObject* j = PyTuple_GetItem(indices, 1);

    if (i == NULL || j == NULL) {
        return NULL;
    }

    int i_is_int = PyLong_Check(i);
    int i_is_tuple = PyTuple_Check(i);
    int i_is_slice = PySlice_Check(i);
    int j_is_int = PyLong_Check(j);
    int j_is_tuple = PyTuple_Check(j);
    int j_is_slice = PySlice_Check(j);

    if (i_is_int && j_is_int) {
        result = li_int_int(shape_i, shape_j, PyLong_AsSsize_t(i), PyLong_AsSsize_t(j));
    } else if (i_is_int && j_is_tuple) {
        result = li_int_tuple(shape_i, shape_j, PyLong_AsSsize_t(i), j);
    } else if (i_is_int && j_is_slice) {
        result = li_int_slice(shape_i, shape_j, PyLong_AsSsize_t(i), j);
    } else if (i_is_tuple && j_is_int) {
        result = li_tuple_int(shape_i, shape_j, i, PyLong_AsSsize_t(j));
    } else if (i_is_tuple && j_is_tuple) {
        result = li_tuple_tuple(shape_i, shape_j, i, j);
    } else if (i_is_tuple && j_is_slice) {
        result = li_tuple_slice(shape_i, shape_j, i, j);
    } else if (i_is_slice && j_is_int) {
        result = li_slice_int(shape_i, shape_j, i, PyLong_AsSsize_t(j));
    } else if (i_is_slice && j_is_tuple) {
        result = li_slice_tuple(shape_i, shape_j, i, j);
    } else if (i_is_slice && j_is_slice) {
        result = li_slice_slice(shape_i, shape_j, i, j);
    } else {
        PyErr_SetString(PyExc_TypeError, "Expected the indices to be either int, tuple or slice.");
        return NULL;
    }

    if (result == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "Unknown error in linearize_indices().");
    }

    return result;
}

static PyMethodDef UtilitiesMethods[] = {
    {"get_sub_shape", utilities_get_sub_shape, METH_VARARGS, "For a given multi-dimensional index, return the shape of the resulting sub-matrix."},
    {"linearize_indices", utilities_linearize_indices, METH_VARARGS, "For a given multi-dimensional index, provide a linear index."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static struct PyModuleDef UtilitiesModule = {
   PyModuleDef_HEAD_INIT,
   "utilities_optimized",   /* name of module */
   "A collection of common utilities.", /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
   UtilitiesMethods
};

PyMODINIT_FUNC PyInit_utilities_optimized(void) {
    return PyModule_Create(&UtilitiesModule);
}