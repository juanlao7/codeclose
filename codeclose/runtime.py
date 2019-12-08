import time
import os
from base64 import b64encode, b64decode, b32decode
from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import AES
from Cryptodome.Hash import SHAKE256
from Cryptodome.Util.number import bytes_to_long

from .errors import InvalidProductKey, InvalidProductId, ExpiredLicense

__settings__ = None
__license__ = None

DEFAULT_LICENSE_ID_SIZE = 24
DEFAULT_PRODUCT_ID_SIZE = 8
DEFAULT_EXPIRATION_TIME_SIZE = 40
DEFAULT_HASH_SIZE = 6

def configure(**settings):
    global __settings__
    __settings__ = settings

def expose(encryptedContent, initializationVector, originalLength):
    try:
        license = getLicense()
    except:
        return ''
    
    cipher = AES.new(license['encryptingKey'], AES.MODE_CBC, iv=b64decode(initializationVector))
    content = cipher.decrypt(b64decode(encryptedContent))
    return content[:originalLength]

def validate(exitOnException=True):
    global __settings__

    try:
        license = getLicense()

        if license['productId'] not in __settings__.get('expectedProductIds', []):
            raise InvalidProductId

        if license['currentTime'] > license['expirationTime']:
            raise ExpiredLicense
    except BaseException as e:
        if exitOnException:
            os._exit(1)     # Without triggering SystemExit exception.
        else:
            raise e

def getLicense():
    global __settings__, __license__
    
    if __license__ is None:
        if 'productKey' not in __settings__:
            raise InvalidProductKey
        
        if 'verifyingPublicKey' in __settings__ and 'expectedProductIds' in __settings__ and 'encryptingKey' in __settings__:
            # Computing the license locally.
            verifyingPublicKeyInstance = RSA.import_key(__settings__['verifyingPublicKey'])
            licenseIdSize = __settings__.get('licenseIdSize', DEFAULT_LICENSE_ID_SIZE)
            productIdSize = __settings__.get('productIdSize', DEFAULT_PRODUCT_ID_SIZE)
            expirationTimeSize = __settings__.get('expirationTimeSize', DEFAULT_EXPIRATION_TIME_SIZE)
            hashSize = __settings__.get('hashSize', DEFAULT_HASH_SIZE)
            expectedProductIds = __settings__['expectedProductIds']
            encryptingKeyString = b64encode(__settings__['encryptingKey']).decode('utf-8')
            __license__ = computeLicense(verifyingPublicKeyInstance, licenseIdSize, productIdSize, expirationTimeSize, hashSize, expectedProductIds, encryptingKeyString, __settings__['productKey'])

        # TODO: obtain the license from the remote server

        if 'encryptingKey' in __license__:
            __license__['encryptingKey'] = b64decode(__license__['encryptingKey'].encode('utf-8'))
    
    return __license__

def computeLicense(verifyingPublicKeyInstance, licenseIdSize, productIdSize, expirationTimeSize, hashSize, expectedProductIds, encryptingKeyString, productKey):
    _, productId, expirationTime = readProductKey(verifyingPublicKeyInstance, licenseIdSize, productIdSize, expirationTimeSize, hashSize, productKey)

    license = {
        'productId': productId,
        'currentTime': int(time.time()),
        'expirationTime': expirationTime
    }

    if productId in expectedProductIds and expirationTime > license['currentTime']:
        license['encryptingKey'] = encryptingKeyString

    return license

def readProductKey(verifyingPublicKeyInstance, licenseIdSize, productIdSize, expirationTimeSize, hashSize, productKey):
    try:
        productKey = productKey.strip().replace('-', '').replace(' ', '')
        productKeyBytes = b32decode((productKey + '=' * (-len(productKey) % 8)).encode('utf-8'))
        productKeyLong = bytes_to_long(productKeyBytes)
        longValue = verifyingPublicKeyInstance._encrypt(productKeyLong)
        bitString = ('{:0' + str(licenseIdSize + productIdSize + expirationTimeSize + hashSize * 8) + 'b}').format(longValue)
        licenseId = int(bitString[:licenseIdSize], 2)
        productId = int(bitString[licenseIdSize:licenseIdSize + productIdSize], 2)
        expirationTime = int(bitString[licenseIdSize + productIdSize:licenseIdSize + productIdSize + expirationTimeSize], 2)
        computedHash = int(bitString[licenseIdSize + productIdSize + expirationTimeSize:], 2)

        shake = SHAKE256.new()
        shake.update(bitString[:licenseIdSize + productIdSize + expirationTimeSize].encode('utf-8'))
        
        if computedHash != bytes_to_long(shake.read(hashSize)):
            raise InvalidProductKey()

        return licenseId, productId, expirationTime
    except:
        raise InvalidProductKey()
