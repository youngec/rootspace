#include "_index_handling.h"

Py_ssize_t linearize_scalar_indices(Py_ssize_t N, Py_ssize_t M, int transposed, Py_ssize_t i, Py_ssize_t j) {
    if (!transposed && 0 <= i && i < N && 0 <= j && j < M) {
        return i * M + j;
    } else if (transposed && 0 <= j && j < N && 0 <= i && i < M) {
        return j * M + i;
    } else {
        PyErr_SetString(PyExc_IndexError, "Index out of bounds");
        return -1;
    }
}

static PyObject* li_int_int(Py_ssize_t N, Py_ssize_t M, int transposed, Py_ssize_t i, Py_ssize_t j) {
    Py_ssize_t lin_idx = linearize_scalar_indices(N, M, transposed, i, j);
    if (lin_idx < 0) {
        return NULL;
    }
    return Py_BuildValue("(n)", lin_idx);
}

static PyObject* li_int_tuple(Py_ssize_t N, Py_ssize_t M, int transposed, Py_ssize_t i, PyObject* j) {
    Py_ssize_t length = PyTuple_Size(j);
    PyObject* r = PyTuple_New(length);
    if (r == NULL) {
        return NULL;
    }

    for (Py_ssize_t r_idx = 0; r_idx < length; r_idx++) {
        PyObject* j_element = PyTuple_GetItem(j, r_idx);
        if (PyLong_Check(j_element)) {
            Py_ssize_t j_element_value = PyLong_AsSsize_t(j_element);
            Py_ssize_t lin_idx = linearize_scalar_indices(N, M, transposed, i, j_element_value);
            if (lin_idx < 0) {
                Py_DECREF(r);
                return NULL;
            }
            PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
        } else {
            Py_DECREF(r);
            PyErr_SetString(PyExc_TypeError, "Expected integers as tuple elements.");
            return NULL;
        }
    }

    return r;
}

static PyObject* li_int_slice(Py_ssize_t N, Py_ssize_t M, int transposed, Py_ssize_t i, PyObject* j) {
    Py_ssize_t max_j = M;
    if (transposed) {
        max_j = N;
    }
    Py_ssize_t start = 0;
    Py_ssize_t stop = max_j;
    Py_ssize_t step = 1;
    Py_ssize_t length = max_j;

    if (PySlice_GetIndicesEx(j, max_j, &start, &stop, &step, &length) < 0) {
        return NULL;
    }

    PyObject* r = PyTuple_New(length);
    if (r == NULL) {
        return NULL;
    }

    for (Py_ssize_t r_idx = 0; r_idx < length; r_idx++) {
        Py_ssize_t j_idx = r_idx * step + start;
        Py_ssize_t lin_idx = linearize_scalar_indices(N, M, transposed, i, j_idx);
        if (lin_idx < 0) {
            Py_DECREF(r);
            return NULL;
        }
        PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
    }

    return r;
}

 PyObject* li_tuple_int(Py_ssize_t N, Py_ssize_t M, int transposed, PyObject* i, Py_ssize_t j) {
    Py_ssize_t length = PyTuple_Size(i);
    PyObject* r = PyTuple_New(length);
    if (r == NULL) {
        return NULL;
    }

    for (Py_ssize_t r_idx = 0; r_idx < length; r_idx++) {
        PyObject* i_element = PyTuple_GetItem(i, r_idx);
        if (PyLong_Check(i_element)) {
            Py_ssize_t i_element_value = PyLong_AsSsize_t(i_element);
            Py_ssize_t lin_idx = linearize_scalar_indices(N, M, transposed, i_element_value, j);
            if (lin_idx < 0) {
                Py_DECREF(r);
                return NULL;
            }
            PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
        } else {
            Py_DECREF(r);
            PyErr_SetString(PyExc_TypeError, "Expected integers as tuple elements.");
            return NULL;
        }
    }

    return r;
}

