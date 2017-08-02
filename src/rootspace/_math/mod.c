#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include "index_handling.h"
#include "matrix_container.h"
#include "matrix.h"
#include "matrix_iterator.h"
#include "quaternion.h"
// #include "physics.h"


static PyMethodDef MathMethods[] = {
    {"get_sub_shape", math_get_sub_shape, METH_VARARGS, math_get_sub_shape_doc},
    {"linearize_indices", math_linearize_indices, METH_VARARGS, math_linearize_indices_doc},
    {"complete_indices", math_complete_indices, METH_VARARGS, math_complete_indices_doc},
    {"select_all", math_select_all, METH_VARARGS, math_select_all_doc},
    // {"euler_step", math_euler_step, METH_VARARGS, math_euler_step_doc},
    // {"runge_kutta_4", math_runge_kutta_4, METH_VARARGS, math_runge_kutta_4_doc},
    // {"velocity_verlet", math_velocity_verlet, METH_VARARGS, math_velocity_verlet_doc},
    // {"equations_of_motion", math_equations_of_motion, METH_VARARGS, math_equations_of_motion_doc},
    // {"aabb_overlap", math_aabb_overlap, METH_VARARGS, math_aabb_overlap_doc},
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
    if (PyType_Ready(&MatrixContainerType) < 0) {
        return NULL;
    }

    if (PyType_Ready(&MatrixType) < 0) {
        return NULL;
    }

    if (PyType_Ready(&MatrixIteratorType) < 0) {
        return NULL;
    }

    if (PyType_Ready(&QuaternionType) < 0) {
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

    Py_INCREF(&MatrixIteratorType);
    PyModule_AddObject(m, "_MatrixIterator", (PyObject*) &MatrixIteratorType);

    Py_INCREF(&QuaternionType);
    PyModule_AddObject(m, "Quaternion", (PyObject*) &QuaternionType);
    return m;
}
