#define PY_SSIZE_T_CLEAN

#include <Python.h>

typedef struct {
    PyObject_VAR_HEAD
    float* data;
    Py_ssize_t shape_i;
    Py_ssize_t shape_j;
    int transposed;
} Matrix;

static PyTypeObject MatrixType;

#define Matrix_Check(op) PyObject_TypeCheck(op, &MatrixType)
#define Matrix_CheckExact(op) (Py_TYPE(op) == &MatrixType)
#define Matrix_DATA(op) (((Matrix*) op)->data)
#define Matrix_SHAPE_I_INTERNAL(op) (((Matrix*) op)->shape_i)
#define Matrix_SHAPE_J_INTERNAL(op) (((Matrix*) op)->shape_j)
#define Matrix_SHAPE_I(op) (((Matrix*) op)->transposed ? Matrix_SHAPE_J_INTERNAL(op) : Matrix_SHAPE_I_INTERNAL(op))
#define Matrix_SHAPE_J(op) (((Matrix*) op)->transposed ? Matrix_SHAPE_I_INTERNAL(op) : Matrix_SHAPE_J_INTERNAL(op))
#define Matrix_TRANSPOSED(op) (((Matrix*) op)->transposed)
#define Matrix_EQUAL_SHAPES(a, b) ()

static Py_ssize_t linearize_scalar_indices(Py_ssize_t shape_i, Py_ssize_t shape_j, Py_ssize_t i, Py_ssize_t j) {
    if (i >= 0 && i < shape_i && j >= 0 && j < shape_j) {
        return i * shape_j + j;
    } else {
        PyErr_SetString(PyExc_IndexError, "Index out of bounds");
        return -1;
    }
}

static PyObject* li_int_int(Py_ssize_t shape_i, Py_ssize_t shape_j, Py_ssize_t i, Py_ssize_t j) {
    Py_ssize_t lin_idx = linearize_scalar_indices(shape_i, shape_j, i, j);
    if (lin_idx < 0) {
        return NULL;
    }
    return Py_BuildValue("(n)", lin_idx);
}

