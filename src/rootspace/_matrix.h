#ifndef MATRIX_H
#define MATRIX_H
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "_matrix_container.h"

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
PyTypeObject MatrixType;

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

/// *Internal* Create a new Matrix object. Accepts a two-dimensional shape
/// (N, M) and a transposition flag. Does not check for the sanity
/// of arguments!
Matrix* Matrix_NewInternal(Py_ssize_t N, Py_ssize_t M, int transposed);

/// Create a new Matrix object. Accepts a shape parameter, and optionally
/// a data and transposition parameter. The data parameter must be either
/// None, an integer, a floating point number, or a sequence. Raises a [TypeError]
/// otherwise. Also, if data is a sequence, its length must equal the product
/// of the shape. Raises a [ValueError] otherwise. Raises a [ValueError] if
/// the two-dimensional shape is not larger or equal to (1, 1).
PyObject* Matrix_New(PyTypeObject* type, PyObject* args, PyObject* kwargs);

/// Implement the Matrix destructor.
void Matrix_Dealloc(Matrix* self);

/// Implement the total ordering methods.
PyObject* Matrix_LessThan(PyObject* first, PyObject* second);
PyObject* Matrix_LessOrEqual(PyObject* first, PyObject* second);
PyObject* Matrix_Equal(PyObject* first, PyObject* second);
PyObject* Matrix_NotEqual(PyObject* first, PyObject* second);
PyObject* Matrix_GreaterOrEqual(PyObject* first, PyObject* second);
PyObject* Matrix_GreaterThan(PyObject* first, PyObject* second);
PyObject* Matrix_RichCompare(PyObject* first, PyObject* second, int op);

/// Provide a human-readable string representation of a Matrix.
PyObject* Matrix_ToString(Matrix* self);

/// Provide an eval-able representation of a Matrix.
PyObject* Matrix_ToRepresentation(Matrix* self);

/// Return the length of the Matrix. Depends on the length of the underlying
/// container and is always equal to the product of the Matrix shape.
Py_ssize_t Matrix_Length(Matrix* self);

PyObject* Matrix_GetItem(Matrix* self, PyObject* key);

int Matrix_SetItem(Matrix* self, PyObject* key, PyObject* value);
#endif