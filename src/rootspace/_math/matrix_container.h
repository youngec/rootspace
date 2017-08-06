#ifndef MATRIX_CONTAINER_H
#define MATRIX_CONTAINER_H
#define PY_SSIZE_T_CLEAN
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
extern PyTypeObject MatrixContainerType;

/// Declare the MatrixContainer docstring.
extern const char MatrixContainer_Docstring[];

/// The following macros allow for non-exact and exact type checking against
/// MatrixContainer.
#define MatrixContainer_Check(op) PyObject_TypeCheck(op, &MatrixContainerType)
#define MatrixContainer_CheckExact(op) (Py_TYPE(op) == &MatrixContainerType)

/// *Internal* Create a new MatrixContainer object. Does not initialize
/// the underlying data! Does not check for the sanity of arguments!
MatrixContainer* MatrixContainer_NewInternal(Py_ssize_t length);
#endif