static PyObject* li_int_tuple(Py_ssize_t shape_i, Py_ssize_t shape_j, Py_ssize_t i, PyObject* j) {
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
            Py_ssize_t lin_idx = linearize_scalar_indices(shape_i, shape_j, i, j_element_value);
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

static PyObject* li_int_slice(Py_ssize_t shape_i, Py_ssize_t shape_j, Py_ssize_t i, PyObject* j) {
    Py_ssize_t start = 0;
    Py_ssize_t stop = shape_j;
    Py_ssize_t step = 1;
    Py_ssize_t length = shape_j;

    if (PySlice_GetIndicesEx(j, shape_j, &start, &stop, &step, &length) < 0) {
        return NULL;
    }

    PyObject* r = PyTuple_New(length);
    if (r == NULL) {
        return NULL;
    }

    Py_ssize_t r_idx;
    for (r_idx = 0; r_idx < length; r_idx++) {
        Py_ssize_t j_idx = r_idx * step + start;
        Py_ssize_t lin_idx = linearize_scalar_indices(shape_i, shape_j, i, j_idx);
        if (lin_idx < 0) {
            Py_DECREF(r);
            return NULL;
        }
        PyTuple_SetItem(r, r_idx, PyLong_FromSsize_t(lin_idx));
    }

    return r;
}

static PyObject* li_tuple_int(Py_ssize_t shape_i, Py_ssize_t shape_j, PyObject* i, Py_ssize_t j) {
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
            Py_ssize_t lin_idx = linearize_scalar_indices(shape_i, shape_j, i_element_value, j);
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

static PyObject* li_tuple_tuple(Py_ssize_t shape_i, Py_ssize_t shape_j, PyObject* i, PyObject* j) {
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
                    Py_ssize_t lin_idx = linearize_scalar_indices(shape_i, shape_j, i_element_value, j_element_value);
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
                Py_ssize_t lin_idx = linearize_scalar_indices(shape_i, shape_j, i_element_value, j_element_value);
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

static PyObject* li_slice_int(Py_ssize_t shape_i, Py_ssize_t shape_j, PyObject* i, Py_ssize_t j) {
    Py_ssize_t start = 0;
    Py_ssize_t stop = shape_i;
    Py_ssize_t step = 1;
    Py_ssize_t length = shape_i;

    if (PySlice_GetIndicesEx(i, shape_i, &start, &stop, &step, &length) < 0) {
        return NULL;
    }

    PyObject* r = PyTuple_New(length);
    if (r == NULL) {
        return NULL;
    }

    Py_ssize_t r_idx;
    for (r_idx = 0; r_idx < length; r_idx++) {
        Py_ssize_t i_idx = r_idx * step + start;
        Py_ssize_t lin_idx = linearize_scalar_indices(shape_i, shape_j, i_idx, j);
        if (lin_idx < 0) {
            Py_DECREF(r);
            return NULL;
        }
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
                Py_ssize_t lin_idx = linearize_scalar_indices(shape_i, shape_j, i_element_value, j_element_value);
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
    if (r == NULL) {
        return NULL;
    }

    Py_ssize_t i_idx;
    for (i_idx = 0; i_idx < i_len; i_idx++) {
        Py_ssize_t i_element_value = i_idx * i_step + i_start;
        Py_ssize_t j_idx;
        for (j_idx = 0; j_idx < j_len; j_idx++) {
            Py_ssize_t j_element_value = j_idx * j_step + j_start;
            Py_ssize_t lin_idx = linearize_scalar_indices(shape_i, shape_j, i_element_value, j_element_value);
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

static PyObject* get_sub_shape(Py_ssize_t shape_i, Py_ssize_t shape_j, PyObject* indices) {
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
            shape = shape_i;
        } else if (idx == 1) {
            shape = shape_j;
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

static PyObject* linearize_indices(Py_ssize_t shape_i, Py_ssize_t shape_j, PyObject* indices) {
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

    return result;
}

static PyObject* sanitize_indices(PyObject* indices, int transposed) {
    PyObject* idx = PyTuple_New(2);
    if (idx == NULL) {
        return NULL;
    }

    Py_ssize_t idx_a = 0;
    Py_ssize_t idx_b = 1;
    if (transposed) {
        idx_a = 1;
        idx_b = 0;
    }

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

static PyObject* select_all(Matrix* obj) {
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

    PyObject* idx_clean = sanitize_indices(idx_raw, obj->transposed);
    if (idx_clean == NULL) {
        Py_DECREF(idx_raw);
        return NULL;
    }

    PyObject* idx_linear = linearize_indices(obj->shape_i, obj->shape_j, idx_clean);
    if (idx_linear == NULL) {
        Py_DECREF(idx_raw);
        Py_DECREF(idx_clean);
        return NULL;
    }

    return idx_linear;
}

static Matrix* Matrix_NewInternal(Py_ssize_t shape_i, Py_ssize_t shape_j, int transposed) {
    Matrix* matrix = (Matrix*) MatrixType.tp_alloc(&MatrixType, 0);
    if (matrix == NULL) {
        return NULL;
    }

    Py_ssize_t length = shape_i * shape_j;
    matrix->data = PyMem_New(float, length);
    if (matrix->data == NULL) {
        Py_DECREF(matrix);
        PyErr_SetNone(PyExc_MemoryError);
        return NULL;
    }

    matrix->shape_i = shape_i;
    matrix->shape_j = shape_j;
    matrix->transposed = transposed;
    Py_SIZE(matrix) = length;

    return matrix;
}

static PyObject* Matrix_New(PyTypeObject* type, PyObject* args, PyObject* kwargs) {
    Py_ssize_t shape_i = 0;
    Py_ssize_t shape_j = 0;
    PyObject* data = NULL;
    int transposed = 0;
    Py_ssize_t length = 0;
    float* array_data = NULL;

    static char* kwlist[] = {"", "data", "transposed", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "(ll)|O$p", kwlist, &shape_i, &shape_j, &data, &transposed)) {
        return NULL;
    }

    if (shape_i > 0 && shape_j > 0) {
        length = shape_i * shape_j;
    } else {
        PyErr_SetString(PyExc_ValueError, "Expected the shape to be larger or equal to (1, 1).");
        return NULL;
    }

    Matrix* self = Matrix_NewInternal(shape_i, shape_j, transposed);
    if (self == NULL) {
        return NULL;
    }
    if (data == NULL) {
        Py_ssize_t idx;
        for (idx = 0; idx < length; idx++) {
            self->data[idx] = 0.0f;
        }
    } else if (PyLong_Check(data)) {
        float data_from_long = (float) PyLong_AsLong(data);
        Py_ssize_t idx;
        for (idx = 0; idx < length; idx++) {
            self->data[idx] = data_from_long;
        }
    } else if (PyFloat_Check(data)) {
        float data_from_float = (float) PyFloat_AsDouble(data);
        Py_ssize_t idx;
        for (idx = 0; idx < length; idx++) {
            self->data[idx] = data_from_float;
        }
    } else if (PySequence_Check(data)) {
        if (PySequence_Size(data) != length) {
            Py_DECREF(self);
            PyErr_SetString(PyExc_ValueError, "The number of elements in data must correspond to the shape!");
            return NULL;
        }
        Py_ssize_t idx;
        for (idx = 0; idx < length; idx++) {
            PyObject* item = PySequence_GetItem(data, idx);
            if (PyLong_Check(item)) {
                self->data[idx] = (float) PyLong_AsLong(item);
            } else if (PyFloat_Check(item)) {
                self->data[idx] = (float) PyFloat_AsDouble(item);
            } else {
                Py_DECREF(self);
                PyErr_SetString(PyExc_TypeError, "Expected elements of the tuple to be either integers or floats.");
                return NULL;
            }
        }
    } else {
        Py_DECREF(self);
        PyErr_SetString(PyExc_TypeError, "Expected data to be either an integer, a float or a sequence.");
        return NULL;
    }

    return (PyObject*) self;
}

static void Matrix_Dealloc(Matrix* self) {
    PyMem_Del(self->data);
    Py_TYPE(self)->tp_free((PyObject*) self);
}

static PyObject* Matrix_ToString(Matrix* self) {
    PyObject* rows = PyList_New(self->shape_i);
    if (rows == NULL) {
        return NULL;
    }
    Py_ssize_t i;
    for (i = 0; i < self->shape_i; i++) {
        PyObject* row = PyList_New(self->shape_j);
        if (row == NULL) {
            Py_DECREF(rows);
            return NULL;
        }
        Py_ssize_t j;
        for (j = 0; j < self->shape_j; j++) {
            Py_ssize_t idx = linearize_scalar_indices(self->shape_i, self->shape_j, i, j);
            PyList_SetItem(row, j, PyFloat_FromDouble((double) self->data[idx]));
        }
        PyList_SetItem(rows, i, row);
    }
    PyObject* s = PyUnicode_FromFormat("%S", rows);
    Py_DECREF(rows);
    return s;
}

static PyObject* Matrix_ToRepresentation(Matrix* self) {
    PyObject* d = PyTuple_New(Py_SIZE(self));
    if (d == NULL) {
        return NULL;
    }
    Py_ssize_t idx;
    for (idx = 0; idx < Py_SIZE(self); idx++) {
        PyTuple_SetItem(d, idx, PyFloat_FromDouble((double) self->data[idx]));
    }
    PyObject* s = PyUnicode_FromFormat("Matrix((%u, %u), %R, transposed=%u)", self->shape_i, self->shape_j, d, self->transposed);
    Py_DECREF(d);
    return s;
}

static Py_ssize_t Matrix_Length(Matrix* self) {
    return self->shape_i * self->shape_j;
}

static PyObject* Matrix_GetItem(Matrix* self, PyObject* key) {
    PyObject* idx = sanitize_indices(key, self->transposed);
    if (idx == NULL) {
        return NULL;
    }

    PyObject* sub_shape = get_sub_shape(self->shape_i, self->shape_j, idx);
    if (sub_shape == NULL) {
        Py_DECREF(idx);
        return NULL;
    }

    PyObject* sub_idx = linearize_indices(self->shape_i, self->shape_j, idx);
    if (sub_idx == NULL) {
        Py_DECREF(sub_shape);
        Py_DECREF(idx);
        return NULL;
    }

    PyObject* sub_shape_i_obj = PyTuple_GetItem(sub_shape, 0);
    PyObject* sub_shape_j_obj = PyTuple_GetItem(sub_shape, 1);
    Py_ssize_t sub_shape_i = PyLong_AsLong(sub_shape_i_obj);
    Py_ssize_t sub_shape_j = PyLong_AsLong(sub_shape_j_obj);

    if (sub_shape_i > 1 && sub_shape_i > 1) {
        Matrix* sub_matrix = Matrix_NewInternal(sub_shape_i, sub_shape_j, 0);
        if (sub_matrix == NULL) {
            Py_DECREF(sub_shape);
            Py_DECREF(sub_idx);
            Py_DECREF(idx);
            return NULL;
        }

        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(sub_matrix); i++) {
            PyObject* idx_i_obj = PyTuple_GetItem(sub_idx, i);
            Py_ssize_t idx_i = PyLong_AsLong(idx_i_obj);
            sub_matrix->data[i] = self->data[idx_i];
        }

        Py_DECREF(sub_shape);
        Py_DECREF(sub_idx);
        Py_DECREF(idx);

        return (PyObject*) sub_matrix;
    } else {
        PyObject* idx_i_obj = PyTuple_GetItem(sub_idx, 0);
        Py_ssize_t idx_i = PyLong_AsLong(idx_i_obj);

        Py_DECREF(sub_shape);
        Py_DECREF(sub_idx);
        Py_DECREF(idx);

        return PyFloat_FromDouble(self->data[idx_i]);
    }
}

static int Matrix_SetItem(Matrix* self, PyObject* key, PyObject* value) {
    PyObject* idx = sanitize_indices(key, self->transposed);
    if (idx == NULL) {
        return -1;
    }

    PyObject* sub_shape = get_sub_shape(self->shape_i, self->shape_j, idx);
    if (sub_shape == NULL) {
        Py_DECREF(idx);
        return -1;
    }

    PyObject* sub_idx = linearize_indices(self->shape_i, self->shape_j, idx);
    if (sub_idx == NULL) {
        Py_DECREF(sub_shape);
        Py_DECREF(idx);
        return -1;
    }

    PyObject* sub_shape_i_obj = PyTuple_GetItem(sub_shape, 0);
    PyObject* sub_shape_j_obj = PyTuple_GetItem(sub_shape, 1);
    Py_ssize_t sub_shape_i = PyLong_AsLong(sub_shape_i_obj);
    Py_ssize_t sub_shape_j = PyLong_AsLong(sub_shape_j_obj);
    Py_ssize_t sub_length = sub_shape_i * sub_shape_j;

    if (Matrix_Check(value)) {
        // FIXME: Must account for transposed Matrices 'value'
        Matrix* value_obj = (Matrix*) value;
        if (value_obj->shape_i != sub_shape_i || value_obj->shape_j != sub_shape_j) {
            Py_DECREF(sub_idx);
            Py_DECREF(sub_shape);
            Py_DECREF(idx);
            PyErr_SetString(PyExc_ValueError, "Shape mismatch between indexed range and submitted Matrix value.");
            return -1;
        }
        Py_ssize_t i;
        for (i = 0; i < sub_length; i++) {
            PyObject* sub_idx_obj = PyTuple_GetItem(sub_idx, i);
            Py_ssize_t sub_idx = PyLong_AsSsize_t(sub_idx_obj);
            self->data[sub_idx] = value_obj->data[i];
        }
    } else if (PySequence_Check(value)) {
        if (PySequence_Size(value) != sub_length) {
            Py_DECREF(sub_idx);
            Py_DECREF(sub_shape);
            Py_DECREF(idx);
            PyErr_SetString(PyExc_ValueError, "The submitted value does not have the same length as the indexed range.");
            return -1;
        }
        Py_ssize_t i;
        for (i = 0; i < sub_length; i++) {
            PyObject* value_obj = PySequence_GetItem(value, i);
            float value_data;
            if (PyFloat_Check(value_obj)) {
                value_data = (float) PyFloat_AsDouble(value_obj);
            } else if (PyLong_Check(value_obj)) {
                value_data = (float) PyLong_AsLong(value_obj);
            } else {
                Py_DECREF(sub_idx);
                Py_DECREF(sub_shape);
                Py_DECREF(idx);
                PyErr_SetString(PyExc_TypeError, "The elements of the submitted Sequence must be integers or floats.");
                return -1;
            }
            PyObject* sub_idx_obj = PyTuple_GetItem(sub_idx, i);
            Py_ssize_t sub_idx = PyLong_AsSsize_t(sub_idx_obj);
            self->data[sub_idx] = value_data;
        }
    } else if (PyLong_Check(value)) {
        float value_data = (float) PyLong_AsLong(value);
        Py_ssize_t i;
        for (i = 0; i < sub_length; i++) {
            PyObject* sub_idx_obj = PyTuple_GetItem(sub_idx, i);
            Py_ssize_t sub_idx = PyLong_AsSsize_t(sub_idx_obj);
            self->data[sub_idx] = value_data;
        }
    } else if (PyFloat_Check(value)) {
        float value_data = (float) PyFloat_AsDouble(value);
        Py_ssize_t i;
        for (i = 0; i < sub_length; i++) {
            PyObject* sub_idx_obj = PyTuple_GetItem(sub_idx, i);
            Py_ssize_t sub_idx = PyLong_AsSsize_t(sub_idx_obj);
            self->data[sub_idx] = value_data;
        }
    } else {
        Py_DECREF(sub_idx);
        Py_DECREF(sub_shape);
        Py_DECREF(idx);
        PyErr_SetString(PyExc_TypeError, "Expected a Matrix, a Sequence, an integer or a float as values.");
        return -1;
    }

    return 0;
}

static PyObject* Matrix_LessThan(PyObject* first, PyObject* second) {
    PyObject* result = Py_NotImplemented;

    if (Matrix_Check(first) && Matrix_Check(second)) {
        if (Matrix_SHAPE_I(first) == Matrix_SHAPE_I(second) && Matrix_SHAPE_J(first) == Matrix_SHAPE_J(second)) {
            Matrix* fm = (Matrix*) first;
            Matrix* sm = (Matrix*) second;
                
            PyObject* flinidx = select_all(fm);
            if (flinidx == NULL) {
                return NULL;
            }

            PyObject* slinidx = select_all(sm);
            if (slinidx == NULL) {
                Py_DECREF(flinidx);
                return NULL;
            }

            int comp = 1;
            Py_ssize_t i;
            for (i = 0; i < PyTuple_Size(flinidx); i++) {
                PyObject* f_element = PyTuple_GetItem(flinidx, i);
                Py_ssize_t f_element_value = PyLong_AsLong(f_element);
                PyObject* s_element = PyTuple_GetItem(slinidx, i);
                Py_ssize_t s_element_value = PyLong_AsLong(s_element);
                if (!(fm->data[f_element_value] < sm->data[s_element_value])) {
                    comp = 0;
                    break;
                }
            }
            Py_DECREF(flinidx);
            Py_DECREF(slinidx);
            if (comp) {
                result = Py_True;
            } else {
                result = Py_False;
            }
        } else {
            PyErr_SetString(PyExc_ValueError, "Matrices cannot be compared due to a shape mismatch.");
            return NULL;
        }
    } else if (Matrix_Check(first) && PyLong_Check(second)) {
        int comp = 1;
        float second_value = (float) PyLong_AsLong(second);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(first); i++) {
            if (!(Matrix_DATA(first)[i] < second_value)) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    } else if (Matrix_Check(first) && PyFloat_Check(second)) {
        int comp = 1;
        float second_value = (float) PyFloat_AsDouble(second);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(first); i++) {
            if (!(Matrix_DATA(first)[i] < second_value)) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    } else if (PyLong_Check(first) && Matrix_Check(second)) {
        int comp = 1;
        float first_value = (float) PyLong_AsLong(first);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(second); i++) {
            if (!(first_value < Matrix_DATA(second)[i])) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    } else if (PyFloat_Check(first) && Matrix_Check(second)) {
        int comp = 1;
        float first_value = (float) PyFloat_AsDouble(first);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(second); i++) {
            if (!(first_value < Matrix_DATA(second)[i])) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    }

    Py_INCREF(result);
    return result;
}

static PyObject* Matrix_LessOrEqual(PyObject* first, PyObject* second) {
    PyObject* result = Py_NotImplemented;

    if (Matrix_Check(first) && Matrix_Check(second)) {
        if (Matrix_SHAPE_I(first) == Matrix_SHAPE_I(second) && Matrix_SHAPE_J(first) == Matrix_SHAPE_J(second)) {
            Matrix* fm = (Matrix*) first;
            Matrix* sm = (Matrix*) second;
                
            PyObject* flinidx = select_all(fm);
            if (flinidx == NULL) {
                return NULL;
            }

            PyObject* slinidx = select_all(sm);
            if (slinidx == NULL) {
                Py_DECREF(flinidx);
                return NULL;
            }

            int comp = 1;
            Py_ssize_t i;
            for (i = 0; i < PyTuple_Size(flinidx); i++) {
                PyObject* f_element = PyTuple_GetItem(flinidx, i);
                Py_ssize_t f_element_value = PyLong_AsLong(f_element);
                PyObject* s_element = PyTuple_GetItem(slinidx, i);
                Py_ssize_t s_element_value = PyLong_AsLong(s_element);
                if (!(fm->data[f_element_value] <= sm->data[s_element_value])) {
                    comp = 0;
                    break;
                }
            }
            Py_DECREF(flinidx);
            Py_DECREF(slinidx);
            if (comp) {
                result = Py_True;
            } else {
                result = Py_False;
            }
        } else {
            PyErr_SetString(PyExc_ValueError, "Matrices cannot be compared due to a shape mismatch.");
            return NULL;
        }
    } else if (Matrix_Check(first) && PyLong_Check(second)) {
        int comp = 1;
        float second_value = (float) PyLong_AsLong(second);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(first); i++) {
            if (!(Matrix_DATA(first)[i] <= second_value)) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    } else if (Matrix_Check(first) && PyFloat_Check(second)) {
        int comp = 1;
        float second_value = (float) PyFloat_AsDouble(second);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(first); i++) {
            if (!(Matrix_DATA(first)[i] <= second_value)) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    } else if (PyLong_Check(first) && Matrix_Check(second)) {
        int comp = 1;
        float first_value = (float) PyLong_AsLong(first);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(second); i++) {
            if (!(first_value <= Matrix_DATA(second)[i])) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    } else if (PyFloat_Check(first) && Matrix_Check(second)) {
        int comp = 1;
        float first_value = (float) PyFloat_AsDouble(first);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(second); i++) {
            if (!(first_value <= Matrix_DATA(second)[i])) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    }

    Py_INCREF(result);
    return result;
}

static PyObject* Matrix_Equal(PyObject* first, PyObject* second) {
    PyObject* result = Py_NotImplemented;

    if (Matrix_Check(first) && Matrix_Check(second)) {
        if (Matrix_SHAPE_I(first) == Matrix_SHAPE_I(second) && Matrix_SHAPE_J(first) == Matrix_SHAPE_J(second)) {
            Matrix* fm = (Matrix*) first;
            Matrix* sm = (Matrix*) second;
                
            PyObject* flinidx = select_all(fm);
            if (flinidx == NULL) {
                return NULL;
            }

            PyObject* slinidx = select_all(sm);
            if (slinidx == NULL) {
                Py_DECREF(flinidx);
                return NULL;
            }

            int comp = 1;
            Py_ssize_t i;
            for (i = 0; i < PyTuple_Size(flinidx); i++) {
                PyObject* f_element = PyTuple_GetItem(flinidx, i);
                Py_ssize_t f_element_value = PyLong_AsLong(f_element);
                PyObject* s_element = PyTuple_GetItem(slinidx, i);
                Py_ssize_t s_element_value = PyLong_AsLong(s_element);
                if (!(fm->data[f_element_value] == sm->data[s_element_value])) {
                    comp = 0;
                    break;
                }
            }
            Py_DECREF(flinidx);
            Py_DECREF(slinidx);
            if (comp) {
                result = Py_True;
            } else {
                result = Py_False;
            }
        } else {
            result = Py_False;
        }
    } else if (Matrix_Check(first) && PyLong_Check(second)) {
        int comp = 1;
        float second_value = (float) PyLong_AsLong(second);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(first); i++) {
            if (!(Matrix_DATA(first)[i] == second_value)) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    } else if (Matrix_Check(first) && PyFloat_Check(second)) {
        int comp = 1;
        float second_value = (float) PyFloat_AsDouble(second);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(first); i++) {
            if (!(Matrix_DATA(first)[i] == second_value)) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    } else if (PyLong_Check(first) && Matrix_Check(second)) {
        int comp = 1;
        float first_value = (float) PyLong_AsLong(first);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(second); i++) {
            if (!(first_value == Matrix_DATA(second)[i])) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    } else if (PyFloat_Check(first) && Matrix_Check(second)) {
        int comp = 1;
        float first_value = (float) PyFloat_AsDouble(first);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(second); i++) {
            if (!(first_value == Matrix_DATA(second)[i])) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    }

    Py_INCREF(result);
    return result;
}

static PyObject* Matrix_NotEqual(PyObject* first, PyObject* second) {
    PyObject* result = Py_NotImplemented;

    if (Matrix_Check(first) && Matrix_Check(second)) {
        if (Matrix_SHAPE_I(first) == Matrix_SHAPE_I(second) && Matrix_SHAPE_J(first) == Matrix_SHAPE_J(second)) {
            Matrix* fm = (Matrix*) first;
            Matrix* sm = (Matrix*) second;
                
            PyObject* flinidx = select_all(fm);
            if (flinidx == NULL) {
                return NULL;
            }

            PyObject* slinidx = select_all(sm);
            if (slinidx == NULL) {
                Py_DECREF(flinidx);
                return NULL;
            }

            int comp = 0;
            Py_ssize_t i;
            for (i = 0; i < PyTuple_Size(flinidx); i++) {
                PyObject* f_element = PyTuple_GetItem(flinidx, i);
                Py_ssize_t f_element_value = PyLong_AsLong(f_element);
                PyObject* s_element = PyTuple_GetItem(slinidx, i);
                Py_ssize_t s_element_value = PyLong_AsLong(s_element);
                if (fm->data[f_element_value] != sm->data[s_element_value]) {
                    comp = 1;
                    break;
                }
            }
            Py_DECREF(flinidx);
            Py_DECREF(slinidx);
            if (comp) {
                result = Py_True;
            } else {
                result = Py_False;
            }
        } else {
            result = Py_True;
        }
    } else if (Matrix_Check(first) && PyLong_Check(second)) {
        int comp = 0;
        float second_value = (float) PyLong_AsLong(second);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(first); i++) {
            if (Matrix_DATA(first)[i] != second_value) {
                comp = 1;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    } else if (Matrix_Check(first) && PyFloat_Check(second)) {
        int comp = 0;
        float second_value = (float) PyFloat_AsDouble(second);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(first); i++) {
            if (Matrix_DATA(first)[i] != second_value) {
                comp = 1;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    } else if (PyLong_Check(first) && Matrix_Check(second)) {
        int comp = 0;
        float first_value = (float) PyLong_AsLong(first);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(second); i++) {
            if (first_value != Matrix_DATA(second)[i]) {
                comp = 1;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    } else if (PyFloat_Check(first) && Matrix_Check(second)) {
        int comp = 0;
        float first_value = (float) PyFloat_AsDouble(first);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(second); i++) {
            if (first_value != Matrix_DATA(second)[i]) {
                comp = 1;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    }

    Py_INCREF(result);
    return result;
}

static PyObject* Matrix_GreaterOrEqual(PyObject* first, PyObject* second) {
    PyObject* result = Py_NotImplemented;

    if (Matrix_Check(first) && Matrix_Check(second)) {
        if (Matrix_SHAPE_I(first) == Matrix_SHAPE_I(second) && Matrix_SHAPE_J(first) == Matrix_SHAPE_J(second)) {
            Matrix* fm = (Matrix*) first;
            Matrix* sm = (Matrix*) second;
                
            PyObject* flinidx = select_all(fm);
            if (flinidx == NULL) {
                return NULL;
            }

            PyObject* slinidx = select_all(sm);
            if (slinidx == NULL) {
                Py_DECREF(flinidx);
                return NULL;
            }

            int comp = 1;
            Py_ssize_t i;
            for (i = 0; i < PyTuple_Size(flinidx); i++) {
                PyObject* f_element = PyTuple_GetItem(flinidx, i);
                Py_ssize_t f_element_value = PyLong_AsLong(f_element);
                PyObject* s_element = PyTuple_GetItem(slinidx, i);
                Py_ssize_t s_element_value = PyLong_AsLong(s_element);
                if (!(fm->data[f_element_value] >= sm->data[s_element_value])) {
                    comp = 0;
                    break;
                }
            }
            Py_DECREF(flinidx);
            Py_DECREF(slinidx);
            if (comp) {
                result = Py_True;
            } else {
                result = Py_False;
            }
        } else {
            PyErr_SetString(PyExc_ValueError, "Matrices cannot be compared due to a shape mismatch.");
            return NULL;
        }
    } else if (Matrix_Check(first) && PyLong_Check(second)) {
        int comp = 1;
        float second_value = (float) PyLong_AsLong(second);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(first); i++) {
            if (!(Matrix_DATA(first)[i] >= second_value)) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    } else if (Matrix_Check(first) && PyFloat_Check(second)) {
        int comp = 1;
        float second_value = (float) PyFloat_AsDouble(second);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(first); i++) {
            if (!(Matrix_DATA(first)[i] >= second_value)) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    } else if (PyLong_Check(first) && Matrix_Check(second)) {
        int comp = 1;
        float first_value = (float) PyLong_AsLong(first);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(second); i++) {
            if (!(first_value >= Matrix_DATA(second)[i])) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    } else if (PyFloat_Check(first) && Matrix_Check(second)) {
        int comp = 1;
        float first_value = (float) PyFloat_AsDouble(first);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(second); i++) {
            if (!(first_value >= Matrix_DATA(second)[i])) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    }

    Py_INCREF(result);
    return result;
}

static PyObject* Matrix_GreaterThan(PyObject* first, PyObject* second) {
    PyObject* result = Py_NotImplemented;

    if (Matrix_Check(first) && Matrix_Check(second)) {
        if (Matrix_SHAPE_I(first) == Matrix_SHAPE_I(second) && Matrix_SHAPE_J(first) == Matrix_SHAPE_J(second)) {
            Matrix* fm = (Matrix*) first;
            Matrix* sm = (Matrix*) second;
                
            PyObject* flinidx = select_all(fm);
            if (flinidx == NULL) {
                return NULL;
            }

            PyObject* slinidx = select_all(sm);
            if (slinidx == NULL) {
                Py_DECREF(flinidx);
                return NULL;
            }

            int comp = 1;
            Py_ssize_t i;
            for (i = 0; i < PyTuple_Size(flinidx); i++) {
                PyObject* f_element = PyTuple_GetItem(flinidx, i);
                Py_ssize_t f_element_value = PyLong_AsLong(f_element);
                PyObject* s_element = PyTuple_GetItem(slinidx, i);
                Py_ssize_t s_element_value = PyLong_AsLong(s_element);
                if (!(fm->data[f_element_value] > sm->data[s_element_value])) {
                    comp = 0;
                    break;
                }
            }
            Py_DECREF(flinidx);
            Py_DECREF(slinidx);
            if (comp) {
                result = Py_True;
            } else {
                result = Py_False;
            }
        } else {
            PyErr_SetString(PyExc_ValueError, "Matrices cannot be compared due to a shape mismatch.");
            return NULL;
        }
    } else if (Matrix_Check(first) && PyLong_Check(second)) {
        int comp = 1;
        float second_value = (float) PyLong_AsLong(second);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(first); i++) {
            if (!(Matrix_DATA(first)[i] > second_value)) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    } else if (Matrix_Check(first) && PyFloat_Check(second)) {
        int comp = 1;
        float second_value = (float) PyFloat_AsDouble(second);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(first); i++) {
            if (!(Matrix_DATA(first)[i] > second_value)) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    } else if (PyLong_Check(first) && Matrix_Check(second)) {
        int comp = 1;
        float first_value = (float) PyLong_AsLong(first);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(second); i++) {
            if (!(first_value > Matrix_DATA(second)[i])) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    } else if (PyFloat_Check(first) && Matrix_Check(second)) {
        int comp = 1;
        float first_value = (float) PyFloat_AsDouble(first);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(second); i++) {
            if (!(first_value > Matrix_DATA(second)[i])) {
                comp = 0;
                break;
            }
        }
        if (comp) {
            result = Py_True;
        } else {
            result = Py_False;
        }
    }

    Py_INCREF(result);
    return result;
}

static PyObject* Matrix_RichCompare(PyObject* first, PyObject* second, int op) {
    switch (op) {
        case Py_LT:
            return Matrix_LessThan(first, second);
        case Py_LE:
            return Matrix_LessOrEqual(first, second);
        case Py_EQ:
            return Matrix_Equal(first, second);
        case Py_NE:
            return Matrix_NotEqual(first, second);
        case Py_GE:
            return Matrix_GreaterOrEqual(first, second);
        case Py_GT:
            return Matrix_GreaterThan(first, second);
        default:
            PyErr_SetString(PyExc_RuntimeError, "Unreachable code reached in Matrix_RichCompare.");
            return NULL;
    }
}

static PyObject* Matrix_Negative(Matrix* self) {
    Matrix* matrix = Matrix_NewInternal(self->shape_i, self->shape_j, self->transposed);
    if (matrix == NULL) {
        return NULL;
    }

    Py_ssize_t i;
    for (i = 0; i < Py_SIZE(matrix); i++) {
        matrix->data[i] = -self->data[i];
    }

    return (PyObject*) matrix;
}

static PyObject* Matrix_Positive(Matrix* self) {
    Matrix* matrix = Matrix_NewInternal(self->shape_i, self->shape_j, self->transposed);
    if (matrix == NULL) {
        return NULL;
    }

    Py_ssize_t i;
    for (i = 0; i < Py_SIZE(matrix); i++) {
        matrix->data[i] = self->data[i];
    }

    return (PyObject*) matrix;
}

static PyObject* Matrix_Absolute(Matrix* self) {
    Matrix* matrix = Matrix_NewInternal(self->shape_i, self->shape_j, self->transposed);
    if (matrix == NULL) {
        return NULL;
    }

    Py_ssize_t i;
    for (i = 0; i < Py_SIZE(matrix); i++) {
        matrix->data[i] = (float) fabs(self->data[i]);
    }

    return (PyObject*) matrix;
}

static PyObject* Matrix_Add(PyObject* first, PyObject* second) {
    if (Matrix_Check(first) && Matrix_Check(second)) {
        if (Matrix_SHAPE_I(first) == Matrix_SHAPE_I(second) && Matrix_SHAPE_J(first) == Matrix_SHAPE_J(second)) {
            Matrix* fm = (Matrix*) first;
            Matrix* sm = (Matrix*) second;

            PyObject* flinidx = select_all(fm);
            if (flinidx == NULL) {
                return NULL;
            }

            PyObject* slinidx = select_all(sm);
            if (slinidx == NULL) {
                Py_DECREF(flinidx);
                return NULL;
            }

            Matrix* result = Matrix_NewInternal(fm->shape_i, fm->shape_j, fm->transposed);

            Py_ssize_t i;
            for (i = 0; i < PyTuple_Size(flinidx); i++) {
                PyObject* f_element = PyTuple_GetItem(flinidx, i);
                Py_ssize_t f_element_value = PyLong_AsLong(f_element);
                PyObject* s_element = PyTuple_GetItem(slinidx, i);
                Py_ssize_t s_element_value = PyLong_AsLong(s_element);
                result->data[f_element_value] = fm->data[f_element_value] + sm->data[s_element_value];
            }
            Py_DECREF(flinidx);
            Py_DECREF(slinidx);
            return (PyObject*) result;
        } else {
            PyErr_SetString(PyExc_ValueError, "Cannot perform addition on Matrices of differing shapes.");
            return NULL;
        }
    } else if (Matrix_Check(first) && PyLong_Check(second)) {
        Matrix* result = Matrix_NewInternal(Matrix_SHAPE_I_INTERNAL(first), Matrix_SHAPE_J_INTERNAL(first), Matrix_TRANSPOSED(first));
        if (result == NULL) {
            return NULL;
        }

        float second_value = (float) PyLong_AsLong(second);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(result); i++) {
            result->data[i] = Matrix_DATA(first)[i] + second_value;
        }

        return (PyObject*) result;
    } else if (Matrix_Check(first) && PyFloat_Check(second)) {
        Matrix* result = Matrix_NewInternal(Matrix_SHAPE_I_INTERNAL(first), Matrix_SHAPE_J_INTERNAL(first), Matrix_TRANSPOSED(first));
        if (result == NULL) {
            return NULL;
        }

        float second_value = (float) PyFloat_AsDouble(second);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(result); i++) {
            result->data[i] = Matrix_DATA(first)[i] + second_value;
        }

        return (PyObject*) result;
    } else if (PyLong_Check(first) && Matrix_Check(second)) {
        Matrix* result = Matrix_NewInternal(Matrix_SHAPE_I_INTERNAL(second), Matrix_SHAPE_J_INTERNAL(second), Matrix_TRANSPOSED(second));
        if (result == NULL) {
            return NULL;
        }

        float first_value = (float) PyLong_AsLong(first);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(result); i++) {
            result->data[i] = first_value + Matrix_DATA(second)[i];
        }

        return (PyObject*) result;
    } else if (PyFloat_Check(first) && Matrix_Check(second)) {
        Matrix* result = Matrix_NewInternal(Matrix_SHAPE_I_INTERNAL(second), Matrix_SHAPE_J_INTERNAL(second), Matrix_TRANSPOSED(second));
        if (result == NULL) {
            return NULL;
        }

        float first_value = (float) PyFloat_AsDouble(first);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(result); i++) {
            result->data[i] = first_value + Matrix_DATA(second)[i];
        }

        return (PyObject*) result;
    } else {
        PyObject* result = Py_NotImplemented;
        Py_INCREF(result);
        return result;
    }
}

static PyObject* Matrix_Subtract(PyObject* first, PyObject* second) {
    if (Matrix_Check(first) && Matrix_Check(second)) {
        if (Matrix_SHAPE_I(first) == Matrix_SHAPE_I(second) && Matrix_SHAPE_J(first) == Matrix_SHAPE_J(second)) {
            Matrix* fm = (Matrix*) first;
            Matrix* sm = (Matrix*) second;

            PyObject* flinidx = select_all(fm);
            if (flinidx == NULL) {
                return NULL;
            }

            PyObject* slinidx = select_all(sm);
            if (slinidx == NULL) {
                Py_DECREF(flinidx);
                return NULL;
            }

            Matrix* result = Matrix_NewInternal(fm->shape_i, fm->shape_j, fm->transposed);

            Py_ssize_t i;
            for (i = 0; i < PyTuple_Size(flinidx); i++) {
                PyObject* f_element = PyTuple_GetItem(flinidx, i);
                Py_ssize_t f_element_value = PyLong_AsLong(f_element);
                PyObject* s_element = PyTuple_GetItem(slinidx, i);
                Py_ssize_t s_element_value = PyLong_AsLong(s_element);
                result->data[f_element_value] = fm->data[f_element_value] - sm->data[s_element_value];
            }
            Py_DECREF(flinidx);
            Py_DECREF(slinidx);
            return (PyObject*) result;
        } else {
            PyErr_SetString(PyExc_ValueError, "Cannot perform addition on Matrices of differing shapes.");
            return NULL;
        }
    } else if (Matrix_Check(first) && PyLong_Check(second)) {
        Matrix* result = Matrix_NewInternal(Matrix_SHAPE_I_INTERNAL(first), Matrix_SHAPE_J_INTERNAL(first), Matrix_TRANSPOSED(first));
        if (result == NULL) {
            return NULL;
        }

        float second_value = (float) PyLong_AsLong(second);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(result); i++) {
            result->data[i] = Matrix_DATA(first)[i] - second_value;
        }

        return (PyObject*) result;
    } else if (Matrix_Check(first) && PyFloat_Check(second)) {
        Matrix* result = Matrix_NewInternal(Matrix_SHAPE_I_INTERNAL(first), Matrix_SHAPE_J_INTERNAL(first), Matrix_TRANSPOSED(first));
        if (result == NULL) {
            return NULL;
        }

        float second_value = (float) PyFloat_AsDouble(second);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(result); i++) {
            result->data[i] = Matrix_DATA(first)[i] - second_value;
        }

        return (PyObject*) result;
    } else if (PyLong_Check(first) && Matrix_Check(second)) {
        Matrix* result = Matrix_NewInternal(Matrix_SHAPE_I_INTERNAL(second), Matrix_SHAPE_J_INTERNAL(second), Matrix_TRANSPOSED(second));
        if (result == NULL) {
            return NULL;
        }

        float first_value = (float) PyLong_AsLong(first);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(result); i++) {
            result->data[i] = first_value - Matrix_DATA(second)[i];
        }

        return (PyObject*) result;
    } else if (PyFloat_Check(first) && Matrix_Check(second)) {
        Matrix* result = Matrix_NewInternal(Matrix_SHAPE_I_INTERNAL(second), Matrix_SHAPE_J_INTERNAL(second), Matrix_TRANSPOSED(second));
        if (result == NULL) {
            return NULL;
        }

        float first_value = (float) PyFloat_AsDouble(first);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(result); i++) {
            result->data[i] = first_value - Matrix_DATA(second)[i];
        }

        return (PyObject*) result;
    } else {
        PyObject* result = Py_NotImplemented;
        Py_INCREF(result);
        return result;
    }
}

static PyObject* Matrix_Multiply(PyObject* first, PyObject* second) {
    if (Matrix_Check(first) && Matrix_Check(second)) {
        if (Matrix_SHAPE_I(first) == Matrix_SHAPE_I(second) && Matrix_SHAPE_J(first) == Matrix_SHAPE_J(second)) {
            Matrix* fm = (Matrix*) first;
            Matrix* sm = (Matrix*) second;

            PyObject* flinidx = select_all(fm);
            if (flinidx == NULL) {
                return NULL;
            }

            PyObject* slinidx = select_all(sm);
            if (slinidx == NULL) {
                Py_DECREF(flinidx);
                return NULL;
            }

            Matrix* result = Matrix_NewInternal(fm->shape_i, fm->shape_j, fm->transposed);

            Py_ssize_t i;
            for (i = 0; i < PyTuple_Size(flinidx); i++) {
                PyObject* f_element = PyTuple_GetItem(flinidx, i);
                Py_ssize_t f_element_value = PyLong_AsLong(f_element);
                PyObject* s_element = PyTuple_GetItem(slinidx, i);
                Py_ssize_t s_element_value = PyLong_AsLong(s_element);
                result->data[f_element_value] = fm->data[f_element_value] * sm->data[s_element_value];
            }
            Py_DECREF(flinidx);
            Py_DECREF(slinidx);
            return (PyObject*) result;
        } else {
            PyErr_SetString(PyExc_ValueError, "Cannot perform addition on Matrices of differing shapes.");
            return NULL;
        }
    } else if (Matrix_Check(first) && PyLong_Check(second)) {
        Matrix* result = Matrix_NewInternal(Matrix_SHAPE_I_INTERNAL(first), Matrix_SHAPE_J_INTERNAL(first), Matrix_TRANSPOSED(first));
        if (result == NULL) {
            return NULL;
        }

        float second_value = (float) PyLong_AsLong(second);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(result); i++) {
            result->data[i] = Matrix_DATA(first)[i] * second_value;
        }

        return (PyObject*) result;
    } else if (Matrix_Check(first) && PyFloat_Check(second)) {
        Matrix* result = Matrix_NewInternal(Matrix_SHAPE_I_INTERNAL(first), Matrix_SHAPE_J_INTERNAL(first), Matrix_TRANSPOSED(first));
        if (result == NULL) {
            return NULL;
        }

        float second_value = (float) PyFloat_AsDouble(second);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(result); i++) {
            result->data[i] = Matrix_DATA(first)[i] * second_value;
        }

        return (PyObject*) result;
    } else if (PyLong_Check(first) && Matrix_Check(second)) {
        Matrix* result = Matrix_NewInternal(Matrix_SHAPE_I_INTERNAL(second), Matrix_SHAPE_J_INTERNAL(second), Matrix_TRANSPOSED(second));
        if (result == NULL) {
            return NULL;
        }

        float first_value = (float) PyLong_AsLong(first);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(result); i++) {
            result->data[i] = first_value * Matrix_DATA(second)[i];
        }

        return (PyObject*) result;
    } else if (PyFloat_Check(first) && Matrix_Check(second)) {
        Matrix* result = Matrix_NewInternal(Matrix_SHAPE_I_INTERNAL(second), Matrix_SHAPE_J_INTERNAL(second), Matrix_TRANSPOSED(second));
        if (result == NULL) {
            return NULL;
        }

        float first_value = (float) PyFloat_AsDouble(first);
        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(result); i++) {
            result->data[i] = first_value * Matrix_DATA(second)[i];
        }

        return (PyObject*) result;
    } else {
        PyObject* result = Py_NotImplemented;
        Py_INCREF(result);
        return result;
    }
}

