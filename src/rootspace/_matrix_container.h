#ifndef MATRIX_CONTAINER_H
#define MATRIX_CONTAINER_H
#include <Python.h>

/// The MatrixDataType is an alias to float.
typedef float MatrixDataType;

/// The MatrixContainer object contains the pointer to the underlying data.
/// The reason why MatrixContainer and Matrix are separated, is to take
/// advantage of reference counting.
typedef struct {
    PyObject_VAR_HEAD
    MatrixDataType data[1];
} MatrixContainer;

/// Declare the MatrixContainer type object.
static PyTypeObject MatrixContainerType;

/// The following macros allow for non-exact and exact type checking against
/// MatrixContainer.
#define MatrixContainer_Check(op) PyObject_TypeCheck(op, &MatrixContainerType)
#define MatrixContainer_CheckExact(op) (Py_TYPE(op) == &MatrixContainerType)

/// *Internal* Create a new MatrixContainer object and initialise the
/// underlying data to 0. Raises a [ValueError] if 'length' is not greater or
/// equal 1.
static MatrixContainer* MatrixContainer_NewInternal(Py_ssize_t length) {
    if (length <= 0) {
        PyErr_SetString(PyExc_ValueError, "Parameter 'length' must be greater or equal 1.");
        return NULL;
    }

    MatrixContainer* container = PyObject_NewVar(MatrixContainer, &MatrixContainerType, length);
    if (container == NULL) {
        return NULL;
    }

    for (Py_ssize_t i = 0; i < length; i++) {
        container->data[i] = (MatrixDataType) 0;
    }

    return container;
}

/// Create a new MatrixContainer object. Accepts only one parameter, length.
static PyObject* MatrixContainer_New(PyTypeObject* type, PyObject* args, PyObject* kwargs) {
    Py_ssize_t length = 0;
    static char* kwlist[] = {"length", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "l", kwlist, &length)) {
        return NULL;
    }
    return (PyObject*) MatrixContainer_NewInternal(length);
}

/// Implement the MatrixContainer object destructor.
static void MatrixContainer_Dealloc(MatrixContainer* self) {
    Py_TYPE(self)->tp_free((PyObject*) self);
}

/// Define the MatrixContainer type object.
static PyTypeObject MatrixContainerType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "_math._MatrixContainer",                 /* tp_name */
    sizeof(MatrixContainer) - sizeof(MatrixDataType),  /* tp_basicsize */
    sizeof(MatrixDataType),                   /* tp_itemsize */
    (destructor) MatrixContainer_Dealloc,    /* tp_dealloc */
    0,                                        /* tp_print */
    0,                                        /* tp_getattr */
    0,                                        /* tp_setattr */
    0,                                        /* tp_reserved */
    0,                                        /* tp_repr */
    0,                                        /* tp_as_number */
    0,                                        /* tp_as_sequence */
    0,                                        /* tp_as_mapping */
    PyObject_HashNotImplemented,              /* tp_hash  */
    0,                                        /* tp_call */
    0,                                        /* tp_str */
    0,                                        /* tp_getattro */
    0,                                        /* tp_setattro */
    0,                                        /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,                       /* tp_flags */
    "Internal Matrix data container object.", /* tp_doc */
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
    MatrixContainer_New,                      /* tp_new */
    PyObject_Del,                             /* tp_free */
};
#endif