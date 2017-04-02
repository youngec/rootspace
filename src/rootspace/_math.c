#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include "_index_handling.h"
#include "_matrix_container.h"
#include "_matrix.h"

static const char math_get_sub_shape_doc[] =
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

static const char math_linearize_indices_doc[] =
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

static const char math_complete_indices_doc[] =
    "For a given int, tuple[int] or slice, return a corresponding two-tuple \n"
    "of the form (indices, slice(None, None, None)). \n"
    "\n"
    "Parameters: \n"
    "indices: Union[int, Tuple[int], slice] \n"
    "\n"
    "Returns: \n"
    "2-Tuple[Union[int, Tuple[int], slice]]";

static const char math_select_all_doc[] =
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
