#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include "_index_handling.h"
#include "_matrix_container.h"
#include "_matrix.h"


static PyMethodDef MathMethods[] = {
    {"get_sub_shape", math_get_sub_shape, METH_VARARGS, math_get_sub_shape_doc},
    {"linearize_indices", math_linearize_indices, METH_VARARGS, math_linearize_indices_doc},
    {"complete_indices", math_complete_indices, METH_VARARGS, math_complete_indices_doc},
    {"select_all", math_select_all, METH_VARARGS, math_select_all_doc},
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
