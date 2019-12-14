#!/bin/sh
codeclose protect -s $1 -e $1/__main__.py keys/code_encrypting.key protected_$1 -k args -a args
