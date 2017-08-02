#ifndef QUATERNION_H
#define QUATERNION_H
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "matrix_container.h"

typedef struct {
    PyObject_HEAD
    MatrixDataType r;
    MatrixDataType i;
    MatrixDataType j;
    MatrixDataType k;
} Quaternion;

extern PyTypeObject QuaternionType;
extern const char Quaternion_Docstring[];

#define Quaternion_Check(op) PyObject_TypeCheck(op, &QuaternionType)
#define Quaternion_CheckExact(op) (Py_TYPE(op) == &QuaternionType)

Quaternion* Quaternion_New_Internal(MatrixDataType r, MatrixDataType i, MatrixDataType j, MatrixDataType k);
#endif