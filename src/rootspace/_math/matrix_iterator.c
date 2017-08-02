#include "matrix_iterator.h"
#include "matrix.h"

const char MatrixIterator_Docstring[] = "Provides an iterator interface to Matrix.";

MatrixIterator* MatrixIterator_NewInternal(Matrix* matrix, Py_ssize_t idx, Py_ssize_t idx_max, int iter_columns) {
    MatrixIterator* matrix_iter = PyObject_New(MatrixIterator, &MatrixIteratorType);
    if (matrix_iter == NULL) {
        return NULL;
    }

    Py_INCREF(matrix);
    matrix_iter->matrix = matrix;
    matrix_iter->idx = idx;
    matrix_iter->idx_max = idx_max;
    matrix_iter->iter_columns = iter_columns;

    return matrix_iter;
}

static PyObject* MatrixIterator_New(PyTypeObject* type, PyObject* args, PyObject* kwargs) {
    PyObject* matrix = NULL;
    Py_ssize_t idx = 0;
    Py_ssize_t idx_max = 1;
    int iter_columns = 0;
    static char* kwlist[] = {"", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O!nnp", kwlist, MatrixType, &matrix, &idx, &idx_max, &iter_columns)) {
        return NULL;
    }
    return (PyObject*) MatrixIterator_NewInternal((Matrix*) matrix, idx, idx_max, iter_columns);
}

static void MatrixIterator_Dealloc(MatrixIterator* self) {
    Py_XDECREF(self->matrix);
    Py_TYPE(self)->tp_free((PyObject*) self);
}

static PyObject* MatrixIterator_GetIter(MatrixIterator* self) {
    Py_INCREF(self);
    return (PyObject*) self;
}

static PyObject* MatrixIterator_Next(MatrixIterator* self) {
    if (0 <= self->idx && self->idx < self->idx_max) {
        if (!self->iter_columns) {
            PyObject* idx_i = PyLong_FromSsize_t(self->idx);
            if (idx_i == NULL) {
                return NULL;
            }
            self->idx += 1;
            PyObject* result = Matrix_GetItem(self->matrix, idx_i);
            Py_DECREF(idx_i);
            return result;
        } else {
            PyObject* idx = PyTuple_New(2);
            if (idx == NULL) {
                return NULL;
            }
            PyObject* idx_i = PySlice_New(NULL, NULL, NULL);
            if (idx_i == NULL) {
                Py_DECREF(idx);
                return NULL;
            }
            PyObject* idx_j = PyLong_FromSsize_t(self->idx);
            if (idx_j == NULL) {
                Py_DECREF(idx_i);
                Py_DECREF(idx);
                return NULL;
            }
            PyTuple_SetItem(idx, 0, idx_i);
            PyTuple_SetItem(idx, 1, idx_j);
            self->idx += 1;
            PyObject* result = Matrix_GetItem(self->matrix, idx);
            Py_DECREF(idx);
            return result;
        }
    } else {
        PyErr_SetNone(PyExc_StopIteration);
        return NULL;
    }
}

PyTypeObject MatrixIteratorType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "_math._MatrixIterator",                  /* tp_name */
    sizeof(MatrixIterator),                   /* tp_basicsize */
    0,                                        /* tp_itemsize */
    (destructor) MatrixIterator_Dealloc,      /* tp_dealloc */
    0,                                        /* tp_print */
    0,                                        /* tp_getattr */
    0,                                        /* tp_setattr */
    0,                                        /* tp_reserved */
    0,                                        /* tp_repr */
    0,                                        /* tp_as_number */
    0,                                        /* tp_as_sequence */
    0,                                        /* tp_as_mapping */
    0,                                        /* tp_hash  */
    0,                                        /* tp_call */
    0,                                        /* tp_str */
    0,                                        /* tp_getattro */
    0,                                        /* tp_setattro */
    0,                                        /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,                       /* tp_flags */
    MatrixIterator_Docstring,                 /* tp_doc */
    0,                                        /* tp_traverse */
    0,                                        /* tp_clear */
    0,                                        /* tp_richcompare */
    0,                                        /* tp_weaklistoffset */
    (getiterfunc) MatrixIterator_GetIter,     /* tp_iter */
    (iternextfunc) MatrixIterator_Next,       /* tp_iternext */
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
    MatrixIterator_New,                       /* tp_new */
    PyObject_Del                              /* tp_free */
};