static PyObject* Matrix_TrueDivide(PyObject* first, PyObject* second) {
    if (Matrix_Check(first) && Matrix_Check(second)) {
        if (Matrix_SHAPE_I(first) == Matrix_SHAPE_I(second) && Matrix_SHAPE_J(first) == Matrix_SHAPE_J(second)) {
            Matrix* fm = (Matrix*) first;
            Matrix* sm = (Matrix*) second;

            PyObject* flinidx = select_all(fm);
            if (flinidx == NULL) {
                return NULL;
            }

            PyObject* slinidx = select_all(sm);
            if (slinidx == NULL) {
                Py_DECREF(flinidx);
                return NULL;
            }

            Matrix* result = Matrix_NewInternal(fm->shape_i, fm->shape_j, fm->transposed);

            Py_ssize_t i;
            for (i = 0; i < PyTuple_Size(flinidx); i++) {
                PyObject* f_element = PyTuple_GetItem(flinidx, i);
                Py_ssize_t f_element_value = PyLong_AsLong(f_element);
                PyObject* s_element = PyTuple_GetItem(slinidx, i);
                Py_ssize_t s_element_value = PyLong_AsLong(s_element);
                float s_value = sm->data[s_element_value];
                if (s_value != 0.0f) {
                    result->data[f_element_value] = fm->data[f_element_value] / s_value;
                } else {
                    Py_DECREF(flinidx);
                    Py_DECREF(slinidx);
                    Py_DECREF(result);
                    PyErr_SetNone(PyExc_ZeroDivisionError);
                    return NULL;
                }
            }
            Py_DECREF(flinidx);
            Py_DECREF(slinidx);
            return (PyObject*) result;
        } else {
            PyErr_SetString(PyExc_ValueError, "Cannot perform addition on Matrices of differing shapes.");
            return NULL;
        }
    } else if (Matrix_Check(first) && PyLong_Check(second)) {
        Matrix* result = Matrix_NewInternal(Matrix_SHAPE_I_INTERNAL(first), Matrix_SHAPE_J_INTERNAL(first), Matrix_TRANSPOSED(first));
        if (result == NULL) {
            return NULL;
        }

        float second_value = (float) PyLong_AsLong(second);
        if (second_value == 0.0f) {
            Py_DECREF(result);
            PyErr_SetNone(PyExc_ZeroDivisionError);
            return NULL;
        }

        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(result); i++) {
            result->data[i] = Matrix_DATA(first)[i] / second_value;
        }

        return (PyObject*) result;
    } else if (Matrix_Check(first) && PyFloat_Check(second)) {
        Matrix* result = Matrix_NewInternal(Matrix_SHAPE_I_INTERNAL(first), Matrix_SHAPE_J_INTERNAL(first), Matrix_TRANSPOSED(first));
        if (result == NULL) {
            return NULL;
        }

        float second_value = (float) PyFloat_AsDouble(second);
        if (second_value == 0.0f) {
            Py_DECREF(result);
            PyErr_SetNone(PyExc_ZeroDivisionError);
            return NULL;
        }

        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(result); i++) {
            result->data[i] = Matrix_DATA(first)[i] / second_value;
        }

        return (PyObject*) result;
    } else if (PyLong_Check(first) && Matrix_Check(second)) {
        Matrix* result = Matrix_NewInternal(Matrix_SHAPE_I_INTERNAL(second), Matrix_SHAPE_J_INTERNAL(second), Matrix_TRANSPOSED(second));
        if (result == NULL) {
            return NULL;
        }

        float first_value = (float) PyLong_AsLong(first);
        if (first_value == 0.0f) {
            Py_DECREF(result);
            PyErr_SetNone(PyExc_ZeroDivisionError);
            return NULL;
        }

        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(result); i++) {
            result->data[i] = first_value / Matrix_DATA(second)[i];
        }

        return (PyObject*) result;
    } else if (PyFloat_Check(first) && Matrix_Check(second)) {
        Matrix* result = Matrix_NewInternal(Matrix_SHAPE_I_INTERNAL(second), Matrix_SHAPE_J_INTERNAL(second), Matrix_TRANSPOSED(second));
        if (result == NULL) {
            return NULL;
        }

        float first_value = (float) PyFloat_AsDouble(first);
        if (first_value == 0.0f) {
            Py_DECREF(result);
            PyErr_SetNone(PyExc_ZeroDivisionError);
            return NULL;
        }

        Py_ssize_t i;
        for (i = 0; i < Py_SIZE(result); i++) {
            result->data[i] = first_value / Matrix_DATA(second)[i];
        }

        return (PyObject*) result;
    } else {
        PyObject* result = Py_NotImplemented;
        Py_INCREF(result);
        return result;
    }
}

