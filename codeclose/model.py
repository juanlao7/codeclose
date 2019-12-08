import os
import textwrap
import inspect
import importlib
import time
from shutil import rmtree
from base64 import b64encode, b32encode
from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import AES
from Cryptodome.Hash import SHAKE256
from Cryptodome import Random
from Cryptodome.Util.number import bytes_to_long, long_to_bytes
from Cryptodome.Math.Numbers import Integer
from Cryptodome.Math.Primality import test_probable_prime

from .runtime import readProductKey as readProductKeyImpl
from .errors import InvalidProductKey

from .runtime import DEFAULT_LICENSE_ID_SIZE, DEFAULT_PRODUCT_ID_SIZE, DEFAULT_EXPIRATION_TIME_SIZE, DEFAULT_HASH_SIZE

DEFAULT_RSA_KEY_SIZE = 120
DEFAULT_RSA_PUBLIC_EXPONENT = 65537
DEFAULT_AES_KEY_SIZE = 256

__AES_POSSIBLE_SIZES__ = [128, 192, 256]

__PROTECTED_SOURCE_TEMPLATE__ = """from codeclose.runtime import expose
exec(expose({encryptedContent}, {initializationVector}, {originalLength}))"""

__INJECTED_CODECLOSE_MODULES__ = ['runtime', 'errors']

def generateSigningKeys(size=DEFAULT_RSA_KEY_SIZE, publicExponent=DEFAULT_RSA_PUBLIC_EXPONENT):
    key = __generateRSAKey__(size, e=publicExponent)
    return key.export_key('PEM'), key.publickey().export_key('PEM')

