import os
import textwrap
import inspect
import importlib
from shutil import rmtree
from base64 import b64encode, b32encode, b32decode
from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import AES
from Cryptodome.Hash import SHAKE256
from Cryptodome.Random import get_random_bytes
from Cryptodome.Util.number import bytes_to_long, long_to_bytes

from .crypto import generateRSAKey, adaptForAES
from .errors import InvalidProductKey

__AES_POSSIBLE_SIZES__ = [128, 192, 256]

__PROTECTED_SOURCE_TEMPLATE__ = """from codeclose.protection import expose
exec(expose({encryptedContent}, {initializationVector}, {originalLength}))"""

# module -> encrypt
__INJECTED_CODECLOSE_MODULES__ = {
    'protection': False,
    'errors': False,
    'validation': True
}

def generateSigningKeys(size=120, publicExponent=65537):
    key = generateRSAKey(size, e=publicExponent)
    return key.export_key('PEM'), key.publickey().export_key('PEM')

def generateEncryptingKey(size=256):
    if size not in __AES_POSSIBLE_SIZES__:
        raise ValueError('Only possible key sizes are %s.' % ', '.join(__AES_POSSIBLE_SIZES__))

    return get_random_bytes(size // 8)

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

def createProductKey(signingPrivateKey, licenseId, productId, expirationTime, groupsLength=None, licenseIdSize=24, productIdSize=8, expirationTimeSize=40, hashSize=6):
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

def readProductKey(verifyingPublicKey, productKey, licenseIdSize=24, productIdSize=8, expirationTimeSize=40, hashSize=6):
    productKey = productKey.strip().replace('-', '').replace(' ', '')
    productKeyBytes = b32decode((productKey + '=' * (-len(productKey) % 8)).encode('utf-8'))
    productKeyLong = bytes_to_long(productKeyBytes)
    publicKey = RSA.import_key(verifyingPublicKey)
    longValue = publicKey._encrypt(productKeyLong)
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

def __getInjectionContent__(encryptingKey, codecloseModuleName):
    injectionContent = {os.path.join('__codeclose__', '__init__.py'): ' '}

    for injectedModuleName in __INJECTED_CODECLOSE_MODULES__:
        injectedFilePath = os.path.join('__codeclose__', '%s.py' % injectedModuleName)
        injectedModule = importlib.import_module('codeclose.%s' % injectedModuleName)
        injectionContent[injectedFilePath] = inspect.getsource(injectedModule)

        if __INJECTED_CODECLOSE_MODULES__[injectedModuleName]:
            injectionContent[injectedFilePath] = __encrypt__(injectionContent[injectedFilePath], encryptingKey, codecloseModuleName)
    
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
    
    initializationVector = get_random_bytes(16)
    cipher = AES.new(encryptingKey, AES.MODE_CBC, iv=initializationVector)
    encryptedContent = cipher.encrypt(adaptForAES(content.encode('utf-8')))

    content = __PROTECTED_SOURCE_TEMPLATE__.format(
        encryptedContent="'%s'" % b64encode(encryptedContent).decode('utf-8'),
        initializationVector="'%s'" % b64encode(initializationVector).decode('utf-8'),
        originalLength=len(content)
    )

    return __remapModules__(content, codecloseModuleName)