static PyObject* Matrix_MatMultiply(PyObject* first, PyObject* second) {
    if (Matrix_Check(first) && Matrix_Check(second)) {
        if (Matrix_SHAPE_J(first) == Matrix_SHAPE_I(second)) {
            Matrix* fm = (Matrix*) first;
            Matrix* sm = (Matrix*) second;
            Py_ssize_t shape_i = Matrix_SHAPE_I(first);
            Py_ssize_t shape_m = Matrix_SHAPE_J(first);
            Py_ssize_t shape_j = Matrix_SHAPE_J(second);
            if (shape_i == 1 && shape_j == 1) {
                float result = 0.0f;
                Py_ssize_t m;
                for (m = 0; m < shape_m; m++) {
                    result += fm->data[m] * sm->data[m];
                }
                return PyFloat_FromDouble((double) result);
            } else {
                Matrix* result = Matrix_NewInternal(shape_i, shape_j, 0);
                if (result == NULL) {
                    return NULL;
                }
                Py_ssize_t i;
                for (i = 0; i < shape_i; i++) {
                    Py_ssize_t j;
                    for (j = 0; j < shape_j; j++) {
                        float temp = 0.0f;
                        Py_ssize_t m;
                        for (m = 0; m < shape_m; m++) {
                            Py_ssize_t flinidx = linearize_scalar_indices(shape_i, shape_m, i, m);
                            Py_ssize_t slinidx = linearize_scalar_indices(shape_m, shape_j, m, j);
                            temp += fm->data[flinidx] * sm->data[slinidx];
                        }
                        Py_ssize_t rlinidx = linearize_scalar_indices(shape_i, shape_j, i, j);
                        result->data[rlinidx] = temp;
                    }
                }
                return (PyObject*) result;
            }
        } else {
            PyErr_SetString(PyExc_ValueError, "Shape mismatch; the last dimension of the first and the first dimension of the second operand must be equal.");
            return NULL;
        }
    } else {
        PyObject* result = Py_NotImplemented;
        Py_INCREF(result);
        return result;
    }
}