static PyObject* li_tuple_tuple(Py_ssize_t N, Py_ssize_t M, int transposed, PyObject* i, PyObject* j) {
    Py_ssize_t i_len = PyTuple_Size(i);
    Py_ssize_t j_len = PyTuple_Size(j);
    Py_ssize_t length = i_len * j_len;

    PyObject* r = PyTuple_New(length);
    if (r == NULL) {
        return NULL;
    }

    for (Py_ssize_t i_idx = 0; i_idx < i_len; i_idx++) {
        PyObject* i_element = PyTuple_GetItem(i, i_idx);
        if (PyLong_Check(i_element)) {
            Py_ssize_t i_element_value = PyLong_AsSsize_t(i_element);
            for (Py_ssize_t j_idx = 0; j_idx < j_len; j_idx++) {
                PyObject* j_element = PyTuple_GetItem(j, j_idx);
                if (PyLong_Check(j_element)) {
                    Py_ssize_t j_element_value = PyLong_AsSsize_t(j_element);
                    Py_ssize_t lin_idx = linearize_scalar_indices(N, M, transposed, i_element_value, j_element_value);
                    if (lin_idx < 0) {
                        Py_DECREF(r);
                        return NULL;
                    }
                    Py_ssize_t r_idx = linearize_scalar_indices(i_len, j_len, 0, i_idx, j_idx);
                    if (r_idx < 0) {
                        Py_DECREF(r);
                        return NULL;
                    }
                    PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
                } else {
                    Py_DECREF(r);
                    PyErr_SetString(PyExc_TypeError, "Expected integers as tuple elements.");
                    return NULL;
                }
            }
        } else {
            Py_DECREF(r);
            PyErr_SetString(PyExc_TypeError, "Expected integers as tuple elements.");
            return NULL;
        }
    }

    return r;
}

static  PyObject* li_tuple_slice(Py_ssize_t N, Py_ssize_t M, int transposed, PyObject* i, PyObject* j) {
    Py_ssize_t max_j = M;
    if (transposed) {
        max_j = N;
    }

    Py_ssize_t i_len = PyTuple_Size(i);
    Py_ssize_t j_start = 0;
    Py_ssize_t j_stop = max_j;
    Py_ssize_t j_step = 1;
    Py_ssize_t j_len = max_j;

    if (PySlice_GetIndicesEx(j, max_j, &j_start, &j_stop, &j_step, &j_len) < 0) {
        return NULL;
    }

    PyObject* r = PyTuple_New(i_len * j_len);
    if (r == NULL) {
        return NULL;
    }

    for (Py_ssize_t i_idx = 0; i_idx < i_len; i_idx++) {
        PyObject* i_element = PyTuple_GetItem(i, i_idx);
        if (PyLong_Check(i_element)) {
            Py_ssize_t i_element_value = PyLong_AsSsize_t(i_element);
            for (Py_ssize_t j_idx = 0; j_idx < j_len; j_idx++) {
                Py_ssize_t j_element_value = j_idx * j_step + j_start;
                Py_ssize_t lin_idx = linearize_scalar_indices(N, M, transposed, i_element_value, j_element_value);
                if (lin_idx < 0) {
                    Py_DECREF(r);
                    return NULL;
                }
                Py_ssize_t r_idx = linearize_scalar_indices(i_len, j_len, 0, i_idx, j_idx);
                if (r_idx < 0) {
                    Py_DECREF(r);
                    return NULL;
                }
                PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
            }
        } else {
            Py_DECREF(r);
            PyErr_SetString(PyExc_TypeError, "Expected integers as tuple elements.");
            return NULL;
        }
    }

    return r;
}

static PyObject* li_slice_int(Py_ssize_t N, Py_ssize_t M, int transposed, PyObject* i, Py_ssize_t j) {
    Py_ssize_t max_i = N;
    if (transposed) {
        max_i = M;
    }

    Py_ssize_t start = 0;
    Py_ssize_t stop = max_i;
    Py_ssize_t step = 1;
    Py_ssize_t length = max_i;

    if (PySlice_GetIndicesEx(i, max_i, &start, &stop, &step, &length) < 0) {
        return NULL;
    }

    PyObject* r = PyTuple_New(length);
    if (r == NULL) {
        return NULL;
    }

    for (Py_ssize_t r_idx = 0; r_idx < length; r_idx++) {
        Py_ssize_t i_idx = r_idx * step + start;
        Py_ssize_t lin_idx = linearize_scalar_indices(N, M, transposed, i_idx, j);
        if (lin_idx < 0) {
            Py_DECREF(r);
            return NULL;
        }
        PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
    }

    return r;
}

