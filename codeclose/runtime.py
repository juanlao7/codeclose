import time
import os
from base64 import b64encode, b64decode, b32decode
from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import AES
from Cryptodome.Hash import SHAKE256
from Cryptodome.Util.number import bytes_to_long

from .errors import InvalidProductKey, InvalidProductId, ExpiredLicense

_license = None

DEFAULT_LICENSE_ID_SIZE = 24
DEFAULT_PRODUCT_ID_SIZE = 8
DEFAULT_EXPIRATION_TIME_SIZE = 40
DEFAULT_HASH_SIZE = 6

def configure(productKey=None, verifyingPublicKey=None, encryptingKey=None, expectedProductIds=None, licenseIdSize=DEFAULT_LICENSE_ID_SIZE, productIdSize=DEFAULT_PRODUCT_ID_SIZE, expirationTimeSize=DEFAULT_EXPIRATION_TIME_SIZE, hashSize=DEFAULT_HASH_SIZE):
    global _productKey, _verifyingPublicKey, _encryptingKey, _expectedProductIds, _licenseIdSize, _productIdSize, _expirationTimeSize, _hashSize
    _productKey = productKey
    _verifyingPublicKey = verifyingPublicKey
    _encryptingKey = encryptingKey
    _expectedProductIds = expectedProductIds
    _licenseIdSize = licenseIdSize
    _productIdSize = productIdSize
    _expirationTimeSize = expirationTimeSize
    _hashSize = hashSize

def expose(encryptedContent, initializationVector, originalSize):
    try:
        license = getLicense()
    except:
        return ''
    
    cipher = AES.new(license['encryptingKey'], AES.MODE_CBC, iv=b64decode(initializationVector))
    contentBytes = cipher.decrypt(b64decode(encryptedContent))
    return contentBytes[:originalSize].decode('utf-8')

def validate(exitOnException=True):
    global _expectedProductIds

    try:
        license = getLicense()

        if _expectedProductIds is None or license['productId'] not in _expectedProductIds:
            raise InvalidProductId()

        if license['currentTime'] > license['expirationTime']:
            raise ExpiredLicense(license['expirationTime'])
        
        return license
    except BaseException as e:
        if exitOnException:
            os._exit(1)     # Without triggering SystemExit exception.
        else:
            raise e

def getLicense():
    global _license, _productKey
    
    if _license is None:
        if _productKey is None:
            raise InvalidProductKey
        
        if _verifyingPublicKey is not None and _expectedProductIds is not None and _encryptingKey is not None:
            # Computing the license locally.
            verifyingPublicKeyInstance = RSA.import_key(_verifyingPublicKey)
            encryptingKeyString = b64encode(_encryptingKey).decode('utf-8')
            _license = computeLicense(_productKey, verifyingPublicKeyInstance, encryptingKeyString, _expectedProductIds, _licenseIdSize, _productIdSize, _expirationTimeSize, _hashSize)

        # TODO: obtain the license from the remote server

        if 'encryptingKey' in _license:
            _license['encryptingKey'] = b64decode(_license['encryptingKey'].encode('utf-8'))
    
    return _license

def computeLicense(productKey, verifyingPublicKeyInstance, encryptingKeyString, expectedProductIds, licenseIdSize, productIdSize, expirationTimeSize, hashSize):
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
