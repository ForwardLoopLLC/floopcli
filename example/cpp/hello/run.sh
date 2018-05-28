#!/bin/bash

# compile with g++
# produces binary hello, which runs immediately
g++ /floop/src/hello.cpp /floop/src/main.cpp \
    -o /floop/hello && \
    /floop/hello