def generateEncryptingKey(size=DEFAULT_AES_KEY_SIZE):
    if size not in __AES_POSSIBLE_SIZES__:
        raise ValueError('Only possible key sizes are %s.' % ', '.join(__AES_POSSIBLE_SIZES__))

    return Random.get_random_bytes(size // 8)

def protect(encryptingKey, destinationDirectoryPath, sourceDirectoryPaths, encryptionExcludedFilePaths=[], followSymlinks=False):
    encryptionExcludedFilePaths = {os.path.abspath(x) for x in encryptionExcludedFilePaths}
    rmtree(destinationDirectoryPath)

    while os.path.exists(destinationDirectoryPath):
        pass
    
    os.makedirs(destinationDirectoryPath, exist_ok=True)
    currentPath = os.getcwd()
    injectionContent = __getInjectionContent__(encryptingKey, '')

    for srcPath in sourceDirectoryPaths:
        destPath = os.path.abspath(os.path.join(destinationDirectoryPath, os.path.basename(os.path.abspath(srcPath))))
        __injectContent__(injectionContent, destPath)
        os.chdir(srcPath)

        for root, _, fileNames in os.walk('.', followlinks=followSymlinks):
            codecloseModuleName = '.' * len(root.split(os.sep)) + '__codeclose__'

            for fileName in fileNames:
                if fileName.endswith('.py'):
                    srcFilePath = os.path.join(root, fileName)
                    destFilePath = os.path.join(destPath, srcFilePath)
                    os.makedirs(os.path.dirname(destFilePath), exist_ok=True)

                    with open(srcFilePath, 'r') as handler:
                        content = handler.read()
                        content = __remapModules__(content, codecloseModuleName)

                        if all(not os.path.samefile(srcFilePath, excludedFilePath) for excludedFilePath in encryptionExcludedFilePaths):
                            content = __encrypt__(content, encryptingKey, codecloseModuleName)

                    with open(destFilePath, 'w') as handler:
                        handler.write(content)
            
        os.chdir(currentPath)

def createProductKey(signingPrivateKey, licenseId, productId, expirationTime, groupsLength=None, licenseIdSize=DEFAULT_LICENSE_ID_SIZE, productIdSize=DEFAULT_PRODUCT_ID_SIZE, expirationTimeSize=DEFAULT_EXPIRATION_TIME_SIZE, hashSize=DEFAULT_HASH_SIZE):
    if licenseId > 2 ** licenseIdSize:
        raise ValueError('License ID is too big for its field size.')
    
    if productId > 2 ** productIdSize:
        raise ValueError('Product ID is too big for its field size.')
    
    if expirationTime > 2 ** expirationTimeSize:
        raise ValueError('Expiration time is too big for its field size.')

    privateKey = RSA.import_key(signingPrivateKey)
    privateKeySize = privateKey.size_in_bits()
    dataSize = licenseIdSize + productIdSize + expirationTimeSize + hashSize * 8

    if privateKeySize < dataSize:
        raise ValueError('The RSA key is too small (%s bits) for the data size (%s bits).' % (privateKeySize, dataSize))

    bitString = ('{:0' + str(licenseIdSize) + 'b}{:0' + str(productIdSize) + 'b}{:0' + str(expirationTimeSize) + 'b}').format(licenseId, productId, expirationTime)
    shake = SHAKE256.new()
    shake.update(bitString.encode('utf-8'))
    computedHash = bytes_to_long(shake.read(hashSize))
    bitString += ('{:0' + str(hashSize * 8) + 'b}').format(computedHash)
    longValue = int(bitString, 2)
    productKeyLong = privateKey._decrypt(longValue)
    productKeyBytes = long_to_bytes(productKeyLong)
    productKey = b32encode(productKeyBytes).decode('utf-8').replace('=', '')
    
    if groupsLength is not None:
        productKey = '-'.join(textwrap.wrap(productKey, groupsLength))
    
    return productKey

def readProductKey(verifyingPublicKey, productKey, licenseIdSize=DEFAULT_LICENSE_ID_SIZE, productIdSize=DEFAULT_PRODUCT_ID_SIZE, expirationTimeSize=DEFAULT_EXPIRATION_TIME_SIZE, hashSize=DEFAULT_HASH_SIZE):
    verifyingPublicKeyInstance = RSA.import_key(verifyingPublicKey)
    return readProductKeyImpl(verifyingPublicKeyInstance, licenseIdSize, productIdSize, expirationTimeSize, hashSize, productKey)

def configureResponseComputation(verifyingPublicKey, encryptingKey, expectedProductIds, licenseIdSize=DEFAULT_LICENSE_ID_SIZE, productIdSize=DEFAULT_PRODUCT_ID_SIZE, expirationTimeSize=DEFAULT_EXPIRATION_TIME_SIZE, hashSize=DEFAULT_HASH_SIZE):
    return {
        'verifyingPublicKeyInstance': RSA.import_key(verifyingPublicKey),
        'encryptingKeyString': b64encode(encryptingKey).decode('utf-8'),
        'expectedProductIds': expectedProductIds,
        'licenseIdSize': licenseIdSize,
        'productIdSize': productIdSize,
        'expirationTimeSize': expirationTimeSize,
        'hashSize': hashSize
    }

def computeResponse(configuration, productKey):
    _, productId, expirationTime = readProductKeyImpl(configuration.verifyingPublicKeyInstance, configuration.licenseIdSize, configuration.productIdSize, configuration.expirationTimeSize, configuration.hashSize, productKey)

    response = {
        ''
    }

    if productId not in expectedProductIds:
        raise InvalidProductId

    if int(time.time()) > expirationTime:
        raise ExpiredLicense

def __getInjectionContent__(encryptingKey, codecloseModuleName):
    injectionContent = {os.path.join('__codeclose__', '__init__.py'): ' '}

    for injectedModuleName in __INJECTED_CODECLOSE_MODULES__:
        injectedFilePath = os.path.join('__codeclose__', '%s.py' % injectedModuleName)
        injectedModule = importlib.import_module('codeclose.%s' % injectedModuleName)
        injectionContent[injectedFilePath] = inspect.getsource(injectedModule)

    return injectionContent

def __injectContent__(injectionContent, destPath):
    for injectedFilePath in injectionContent:
        destInjectedFilePath = os.path.join(destPath, injectedFilePath)
        os.makedirs(os.path.dirname(destInjectedFilePath), exist_ok=True)

        with open(destInjectedFilePath, 'w') as handler:
            handler.write(injectionContent[injectedFilePath])

def __remapModules__(content, codecloseModuleName):
    # TODO: use abstract syntax trees.
    
    for injectedModule in __INJECTED_CODECLOSE_MODULES__:
        content = content.replace('codeclose.%s' % injectedModule, '%s.%s' % (codecloseModuleName, injectedModule))
    
    return content

def __encrypt__(content, encryptingKey, codecloseModuleName):
    if not content:
        return content
    
    initializationVector = Random.get_random_bytes(16)
    cipher = AES.new(encryptingKey, AES.MODE_CBC, iv=initializationVector)
    encryptedContent = cipher.encrypt(__adaptForAES__(content.encode('utf-8')))

    content = __PROTECTED_SOURCE_TEMPLATE__.format(
        encryptedContent="'%s'" % b64encode(encryptedContent).decode('utf-8'),
        initializationVector="'%s'" % b64encode(initializationVector).decode('utf-8'),
        originalLength=len(content)
    )

    return __remapModules__(content, codecloseModuleName)

def __generateProbablePrime__(**kwargs):
    """Modified version of pycryptodome's Cryptodome.Math.Primality.generate_probable_prime to create primes of any size."""

    exact_bits = kwargs.pop("exact_bits", None)
    randfunc = kwargs.pop("randfunc", None)
    prime_filter = kwargs.pop("prime_filter", lambda x: True)
    if kwargs:
        raise ValueError("Unknown parameters: " + kwargs.keys())

    if exact_bits is None:
        raise ValueError("Missing exact_bits parameter")

    if randfunc is None:
        randfunc = Random.new().read

    result = 0
    while result == 0:
        candidate = Integer.random(exact_bits=exact_bits,
                                   randfunc=randfunc) | 1
        if not prime_filter(candidate):
            continue
        result = test_probable_prime(candidate, randfunc)
    return candidate

def __generateRSAKey__(bits, randfunc=None, e=65537):
    """Modified version of pycryptodome's Crypto.RSA.generate to allow keys of any size."""

    if e % 2 == 0 or e < 3:
        raise ValueError("RSA public exponent must be a positive, odd integer larger than 2.")

    if randfunc is None:
        randfunc = Random.get_random_bytes

    d = n = Integer(1)
    e = Integer(e)

    while n.size_in_bits() != bits and d < (1 << (bits // 2)):
        # Generate the prime factors of n: p and q.
        # By construciton, their product is always
        # 2^{bits-1} < p*q < 2^bits.
        size_q = bits // 2
        size_p = bits - size_q

        min_p = min_q = (Integer(1) << (2 * size_q - 1)).sqrt()
        if size_q != size_p:
            min_p = (Integer(1) << (2 * size_p - 1)).sqrt()

        def filter_p(candidate):
            return candidate > min_p and (candidate - 1).gcd(e) == 1

        p = __generateProbablePrime__(exact_bits=size_p,
                                    randfunc=randfunc,
                                    prime_filter=filter_p)

        min_distance = Integer(1) << max(0, bits // 2 - 100)

        def filter_q(candidate):
            return (candidate > min_q and
                    (candidate - 1).gcd(e) == 1 and
                    abs(candidate - p) > min_distance)

        q = __generateProbablePrime__(exact_bits=size_q,
                                    randfunc=randfunc,
                                    prime_filter=filter_q)

        n = p * q
        lcm = (p - 1).lcm(q - 1)
        d = e.inverse(lcm)

    if p > q:
        p, q = q, p

    u = p.inverse(q)

    return RSA.RsaKey(n=n, e=e, d=d, p=p, q=q, u=u)

def __adaptForAES__(data):
    dataLength = len(data)
    return data.ljust(dataLength + (16 - dataLength) % 16, b'\0')
