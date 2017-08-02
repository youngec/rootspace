#include "quaternion.h"

const char Quaternion_Docstring[] = "missing docstring";

Quaternion* Quaternion_NewInternal(MatrixDataType r, MatrixDataType i, MatrixDataType j, MatrixDataType k) {
    Quaternion* quat = PyObject_New(Quaternion, &QuaternionType);
    if (quat == NULL) {
        return NULL;
    }

    quat->r = r;
    quat->i = i;
    quat->j = j;
    quat->k = k;

    return quat;
}

static PyObject* Quaternion_New(PyTypeObject* type, PyObject* args, PyObject* kwargs) {
    double r = 1.0;
    double i = 0.0;
    double j = 0.0;
    double k = 0.0;
    static char* kwlist[] = {"r", "i", "j", "k", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|dddd", kwlist, &r, &i, &j, &k)) {
        return NULL;
    }
    return (PyObject*) Quaternion_NewInternal((MatrixDataType) r, (MatrixDataType) i, (MatrixDataType) j, (MatrixDataType) k);
}

static void Quaternion_Dealloc(Quaternion* self) {
    Py_TYPE(self)->tp_free((PyObject*) self);
}

PyTypeObject QuaternionType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "_math.Quaternion",                       /* tp_name */
    sizeof(Quaternion),                       /* tp_basicsize */
    0,                                        /* tp_itemsize */
    (destructor) Quaternion_Dealloc,          /* tp_dealloc */
    0,                                        /* tp_print */
    0,                                        /* tp_getattr */
    0,                                        /* tp_setattr */
    0,                                        /* tp_reserved */
    0,       /* tp_repr */
    0,                         /* tp_as_number */
    0,                                        /* tp_as_sequence */
    0,                        /* tp_as_mapping */
    0,                                        /* tp_hash  */
    0,                                        /* tp_call */
    0,               /* tp_str */
    0,                                        /* tp_getattro */
    0,                                        /* tp_setattro */
    0,                                        /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,                       /* tp_flags */
    Quaternion_Docstring,                     /* tp_doc */
    0,                                        /* tp_traverse */
    0,                                        /* tp_clear */
    0,         /* tp_richcompare */
    0,                                        /* tp_weaklistoffset */
    0,             /* tp_iter */
    0,                                        /* tp_iternext */
    0,                           /* tp_methods */
    0,                                        /* tp_members */
    0,                        /* tp_getset */
    0,                                        /* tp_base */
    0,                                        /* tp_dict */
    0,                                        /* tp_descr_get */
    0,                                        /* tp_descr_set */
    0,                                        /* tp_dictoffset */
    0,                                        /* tp_init */
    0,                                        /* tp_alloc */
    Quaternion_New,                           /* tp_new */
    PyObject_Del                              /* tp_free */
};