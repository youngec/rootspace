#ifndef MATRIX_H
#define MATRIX_H
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "matrix_container.h"

/// The Matrix object contains a pointer to a MatrixContainer object,
/// as well as Matrix shape and transposition variables.
typedef struct {
    PyObject_HEAD
    MatrixContainer* container;
    Py_ssize_t N;
    Py_ssize_t M;
    int transposed;
} Matrix;

/// Declare the Matrix type object.
extern PyTypeObject MatrixType;

/// Declare the Matrix docstring
extern const char Matrix_Docstring[];

/// The following macros allow for non-exact and exact type checking against
/// Matrix.
#define Matrix_Check(op) PyObject_TypeCheck(op, &MatrixType)
#define Matrix_CheckExact(op) (Py_TYPE(op) == &MatrixType)

/// The following macros allow for easier access to the Matrix shape, depending
/// on whether the Matrix is Transposed or not.
#define Matrix_N(op) (((Matrix*) op)->N)
#define Matrix_M(op) (((Matrix*) op)->M)
#define Matrix_TRANSPOSED(op) (((Matrix*) op)->transposed)
#define Matrix_SHAPE_I(op) (Matrix_TRANSPOSED(op) ? Matrix_M(op) : Matrix_N(op))
#define Matrix_SHAPE_J(op) (Matrix_TRANSPOSED(op) ? Matrix_N(op) : Matrix_M(op))

/// The following macros allow for easier access to Matrix length and data
#define Matrix_SIZE(op) (Py_SIZE(((Matrix*) op)->container))
#define Matrix_DATA(op) (((Matrix*) op)->container->data)

/// Implemented the Python math module isclose function.
int is_close(double a, double b, double rel_tol, double abs_tol);

/// *Internal* Create a new Matrix object and populate the structure with
/// the function arguments.
/// Does not check for the sanity of arguments!
Matrix* Matrix_NewInternalShallow(Py_ssize_t N, Py_ssize_t M, int transposed, MatrixContainer* container);

/// *Internal* Create a new Matrix object and the underlying container object.
/// Accepts a two-dimensional shape (N, M) and a transposition flag.
/// Does not check for the sanity of arguments!
Matrix* Matrix_NewInternal(Py_ssize_t N, Py_ssize_t M, int transposed);

/// *Internal* Create a new identity matrix object. Accepts a single
/// integer that indicates the dimension of the matrix.
/// Does not check for the sanity of arguments!
Matrix* Matrix_IdentityInternal(Py_ssize_t d);

/// Matrix_GetItem is used by MatrixIterator in MatrixIterator_Next.
PyObject* Matrix_GetItem(Matrix* self, PyObject* key);
#endif