static PyObject* li_slice_tuple(Py_ssize_t N, Py_ssize_t M, int transposed, PyObject* i, PyObject* j) {
    Py_ssize_t max_i = N;
    if (transposed) {
        max_i = M;
    }

    Py_ssize_t i_start = 0;
    Py_ssize_t i_stop = max_i;
    Py_ssize_t i_step = 1;
    Py_ssize_t i_len = max_i;

    if (PySlice_GetIndicesEx(i, max_i, &i_start, &i_stop, &i_step, &i_len) < 0) {
        return NULL;
    }
    Py_ssize_t j_len = PyTuple_Size(j);

    PyObject* r = PyTuple_New(i_len * j_len);
    if (r == NULL) {
        return NULL;
    }

    for (Py_ssize_t i_idx = 0; i_idx < i_len; i_idx++) {
        Py_ssize_t i_element_value = i_idx * i_step + i_start;
        for (Py_ssize_t j_idx = 0; j_idx < j_len; j_idx++) {
            PyObject* j_element = PyTuple_GetItem(j, j_idx);
            if (PyLong_Check(j_element)) {
                Py_ssize_t j_element_value = PyLong_AsSsize_t(j_element);
                Py_ssize_t lin_idx = linearize_scalar_indices(N, M, transposed, i_element_value, j_element_value);
                if (lin_idx < 0) {
                    Py_DECREF(r);
                    return NULL;
                }
                Py_ssize_t r_idx = linearize_scalar_indices(i_len, j_len, 0, i_idx, j_idx);
                if (r_idx < 0) {
                    Py_DECREF(r);
                    return NULL;
                }
                PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
            } else {
                Py_DECREF(r);
                PyErr_SetString(PyExc_TypeError, "Expected integers as tuple elements.");
                return NULL;
            }
        }
    }

    return r;

}

static PyObject* li_slice_slice(Py_ssize_t N, Py_ssize_t M, int transposed, PyObject* i, PyObject* j) {
    Py_ssize_t max_i = N;
    Py_ssize_t max_j = M;
    if (transposed) {
        max_i = M;
        max_j = N;
    }

    Py_ssize_t i_start = 0;
    Py_ssize_t i_stop = max_i;
    Py_ssize_t i_step = 1;
    Py_ssize_t i_len = max_i;

    if (PySlice_GetIndicesEx(i, max_i, &i_start, &i_stop, &i_step, &i_len) < 0) {
        return NULL;
    }

    Py_ssize_t j_start = 0;
    Py_ssize_t j_stop = max_j;
    Py_ssize_t j_step = 1;
    Py_ssize_t j_len = max_j;

    if (PySlice_GetIndicesEx(j, max_j, &j_start, &j_stop, &j_step, &j_len) < 0) {
        return NULL;
    }

    PyObject* r = PyTuple_New(i_len * j_len);
    if (r == NULL) {
        return NULL;
    }

    for (Py_ssize_t i_idx = 0; i_idx < i_len; i_idx++) {
        Py_ssize_t i_element_value = i_idx * i_step + i_start;
        for (Py_ssize_t j_idx = 0; j_idx < j_len; j_idx++) {
            Py_ssize_t j_element_value = j_idx * j_step + j_start;
            Py_ssize_t lin_idx = linearize_scalar_indices(N, M, transposed, i_element_value, j_element_value);
            if (lin_idx < 0) {
                Py_DECREF(r);
                return NULL;
            }
            Py_ssize_t r_idx = linearize_scalar_indices(i_len, j_len, 0, i_idx, j_idx);
            if (r_idx < 0) {
                Py_DECREF(r);
                return NULL;
            }
            PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
        }
    }

    return r;
}

