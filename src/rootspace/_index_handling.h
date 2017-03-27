#ifndef INDEX_HANDLING_H
#define INDEX_HANDLING_H
#include <Python.h>

static Py_ssize_t linearize_scalar_indices(Py_ssize_t N, Py_ssize_t M, Py_ssize_t i, Py_ssize_t j) {
    if (i >= 0 && i < N && j >= 0 && j < M) {
        return i * M + j;
    } else {
        PyErr_SetString(PyExc_IndexError, "Index out of bounds");
        return -1;
    }
}

static PyObject* li_int_int(Py_ssize_t N, Py_ssize_t M, Py_ssize_t i, Py_ssize_t j) {
    Py_ssize_t lin_idx = linearize_scalar_indices(N, M, i, j);
    if (lin_idx < 0) {
        return NULL;
    }
    return Py_BuildValue("(n)", lin_idx);
}

static PyObject* li_int_tuple(Py_ssize_t N, Py_ssize_t M, Py_ssize_t i, PyObject* j) {
    Py_ssize_t length = PyTuple_Size(j);
    PyObject* r = PyTuple_New(length);
    if (r == NULL) {
        return NULL;
    }

    Py_ssize_t r_idx;
    for (r_idx = 0; r_idx < length; r_idx++) {
        PyObject* j_element = PyTuple_GetItem(j, r_idx);
        if (PyLong_Check(j_element)) {
            Py_ssize_t j_element_value = PyLong_AsSsize_t(j_element);
            Py_ssize_t lin_idx = linearize_scalar_indices(N, M, i, j_element_value);
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

static PyObject* li_int_slice(Py_ssize_t N, Py_ssize_t M, Py_ssize_t i, PyObject* j) {
    Py_ssize_t start = 0;
    Py_ssize_t stop = M;
    Py_ssize_t step = 1;
    Py_ssize_t length = M;

    if (PySlice_GetIndicesEx(j, M, &start, &stop, &step, &length) < 0) {
        return NULL;
    }

    PyObject* r = PyTuple_New(length);
    if (r == NULL) {
        return NULL;
    }

    Py_ssize_t r_idx;
    for (r_idx = 0; r_idx < length; r_idx++) {
        Py_ssize_t j_idx = r_idx * step + start;
        Py_ssize_t lin_idx = linearize_scalar_indices(N, M, i, j_idx);
        if (lin_idx < 0) {
            Py_DECREF(r);
            return NULL;
        }
        PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
    }

    return r;
}

static PyObject* li_tuple_int(Py_ssize_t N, Py_ssize_t M, PyObject* i, Py_ssize_t j) {
    Py_ssize_t length = PyTuple_Size(i);
    PyObject* r = PyTuple_New(length);
    if (r == NULL) {
        return NULL;
    }

    Py_ssize_t r_idx;
    for (r_idx = 0; r_idx < length; r_idx++) {
        PyObject* i_element = PyTuple_GetItem(i, r_idx);
        if (PyLong_Check(i_element)) {
            Py_ssize_t i_element_value = PyLong_AsSsize_t(i_element);
            Py_ssize_t lin_idx = linearize_scalar_indices(N, M, i_element_value, j);
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

static PyObject* li_tuple_tuple(Py_ssize_t N, Py_ssize_t M, PyObject* i, PyObject* j) {
    Py_ssize_t i_len = PyTuple_Size(i);
    Py_ssize_t j_len = PyTuple_Size(j);
    Py_ssize_t length = i_len * j_len;

    PyObject* r = PyTuple_New(length);
    if (r == NULL) {
        return NULL;
    }

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
                    Py_ssize_t lin_idx = linearize_scalar_indices(N, M, i_element_value, j_element_value);
                    if (lin_idx < 0) {
                        Py_DECREF(r);
                        return NULL;
                    }
                    Py_ssize_t r_idx = linearize_scalar_indices(i_len, j_len, i_idx, j_idx);
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

static PyObject* li_tuple_slice(Py_ssize_t N, Py_ssize_t M, PyObject* i, PyObject* j) {
    Py_ssize_t i_len = PyTuple_Size(i);
    Py_ssize_t j_start = 0;
    Py_ssize_t j_stop = M;
    Py_ssize_t j_step = 1;
    Py_ssize_t j_len = M;

    if (PySlice_GetIndicesEx(j, M, &j_start, &j_stop, &j_step, &j_len) < 0) {
        return NULL;
    }

    PyObject* r = PyTuple_New(i_len * j_len);
    if (r == NULL) {
        return NULL;
    }

    Py_ssize_t i_idx;
    for (i_idx = 0; i_idx < i_len; i_idx++) {
        PyObject* i_element = PyTuple_GetItem(i, i_idx);
        if (PyLong_Check(i_element)) {
            Py_ssize_t i_element_value = PyLong_AsSsize_t(i_element);
            Py_ssize_t j_idx;
            for (j_idx = 0; j_idx < j_len; j_idx++) {
                Py_ssize_t j_element_value = j_idx * j_step + j_start;
                Py_ssize_t lin_idx = linearize_scalar_indices(N, M, i_element_value, j_element_value);
                if (lin_idx < 0) {
                    Py_DECREF(r);
                    return NULL;
                }
                Py_ssize_t r_idx = linearize_scalar_indices(i_len, j_len, i_idx, j_idx);
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

static PyObject* li_slice_int(Py_ssize_t N, Py_ssize_t M, PyObject* i, Py_ssize_t j) {
    Py_ssize_t start = 0;
    Py_ssize_t stop = N;
    Py_ssize_t step = 1;
    Py_ssize_t length = N;

    if (PySlice_GetIndicesEx(i, N, &start, &stop, &step, &length) < 0) {
        return NULL;
    }

    PyObject* r = PyTuple_New(length);
    if (r == NULL) {
        return NULL;
    }

    Py_ssize_t r_idx;
    for (r_idx = 0; r_idx < length; r_idx++) {
        Py_ssize_t i_idx = r_idx * step + start;
        Py_ssize_t lin_idx = linearize_scalar_indices(N, M, i_idx, j);
        if (lin_idx < 0) {
            Py_DECREF(r);
            return NULL;
        }
        PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
    }

    return r;
}

static PyObject* li_slice_tuple(Py_ssize_t N, Py_ssize_t M, PyObject* i, PyObject* j) {
    Py_ssize_t i_start = 0;
    Py_ssize_t i_stop = N;
    Py_ssize_t i_step = 1;
    Py_ssize_t i_len = N;
    Py_ssize_t j_len = PyTuple_Size(j);

    if (PySlice_GetIndicesEx(i, N, &i_start, &i_stop, &i_step, &i_len) < 0) {
        return NULL;
    }

    PyObject* r = PyTuple_New(i_len * j_len);
    if (r == NULL) {
        return NULL;
    }

    Py_ssize_t i_idx;
    for (i_idx = 0; i_idx < i_len; i_idx++) {
        Py_ssize_t i_element_value = i_idx * i_step + i_start;
        Py_ssize_t j_idx;
        for (j_idx = 0; j_idx < j_len; j_idx++) {
            PyObject* j_element = PyTuple_GetItem(j, j_idx);
            if (PyLong_Check(j_element)) {
                Py_ssize_t j_element_value = PyLong_AsSsize_t(j_element);
                Py_ssize_t lin_idx = linearize_scalar_indices(N, M, i_element_value, j_element_value);
                if (lin_idx < 0) {
                    Py_DECREF(r);
                    return NULL;
                }
                Py_ssize_t r_idx = linearize_scalar_indices(i_len, j_len, i_idx, j_idx);
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

static PyObject* li_slice_slice(Py_ssize_t N, Py_ssize_t M, PyObject* i, PyObject* j) {
    Py_ssize_t i_start = 0;
    Py_ssize_t i_stop = N;
    Py_ssize_t i_step = 1;
    Py_ssize_t i_len = N;
    Py_ssize_t j_start = 0;
    Py_ssize_t j_stop = M;
    Py_ssize_t j_step = 1;
    Py_ssize_t j_len = M;

    if (PySlice_GetIndicesEx(i, N, &i_start, &i_stop, &i_step, &i_len) < 0) {
        return NULL;
    }

    if (PySlice_GetIndicesEx(j, M, &j_start, &j_stop, &j_step, &j_len) < 0) {
        return NULL;
    }

    PyObject* r = PyTuple_New(i_len * j_len);
    if (r == NULL) {
        return NULL;
    }

    Py_ssize_t i_idx;
    for (i_idx = 0; i_idx < i_len; i_idx++) {
        Py_ssize_t i_element_value = i_idx * i_step + i_start;
        Py_ssize_t j_idx;
        for (j_idx = 0; j_idx < j_len; j_idx++) {
            Py_ssize_t j_element_value = j_idx * j_step + j_start;
            Py_ssize_t lin_idx = linearize_scalar_indices(N, M, i_element_value, j_element_value);
            if (lin_idx < 0) {
                Py_DECREF(r);
                return NULL;
            }
            Py_ssize_t r_idx = linearize_scalar_indices(i_len, j_len, i_idx, j_idx);
            if (r_idx < 0) {
                Py_DECREF(r);
                return NULL;
            }
            PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
        }
    }

    return r;
}

static PyObject* get_sub_shape(Py_ssize_t N, Py_ssize_t M, PyObject* indices) {
    Py_ssize_t idx_len = PyTuple_Size(indices);
    if (idx_len != 2) {
        PyErr_SetString(PyExc_ValueError, "The number of multidimensional indices is not 2.");
        return NULL;
    }

    PyObject* result = PyTuple_New(idx_len);
    if (result == NULL) {
        return NULL;
    }

    Py_ssize_t idx;
    for (idx = 0; idx < idx_len; idx++) {
        Py_ssize_t shape = 1;
        if (idx == 0) {
            shape = N;
        } else if (idx == 1) {
            shape = M;
        }

        PyObject* i = PyTuple_GetItem(indices, idx);
        if (i == NULL) {
            Py_DECREF(result);
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
                Py_DECREF(result);
                return NULL;
            }
            PyTuple_SetItem(result, idx, PyLong_FromSsize_t(i_len));
        } else {
            Py_DECREF(result);
            PyErr_SetString(PyExc_TypeError, "Expected the indices to be either int, tuple or slice.");
            return NULL;
        }
    }

    return result;
}

static PyObject* linearize_indices(Py_ssize_t N, Py_ssize_t M, PyObject* indices) {
    PyObject* result = NULL;

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
        result = li_int_int(N, M, PyLong_AsSsize_t(i), PyLong_AsSsize_t(j));
    } else if (i_is_int && j_is_tuple) {
        result = li_int_tuple(N, M, PyLong_AsSsize_t(i), j);
    } else if (i_is_int && j_is_slice) {
        result = li_int_slice(N, M, PyLong_AsSsize_t(i), j);
    } else if (i_is_tuple && j_is_int) {
        result = li_tuple_int(N, M, i, PyLong_AsSsize_t(j));
    } else if (i_is_tuple && j_is_tuple) {
        result = li_tuple_tuple(N, M, i, j);
    } else if (i_is_tuple && j_is_slice) {
        result = li_tuple_slice(N, M, i, j);
    } else if (i_is_slice && j_is_int) {
        result = li_slice_int(N, M, i, PyLong_AsSsize_t(j));
    } else if (i_is_slice && j_is_tuple) {
        result = li_slice_tuple(N, M, i, j);
    } else if (i_is_slice && j_is_slice) {
        result = li_slice_slice(N, M, i, j);
    } else {
        PyErr_SetString(PyExc_TypeError, "Expected the indices to be either int, tuple or slice.");
        return NULL;
    }

    return result;
}

static PyObject* complete_indices(PyObject* indices) {
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

static PyObject* select_all(Py_ssize_t N, Py_ssize_t M, int transposed) {
    PyObject* slice_i = PySlice_New(NULL, NULL, NULL);
    if (slice_i == NULL) {
        return NULL;
    }
    PyObject* slice_j = PySlice_New(NULL, NULL, NULL);
    if (slice_j == NULL) {
        Py_DECREF(slice_i);
        return NULL;
    }
    PyObject* idx_raw = PyTuple_Pack(2, slice_i, slice_j);
    if (idx_raw == NULL) {
        Py_DECREF(slice_i);
        Py_DECREF(slice_j);
        return NULL;
    }

    PyObject* idx_clean = complete_indices(idx_raw);
    if (idx_clean == NULL) {
        Py_DECREF(idx_raw);
        return NULL;
    }

    PyObject* idx_linear = linearize_indices(N, M, idx_clean);
    if (idx_linear == NULL) {
        Py_DECREF(idx_raw);
        Py_DECREF(idx_clean);
        return NULL;
    }

    return idx_linear;
}
#endif
