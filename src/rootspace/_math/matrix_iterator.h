#ifndef MATRIX_ITERATOR_H
#define MATRIX_ITERATOR_H
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "matrix.h"

/// The MatrixIterator object contains a pointer to a Matrix object.
typedef struct {
    PyObject_HEAD
    Matrix* matrix;
    Py_ssize_t idx;
    Py_ssize_t idx_max;
    int iter_columns;
} MatrixIterator;

/// Declare the MatrixIterator type object.
extern PyTypeObject MatrixIteratorType;

/// Declare the MatrixIterator docstring.
extern const char MatrixIterator_Docstring[];

/// The following macros allow for non-exact and exact type checking against
/// Matrix.
#define MatrixIterator_Check(op) PyObject_TypeCheck(op, &MatrixIteratorType)
#define MatrixIterator_CheckExact(op) (Py_TYPE(op) == &MatrixIteratorType)

/// *Internal* Create a new MatrixIterator object. Accepts a Matrix object.
/// Does not do any sanity checking on the arguments!
MatrixIterator* MatrixIterator_NewInternal(Matrix* matrix, Py_ssize_t idx, Py_ssize_t idx_max, int iter_columns);
#endif