PyObject* get_sub_shape(Py_ssize_t N, Py_ssize_t M, int transposed, PyObject* indices) {
    if (!PyTuple_Check(indices)) {
        PyErr_SetString(PyExc_TypeError, "The parameter 'indices' must be a tuple.");
        return NULL;
    }

    Py_ssize_t idx_len = PyTuple_Size(indices);
    if (idx_len != 2) {
        PyErr_SetString(PyExc_ValueError, "The parameter 'indices' must be of length 2.");
        return NULL;
    }

    Py_ssize_t max_i = N;
    Py_ssize_t max_j = M;
    if (transposed) {
        max_i = M;
        max_j = N;
    }

    PyObject* i = PyTuple_GetItem(indices, 0);
    PyObject* j = PyTuple_GetItem(indices, 1);

    int i_is_int = PyLong_Check(i);
    int i_is_tuple = PyTuple_Check(i);
    int i_is_slice = PySlice_Check(i);
    int j_is_int = PyLong_Check(j);
    int j_is_tuple = PyTuple_Check(j);
    int j_is_slice = PySlice_Check(j);

    if (i_is_int && j_is_int) {
        return Py_BuildValue("(ll)", 1, 1);
    } else if (i_is_int && j_is_tuple) {
        return Py_BuildValue("(ll)", 1, PyTuple_Size(j));
    } else if (i_is_int && j_is_slice) {
        Py_ssize_t start = 0;
        Py_ssize_t stop = max_j;
        Py_ssize_t step = 1;
        Py_ssize_t len = max_j;
        if (PySlice_GetIndicesEx(j, max_j, &start, &stop, &step, &len) < 0) {
            return NULL;
        }
        return Py_BuildValue("(ll)", 1, len);
    } else if (i_is_tuple && j_is_int) {
        return Py_BuildValue("(ll)", PyTuple_Size(i), 1);
    } else if (i_is_tuple && j_is_tuple) {
        return Py_BuildValue("(ll)", PyTuple_Size(i), PyTuple_Size(j));
    } else if (i_is_tuple && j_is_slice) {
        Py_ssize_t start = 0;
        Py_ssize_t stop = max_j;
        Py_ssize_t step = 1;
        Py_ssize_t len = max_j;
        if (PySlice_GetIndicesEx(j, max_j, &start, &stop, &step, &len) < 0) {
            return NULL;
        }
        return Py_BuildValue("(ll)", PyTuple_Size(i), len);
    } else if (i_is_slice && j_is_int) {
        Py_ssize_t start = 0;
        Py_ssize_t stop = max_i;
        Py_ssize_t step = 1;
        Py_ssize_t len = max_i;
        if (PySlice_GetIndicesEx(i, max_i, &start, &stop, &step, &len) < 0) {
            return NULL;
        }
        return Py_BuildValue("(ll)", len, 1);
    } else if (i_is_slice && j_is_tuple) {
        Py_ssize_t start = 0;
        Py_ssize_t stop = max_i;
        Py_ssize_t step = 1;
        Py_ssize_t len = max_i;
        if (PySlice_GetIndicesEx(i, max_i, &start, &stop, &step, &len) < 0) {
            return NULL;
        }
        return Py_BuildValue("(ll)", len, PyTuple_Size(j));
    } else if (i_is_slice && j_is_slice) {
        Py_ssize_t start_i = 0;
        Py_ssize_t stop_i = max_i;
        Py_ssize_t step_i = 1;
        Py_ssize_t len_i = max_i;
        if (PySlice_GetIndicesEx(i, max_i, &start_i, &stop_i, &step_i, &len_i) < 0) {
            return NULL;
        }
        Py_ssize_t start_j = 0;
        Py_ssize_t stop_j = max_j;
        Py_ssize_t step_j = 1;
        Py_ssize_t len_j = max_j;
        if (PySlice_GetIndicesEx(j, max_j, &start_j, &stop_j, &step_j, &len_j) < 0) {
            return NULL;
        }
        return Py_BuildValue("(ll)", len_i, len_j);
    } else {
        PyErr_SetString(PyExc_TypeError, "Expected the indices to be either int, tuple or slice.");
        return NULL;
    }
}

