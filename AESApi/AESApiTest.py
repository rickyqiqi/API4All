#! /usr/bin/python

from ctypes import *

class point(Structure):
    _fields_ = [
        ("x", c_int),
        ("y", c_int)
    ]

ptr = point(10, 20)
libpoint = CDLL("./libAESApi.so")
libpoint.point_print(byref(ptr))
libpoint.point_print(pointer(ptr))