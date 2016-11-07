#! /usr/bin/python

from AESApi import *

plain = "plain text string"
encrypt = AESEncrypt(plain)
print encrypt
decrypt = AESDecrypt(encrypt)
print decrypt
