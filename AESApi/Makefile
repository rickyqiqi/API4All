#
# CSC DL PORT - Makefile
#
# Copyright (c) 
#
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# platform dependencies
# ---------------------------------------------------------------------------
CC	    = gcc
CXX	    = g++
AR      = ar

OSHOST  = $(shell "uname -s")

# ---------------------------------------------------------------------------
# project specifics
# ---------------------------------------------------------------------------
#set Debug or Release
#COMPILE_VARIABLE   = Debug

DEFINES     += 

ifeq ($(COMPILE_VARIABLE),Debug)
CFLAGS	    += -g -Wall $(DEFINES)
else
CFLAGS	    += -O2 -Wall -DNDEBUG $(DEFINES)
endif
CFLAGS      += -I./ -I/usr/include/python2.6/

# here to add "-Wl,-Bsymbolic" to avoid symbolic confilict in different 
# libraries in using same variable or function names
LDFLAGS     += -Wl,-Bsymbolic -fPIC -shared -lpython2.6

TGT         = $$PWD/AESApiTest/AESApi.so
CSRC        = 
CXXSRC      = ./AESApi.cpp

ASRC        = 
OBJS        = $(CSRC:.c=.o)  $(CXXSRC:.cpp=.o) $(ASRC:.S=.o)
BIN         = $(TGT)
LIBS        = 

###########################################
# feature special files to add here       #
###########################################

.PHONY: clean all

all: $(BIN)

$(BIN): $(OBJS)
	$(CXX) $(CFLAGS) $(OBJS) -o $@ $(LDFLAGS) $(LIBS)

clean:
	rm -f $(OBJS)
	rm -f $(BIN)

# ---------------------------------------------------------------------------
# rules for code generation
# ---------------------------------------------------------------------------
%.o:    %.c
	$(CC) $(CFLAGS) -o $@ -c $<

%.o:    %.cpp
	$(CXX) $(CFLAGS) -o $@ -c $<

%.o:    %.S
	$(CC) $(ASFLAGS) -o $@ -c $<


