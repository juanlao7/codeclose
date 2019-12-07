import time
from Cryptodome.Cipher import AES
from base64 import b64decode

from .errors import InvalidProductKey

__productKey__ = None
__license__ = None

def expose(encryptedContent, initializationVector, originalLength):
    try:
        license = getLicense()
    except:
        return ''
    
    cipher = AES.new(license['codeCipherKey'], AES.MODE_CBC, iv=b64decode(initializationVector))
    content = cipher.decrypt(b64decode(encryptedContent))
    return content[:originalLength]

def getLicense():
    global __productKey__, __license__
    
    if __license__ is None:
        if __productKey__ is None:
            raise InvalidProductKey

        __license__ = {
            'productId': 1,
            'currentTime': int(time.time()),
            'expirationTime': 1577836800
        }

        with open('C:\\projects\\protopipe\\engine\\codeclose_keys\\code_encrypting.key', 'rb') as handler:
            __license__['codeCipherKey'] = handler.read()

    return __license__

def setProductKey(productKey, expectedProductIds, exitOnException=False):
    global __productKey__
    __productKey__ = productKey
    from . import validation

    try:
        if not hasattr(validation, 'validate'):
            raise InvalidProductKey
        
        validation.validate(expectedProductIds, exitOnException)
    except BaseException as e:
        if exitOnException:
            os._exit(1)     # Without triggering SystemExit exception.
        else:
            raise e
