from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers import algorithms
from base64 import b64decode

__LICENSE__ = None

def expose(encryptedContent, initializationVector, originalLength):
    license = getLicense()
    decryptor = Cipher(license['aes'], modes.CBC(b64decode(initializationVector)), backend=default_backend()).decryptor()
    content = decryptor.update(b64decode(encryptedContent)) + decryptor.finalize()
    return content[:originalLength]

def getLicense():
    global __LICENSE__
    
    if __LICENSE__ is None:
        __LICENSE__ = {}

        with open('C:\\projects\\protopipe\\engine\\codeclose_keys\\source_code.key', 'rb') as handler:
            __LICENSE__['aes'] = algorithms.AES(handler.read())

    return __LICENSE__
