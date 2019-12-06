from Cryptodome.Cipher import AES
from base64 import b64decode

__LICENSE__ = None

def expose(encryptedContent, initializationVector, originalLength):
    license = getLicense()
    cipher = AES.new(license['codeCipherKey'], AES.MODE_CBC, iv=b64decode(initializationVector))
    content = cipher.decrypt(b64decode(encryptedContent))
    return content[:originalLength]

def getLicense():
    global __LICENSE__
    
    if __LICENSE__ is None:
        __LICENSE__ = {}

        with open('C:\\projects\\protopipe\\engine\\codeclose_keys\\source_code.key', 'rb') as handler:
            __LICENSE__['codeCipherKey'] = handler.read()

    return __LICENSE__