PyObject* linearize_indices(Py_ssize_t N, Py_ssize_t M, int transposed, PyObject* indices) {
    if (!PyTuple_Check(indices)) {
        PyErr_SetString(PyExc_TypeError, "The parameter 'indices' must be a tuple.");
        return NULL;
    }

    Py_ssize_t idx_len = PyTuple_Size(indices);
    if (idx_len != 2) {
        PyErr_SetString(PyExc_ValueError, "The parameter 'indices' must be of length 2.");
        return NULL;
    }

    PyObject* i = PyTuple_GetItem(indices, 0);
    PyObject* j = PyTuple_GetItem(indices, 1);

    int i_is_int = PyLong_Check(i);
    int i_is_tuple = PyTuple_Check(i);
    int i_is_slice = PySlice_Check(i);
    int j_is_int = PyLong_Check(j);
    int j_is_tuple = PyTuple_Check(j);
    int j_is_slice = PySlice_Check(j);

    if (i_is_int && j_is_int) {
        return li_int_int(N, M, transposed, PyLong_AsSsize_t(i), PyLong_AsSsize_t(j));
    } else if (i_is_int && j_is_tuple) {
        return li_int_tuple(N, M, transposed, PyLong_AsSsize_t(i), j);
    } else if (i_is_int && j_is_slice) {
        return li_int_slice(N, M, transposed, PyLong_AsSsize_t(i), j);
    } else if (i_is_tuple && j_is_int) {
        return li_tuple_int(N, M, transposed, i, PyLong_AsSsize_t(j));
    } else if (i_is_tuple && j_is_tuple) {
        return li_tuple_tuple(N, M, transposed, i, j);
    } else if (i_is_tuple && j_is_slice) {
        return li_tuple_slice(N, M, transposed, i, j);
    } else if (i_is_slice && j_is_int) {
        return li_slice_int(N, M, transposed, i, PyLong_AsSsize_t(j));
    } else if (i_is_slice && j_is_tuple) {
        return li_slice_tuple(N, M, transposed, i, j);
    } else if (i_is_slice && j_is_slice) {
        return li_slice_slice(N, M, transposed, i, j);
    } else {
        PyErr_SetString(PyExc_TypeError, "Expected the indices to be either int, tuple or slice.");
        return NULL;
    }
}

PyObject* complete_indices(PyObject* indices) {
    PyObject* idx = PyTuple_New(2);
    if (idx == NULL) {
        return NULL;
    }

    Py_ssize_t idx_a = 0;
    Py_ssize_t idx_b = 1;

    if (PyLong_Check(indices) || PySlice_Check(indices)) {
        PyObject* idx_a_element = indices;
        PyObject* idx_b_element = PySlice_New(NULL, NULL, NULL);
        if (idx_b_element == NULL) {
            Py_DECREF(idx);
            return NULL;
        }
        Py_INCREF(idx_a_element);
        PyTuple_SetItem(idx, idx_a, idx_a_element);
        PyTuple_SetItem(idx, idx_b, idx_b_element);
    } else if (PyTuple_Check(indices)) {
        if (PyTuple_Size(indices) == 1) {
            PyObject* idx_a_element = PyTuple_GetItem(indices, 0);
            PyObject* idx_b_element = PySlice_New(NULL, NULL, NULL);
            if (idx_b_element == NULL) {
                Py_DECREF(idx);
                return NULL;
            }
            Py_INCREF(idx_a_element);
            PyTuple_SetItem(idx, idx_a, idx_a_element);
            PyTuple_SetItem(idx, idx_b, idx_b_element);
        } else if (PyTuple_Size(indices) == 2) {
            PyObject* idx_a_element = PyTuple_GetItem(indices, 0);
            PyObject* idx_b_element = PyTuple_GetItem(indices, 1);
            Py_INCREF(idx_a_element);
            PyTuple_SetItem(idx, idx_a, idx_a_element);
            Py_INCREF(idx_b_element);
            PyTuple_SetItem(idx, idx_b, idx_b_element);
        } else {
            Py_DECREF(idx);
            PyErr_SetString(PyExc_ValueError, "Too many multi-dimensional indices, expected 2.");
            return NULL;
        }
    } else {
        Py_DECREF(idx);
        PyErr_SetString(PyExc_TypeError, "Expected an integer, a slice or a tuple.");
        return NULL;
    }

    return idx;
}

PyObject* select_all(Py_ssize_t N, Py_ssize_t M, int transposed) {
    PyObject* slice_i = PySlice_New(NULL, NULL, NULL);
    if (slice_i == NULL) {
        return NULL;
    }
    PyObject* slice_j = PySlice_New(NULL, NULL, NULL);
    if (slice_j == NULL) {
        Py_DECREF(slice_i);
        return NULL;
    }
    PyObject* idx = PyTuple_Pack(2, slice_i, slice_j);
    if (idx == NULL) {
        Py_DECREF(slice_i);
        Py_DECREF(slice_j);
        return NULL;
    }

    PyObject* idx_linear = linearize_indices(N, M, transposed, idx);
    if (idx_linear == NULL) {
        Py_DECREF(idx);
        return NULL;
    }

    return idx_linear;
}

