#ifndef PHYSICS_H
#define PHYSICS_H
#define PY_SSIZE_T_CLEAN
#include <Python.h>

PyObject* math_euler_step(PyObject* self, PyObject* args);
extern const char math_euler_step_doc[];

PyObject* math_runge_kutta_4(PyObject* self, PyObject* args);
extern const char math_runge_kutta_4_doc[];

PyObject* math_velocity_verlet(PyObject* self, PyObject* args);
extern const char math_velocity_verlet_doc[];

PyObject* math_equations_of_motion(PyObject* self, PyObject* args);
extern const char math_equations_of_motion_doc[];

PyObject* math_aabb_overlap(PyObject* self, PyObject* args);
extern const char math_aabb_overlap_doc[];
#endif