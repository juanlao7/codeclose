import time
import os
from base64 import b64encode, b64decode, b32decode
from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import AES
from Cryptodome.Hash import SHAKE256
from Cryptodome.Util.number import bytes_to_long

from .errors import InvalidProductKey, InvalidProductId, ExpiredLicense

_settings = None
_license = None

DEFAULT_LICENSE_ID_SIZE = 24
DEFAULT_PRODUCT_ID_SIZE = 8
DEFAULT_EXPIRATION_TIME_SIZE = 40
DEFAULT_HASH_SIZE = 6

def configure(**settings):
    global _settings
    _settings = settings

def expose(encryptedContent, initializationVector, originalSize):
    try:
        license = getLicense()
    except:
        return ''
    
    cipher = AES.new(license['encryptingKey'], AES.MODE_CBC, iv=b64decode(initializationVector))
    contentBytes = cipher.decrypt(b64decode(encryptedContent))
    return contentBytes[:originalSize].decode('utf-8')

def validate(exitOnException=True):
    global _settings

    try:
        license = getLicense()

        if license['productId'] not in _settings.get('expectedProductIds', []):
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
    global _settings, _license
    
    if _license is None:
        if 'productKey' not in _settings:
            raise InvalidProductKey
        
        if 'verifyingPublicKey' in _settings and 'expectedProductIds' in _settings and 'encryptingKey' in _settings:
            # Computing the license locally.
            verifyingPublicKeyInstance = RSA.import_key(_settings['verifyingPublicKey'])
            licenseIdSize = _settings.get('licenseIdSize', DEFAULT_LICENSE_ID_SIZE)
            productIdSize = _settings.get('productIdSize', DEFAULT_PRODUCT_ID_SIZE)
            expirationTimeSize = _settings.get('expirationTimeSize', DEFAULT_EXPIRATION_TIME_SIZE)
            hashSize = _settings.get('hashSize', DEFAULT_HASH_SIZE)
            expectedProductIds = _settings['expectedProductIds']
            encryptingKeyString = b64encode(_settings['encryptingKey']).decode('utf-8')
            _license = computeLicense(verifyingPublicKeyInstance, licenseIdSize, productIdSize, expirationTimeSize, hashSize, expectedProductIds, encryptingKeyString, _settings['productKey'])

        # TODO: obtain the license from the remote server

        if 'encryptingKey' in _license:
            _license['encryptingKey'] = b64decode(_license['encryptingKey'].encode('utf-8'))
    
    return _license

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