static PyNumberMethods MatrixAsNumber = {
    (binaryfunc) Matrix_Add,
    (binaryfunc) Matrix_Subtract,
    (binaryfunc) Matrix_Multiply,
    0,  // Matrix_Remainder
    0,  // Matrix_Divmod
    0,  // Matrix_Power
    (unaryfunc) Matrix_Negative,
    (unaryfunc) Matrix_Positive,
    (unaryfunc) Matrix_Absolute,
    0,  // Matrix_Bool
    0,  // Matrix_Invert
    0,  // Matrix_LeftShift
    0,  // Matrix_RightShift
    0,  // Matrix_And
    0,  // Matrix_Xor
    0,  // Matrix_Or
    0,  // Matrix_Int
    0,  // Reserved
    0,  // Matrix_Float

    0,  // Matrix_InplaceAdd
    0,  // Matrix_InplaceSubtract
    0,  // Matrix_InplaceMultiply
    0,  // Matrix_InplaceRemainder
    0,  // Matrix_InplacePower
    0,  // Matrix_InplaceLeftShift
    0,  // Matrix_InplaceRightShift
    0,  // Matrix_InplaceAnd
    0,  // Matrix_InplaceXor
    0,  // Matrix_InplaceOr

    0,  // Matrix_FloorDivide
    (binaryfunc) Matrix_TrueDivide,
    0,  // Matrix_InplaceFloorDivide
    0,  // Matrix_InplaceTrueDivide

    0,  // Matrix_Index

    (binaryfunc) Matrix_MatMultiply,
    0,  // Matrix_InplaceMatMultiply
};

