package hello_test

import (
    "hello"
    "testing"
)

func TestHello(t *testing.T) {
   if err := hello.Hello(); err != nil {
        t.Error("Hello, World?")
   }
}
