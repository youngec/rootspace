#define PY_SSIZE_T_CLEAN

#include <Python.h>

static Py_ssize_t linearize_scalar_indices(Py_ssize_t shape_i, Py_ssize_t shape_j, Py_ssize_t i, Py_ssize_t j) {
    return i * shape_j + j;
}

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

static void Matrix_dealloc(Matrix* self) {
    PyMem_Del(self->data);
    Py_TYPE(self)->tp_free((PyObject*) self);
}

static PyObject* Matrix_str(Matrix* self) {
    PyObject* rows = PyList_New(self->shape_i);
    Py_ssize_t i;
    for (i = 0; i < self->shape_i; i++) {
        PyObject* row = PyList_New(self->shape_j);
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

static PyObject* Matrix_repr(Matrix* self) {
    PyObject* d = PyTuple_New(Py_SIZE(self));
    Py_ssize_t idx;
    for (idx = 0; idx < Py_SIZE(self); idx++) {
        PyTuple_SetItem(d, idx, PyFloat_FromDouble((double) self->data[idx]));
    }

    PyObject* s = PyUnicode_FromFormat("Matrix((%u, %u), %R, transposed=%u)", self->shape_i, self->shape_j, d, self->transposed);
    Py_DECREF(d);
    return s;
}

static PyObject* Matrix_new(PyTypeObject* type, PyObject* args, PyObject* kwargs) {
    Py_ssize_t shape_i = 0;
    Py_ssize_t shape_j = 0;
    PyObject* data = NULL;
    int transposed = 0;
    Py_ssize_t length = 0;
    float* array_data = NULL;

    static char* kwlist[] = {"", "", "transposed", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "(ll)O|$p", kwlist, &shape_i, &shape_j, &data, &transposed)) {
        return NULL;
    }

    if (shape_i > 0 && shape_j > 0) {
        length = shape_i * shape_j;
    } else {
        PyErr_SetString(PyExc_ValueError, "Expected the shape to be larger or equal to (1, 1).");
        return NULL;
    }

    Matrix* self = (Matrix*) type->tp_alloc(type, 0);
    if (self != NULL) {
        self->data = PyMem_New(float, length);
        if (self->data == NULL) {
            Py_DECREF(self);
            PyErr_SetNone(PyExc_MemoryError);
            return NULL;
        }

        if (PyLong_Check(data)) {
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
        } else if (PyTuple_Check(data)) {
            if (PyTuple_Size(data) != length) {
                Py_DECREF(self);
                PyErr_SetString(PyExc_ValueError, "The number of elements in data must correspond to the shape!");
                return NULL;
            }
            Py_ssize_t idx;
            for (idx = 0; idx < length; idx++) {
                PyObject* item = PyTuple_GetItem(data, idx);
                if (PyLong_Check(item)) {
                    self->data[idx] = (float) PyLong_AsLong(data);
                } else if (PyFloat_Check(item)) {
                    self->data[idx] = (float) PyFloat_AsDouble(data);
                } else {
                    Py_DECREF(self);
                    PyErr_SetString(PyExc_TypeError, "Expected elements of the tuple to be either integers or floats.");
                    return NULL;
                }
            }
        } else {
            Py_DECREF(self);
            PyErr_SetString(PyExc_TypeError, "Expected data to be either an integer, a float or a tuple.");
            return NULL;
        }

        self->shape_i = shape_i;
        self->shape_j = shape_j;
        self->transposed = transposed;
        Py_SIZE(self) = length;
    }

    return (PyObject*) self;
}

static PyTypeObject MatrixType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "math.Matrix",                            /* tp_name */
    sizeof(Matrix),                           /* tp_basicsize */
    sizeof(float),                            /* tp_itemsize */
    (destructor) Matrix_dealloc,              /* tp_dealloc */
    0,                                        /* tp_print */
    0,                                        /* tp_getattr */
    0,                                        /* tp_setattr */
    0,                                        /* tp_reserved */
    (reprfunc) Matrix_repr,                   /* tp_repr */
    0,                                        /* tp_as_number */
    0,                                        /* tp_as_sequence */
    0,                                        /* tp_as_mapping */
    PyObject_HashNotImplemented,              /* tp_hash  */
    0,                                        /* tp_call */
    (reprfunc) Matrix_str,                    /* tp_str */
    0,                                        /* tp_getattro */
    0,                                        /* tp_setattro */
    0,                                        /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
    "Arbitrary size matrix (float32)",        /* tp_doc */
    0,                                        /* tp_traverse */
    0,                                        /* tp_clear */
    0,                                        /* tp_richcompare */
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
    Matrix_new,                               /* tp_new */
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
    PyModule_AddObject(m, "Matrix", (PyObject *)&MatrixType);
    return m;
}