static PyMappingMethods MatrixAsMapping = {
    (lenfunc) Matrix_Length,
    (binaryfunc) Matrix_GetItem,
    (objobjargproc) Matrix_SetItem
};

static PyTypeObject MatrixType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "math.Matrix",                            /* tp_name */
    sizeof(Matrix),                           /* tp_basicsize */
    sizeof(float),                            /* tp_itemsize */
    (destructor) Matrix_Dealloc,              /* tp_dealloc */
    0,                                        /* tp_print */
    0,                                        /* tp_getattr */
    0,                                        /* tp_setattr */
    0,                                        /* tp_reserved */
    (reprfunc) Matrix_ToRepresentation,                   /* tp_repr */
    &MatrixAsNumber,                          /* tp_as_number */
    0,                                        /* tp_as_sequence */
    &MatrixAsMapping,                         /* tp_as_mapping */
    PyObject_HashNotImplemented,              /* tp_hash  */
    0,                                        /* tp_call */
    (reprfunc) Matrix_ToString,                    /* tp_str */
    0,                                        /* tp_getattro */
    0,                                        /* tp_setattro */
    0,                                        /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
    "Arbitrary size matrix (float32)",        /* tp_doc */
    0,                                        /* tp_traverse */
    0,                                        /* tp_clear */
    (richcmpfunc) Matrix_RichCompare,         /* tp_richcompare */
    0,                                        /* tp_weaklistoffset */
    0,                                        /* tp_iter */
    0,                                        /* tp_iternext */
    0,                                        /* tp_methods */
    0,                                        /* tp_members */
    0,                                        /* tp_getset */
    0,                                        /* tp_base */
    0,                                        /* tp_dict */
    0,                                        /* tp_descr_get */
    0,                                        /* tp_descr_set */
    0,                                        /* tp_dictoffset */
    0,                                        /* tp_init */
    0,                                        /* tp_alloc */
    Matrix_New,                               /* tp_new */
    PyObject_Del,                             /* tp_free */
};

static struct PyModuleDef MathModule = {
   PyModuleDef_HEAD_INIT,
   "_math",   /* name of module */
   "A collection of math classes and functions.", /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
   NULL, NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC PyInit__math(void) {
    PyObject* m;

    if (PyType_Ready(&MatrixType) < 0)
        return NULL;

    m = PyModule_Create(&MathModule);
    if (m == NULL)
        return NULL;

    Py_INCREF(&MatrixType);
    PyModule_AddObject(m, "Matrix", (PyObject*) &MatrixType);
    return m;
}