PyObject* math_get_sub_shape(PyObject* self, PyObject* args) {
    Py_ssize_t N = 1;
    Py_ssize_t M = 1;
    int transposed = 0;
    PyObject* indices = NULL;
    if (!PyArg_ParseTuple(args, "nnpO!", &N, &M, &transposed, &PyTuple_Type, &indices)) {
        return NULL;
    }
    return get_sub_shape(N, M, transposed, indices);
}
const char math_get_sub_shape_doc[] =
    "For a tuple of int, tuple[Any], or slice, calculate the shape of the \n"
    "resulting sub-matrix. Raises a TypeError if the indices parameter is \n"
    "not a tuple, a ValueError if its length is lot 2, and a TypeError if \n"
    "its elements are neither int, tuple, or slice. \n"
    "\n"
    "Parameters: \n"
    "N: int (The number of rows in the matrix) \n"
    "M: int (The number of columns in the matrix) \n"
    "transposed: bool (Whether the matrix is transposed) \n"
    "indices: 2-Tuple[Union[int, Tuple[Any], slice]] (A two-tuple of indices) \n"
    "\n"
    "Returns: \n"
    "2-Tuple[int]";

PyObject* math_linearize_indices(PyObject* self, PyObject* args) {
    Py_ssize_t N = 1;
    Py_ssize_t M = 1;
    int transposed = 0;
    PyObject* indices = NULL;
    if (!PyArg_ParseTuple(args, "nnpO!", &N, &M, &transposed, &PyTuple_Type, &indices)) {
        return NULL;
    }
    return linearize_indices(N, M, transposed, indices);
}
const char math_linearize_indices_doc[] =
    "For a tuple of int, tuple[int], or slice, calculate the corresponding \n"
    "tuple of linear indices. Raises a TypeError if the indices parameter \n"
    "is not a tuple, a ValueError if its length is not 2, and a TypeError \n"
    "if its elements are neither int, tuple, or slice. Furthermore, raises \n"
    "a TypeError if the elements of a tuple index are not of type int. \n"
    "Lastly, raises an IndexError if indices are out of bounds. \n"
    "\n"
    "Parameters: \n"
    "N: int (The number of rows in the matrix) \n"
    "M: int (The number of columns in the matrix) \n"
    "transposed: bool (Whether the matrix is transposed) \n"
    "indices: 2-Tuple[Union[int, Tuple[int], slice]] (A two-tuple of indices) \n"
    "\n"
    "Returns: \n"
    "Tuple[int]";

PyObject* math_complete_indices(PyObject* self, PyObject* args) {
    PyObject* indices = NULL;
    if (!PyArg_ParseTuple(args, "O", &indices)) {
        return NULL;
    }
    return complete_indices(indices);
}
const char math_complete_indices_doc[] =
    "For a given int, tuple[int] or slice, return a corresponding two-tuple \n"
    "of the form (indices, slice(None, None, None)). \n"
    "\n"
    "Parameters: \n"
    "indices: Union[int, Tuple[int], slice] \n"
    "\n"
    "Returns: \n"
    "2-Tuple[Union[int, Tuple[int], slice]]";


PyObject* math_select_all(PyObject* self, PyObject* args) {
    Py_ssize_t N = 1;
    Py_ssize_t M = 1;
    int transposed = 0;
    if (!PyArg_ParseTuple(args, "nnp", &N, &M, &transposed)) {
        return NULL;
    }
    return select_all(N, M, transposed);
}
const char math_select_all_doc[] =
    "For a given matrix shape and transposition flag, return a tuple of \n"
    "linear indices that select all elements. \n"
    "\n"
    "Parameters: \n"
    "N: int (The number of rows in the matrix) \n"
    "M: int (The number of columns in the matrix) \n"
    "transposed: bool (Whether the matrix is transposed) \n"
    "\n"
    "Returns: \n"
    "Tuple[int]";
