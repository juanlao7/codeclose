#!/bin/sh
codeclose protect --src $1 --encryption-excluded $1/__main__.py --encryption-excluded $1/__init__.py --encryption-excluded $1/unencrypted_submodule.py keys/code_encrypting.key protected --keep-identifier args --keep-attributes args 
cp keys/code_encrypting.key protected/$1
cp keys/pk_verifying-public.pem protected/$1