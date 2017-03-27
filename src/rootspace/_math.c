#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include "_matrix_container.h"
#include "_matrix.h"

/// Define the _math module.
static struct PyModuleDef MathModule = {
   PyModuleDef_HEAD_INIT,
   "_math",  // Module name
   "A collection of math classes and functions.",  // Module docstring
   -1,
   NULL, NULL, NULL, NULL, NULL
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
