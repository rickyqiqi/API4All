#! /usr/bin/python

from ctypes import *

libpoint = CDLL("./libAESApi.so")
plainstr = create_string_buffer(b"plain text string") 
print sizeof(plainstr), repr(plainstr.raw)
# encrypt
encryptstr = libpoint.AESEncrypt(plainstr)
print encryptstr
# decrypt
decryptstr = libpoint.AESDecrypt(encryptstr)
print decryptstr
# Free string memory
libpoint.AESFreeMem(encryptstr)
libpoint.AESFreeMem(decryptstr)