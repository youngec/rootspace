#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include "_index_handling.h"
#include "_matrix_container.h"
#include "_matrix.h"

static PyObject* math_get_sub_shape(PyObject* self, PyObject* args) {
    Py_ssize_t N = 1;
    Py_ssize_t M = 1;
    int transposed = 0;
    PyObject* indices = NULL;
    if (!PyArg_ParseTuple(args, "nnpO", &N, &M, &transposed, &indices)) {
        return NULL;
    }
    return get_sub_shape(N, M, transposed, indices);
}

static PyObject* math_linearize_indices(PyObject* self, PyObject* args) {
    Py_ssize_t N = 1;
    Py_ssize_t M = 1;
    int transposed = 0;
    PyObject* indices = NULL;
    if (!PyArg_ParseTuple(args, "nnpO", &N, &M, &transposed, &indices)) {
        return NULL;
    }
    return linearize_indices(N, M, transposed, indices);
}

static PyObject* math_complete_indices(PyObject* self, PyObject* args) {
    PyObject* indices = NULL;
    if (!PyArg_ParseTuple(args, "O", &indices)) {
        return NULL;
    }
    return complete_indices(indices);
}

static PyObject* math_select_all(PyObject* self, PyObject* args) {
    Py_ssize_t N = 1;
    Py_ssize_t M = 1;
    int transposed = 0;
    if (!PyArg_ParseTuple(args, "nnp", &N, &M, &transposed)) {
        return NULL;
    }
    return select_all(N, M, transposed);
}


static PyMethodDef MathMethods[] = {
    {"get_sub_shape", math_get_sub_shape, METH_VARARGS, "Calculate the shape of a sub-matrix selected by given indices."},
    {"linearize_indices", math_linearize_indices, METH_VARARGS, "Calculate the tuple of linear indices from a given multi-dimensional index."},
    {"complete_indices", math_complete_indices, METH_VARARGS, "Expand the supplied index to a two-tuple multi-dimensional index."},
    {"select_all", math_select_all, METH_VARARGS, "Return a linear index that selects all elements, accounting for transposition."},
    {NULL, NULL, 0, NULL}
};

/// Define the _math module.
static struct PyModuleDef MathModule = {
   PyModuleDef_HEAD_INIT,
   "_math",  // Module name
   "A collection of math classes and functions.",  // Module docstring
   -1,
   MathMethods
};

/// Implement the _math module constructor.
///
/// # Module Members
/// * _MatrixContainer
/// * Matrix
PyMODINIT_FUNC PyInit__math(void) {
    if (PyType_Ready(&MatrixContainerType) < 0 || PyType_Ready(&MatrixType) < 0) {
        return NULL;
    }

    PyObject* m = PyModule_Create(&MathModule);
    if (m == NULL) {
        return NULL;
    }

    Py_INCREF(&MatrixContainerType);
    PyModule_AddObject(m, "_MatrixContainer", (PyObject*) &MatrixContainerType);

    Py_INCREF(&MatrixType);
    PyModule_AddObject(m, "Matrix", (PyObject*) &MatrixType);
    return m;
}
