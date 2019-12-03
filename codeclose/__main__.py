import argparse
import inspect
import os
import sys
from shutil import copyfile, rmtree
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from base64 import b64encode

PROTECTED_SOURCE_TEMPLATE = """from codeclose import expose
exec(expose({encryptedContent}, {initializationVector}, {originalLength}))"""

def ReadableDirectory(value):
    if not os.path.isdir(value):
        raise argparse.ArgumentTypeError('"%s" is not a directory.' % value)
    
    if not os.access(value, os.R_OK):
        raise argparse.ArgumentTypeError('"%s" directory is not readable.' % value)
    
    return value

def WritableDirectory(value):
    if not os.path.exists(value):
        os.makedirs(value, exist_ok=True)
    
    if not os.path.isdir(value):
        raise argparse.ArgumentTypeError('"%s" is not a directory.' % value)
    
    if not os.access(value, os.W_OK):
        raise argparse.ArgumentTypeError('"%s" directory is not writable.' % value)
    
    return value

def toHyphenSeparated(value):
    result = value[0].lower()

    for i in range(1, len(value)):
        if value[i].isupper():
            result += '-%s' % value[i].lower()
        else:
            result += value[i]

    return result

class Commands(object):
    @classmethod
    def generateSigningKeys(cls):
        def preparer(parser):
            def handler(args):
                key = rsa.generate_private_key(backend=default_backend(), public_exponent=args.public_exponent, key_size=args.key_size)

                privateKey = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
                args.private_key_path.write(privateKey)

                publicKey = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
                args.public_key_path.write(publicKey)
            
            parser.add_argument('--key-size', default=2048, type=int, help='RSA key size, in bits. 2048 by default.')
            parser.add_argument('--public-exponent', default=65537, type=int, help='RSA public exponent. 65537 by default.')
            parser.add_argument('private_key_path', type=argparse.FileType('wb'), help='File path where the RSA private key for signing product keys will be stored.')
            parser.add_argument('public_key_path', type=argparse.FileType('wb'), help='File path where the RSA public key for verifying product keys will be stored.')
            return handler
        
        return 'Generates RSA keys for signing/verifying product keys.', preparer
    
    @classmethod
    def generateEncryptingKey(cls):
        def preparer(parser):
            def handler(args):
                args.key_path.write(os.urandom(int(args.size / 8)))
            
            parser.add_argument('--size', default=256, choices=[128, 192, 256], help='AES key size, in bits (128, 192 or 256). 256 by default.')
            parser.add_argument('key_path', type=argparse.FileType('wb'), help='File path where the AES key for encrypting source code will be stored.')
            return handler
        
        return 'Generates an AES key for encrypting/decrypting source code.', preparer

    @classmethod
    def protect(cls):
        def preparer(parser):
            def handler(args):
                backend = default_backend()
                aes = algorithms.AES(args.key_path.read())
                rmtree(args.dest_directory)

                while os.path.exists(args.dest_directory):
                    pass
                
                os.makedirs(args.dest_directory, exist_ok=True)
                currentPath = os.getcwd()

                def adaptForAES(data):
                    dataLength = len(data)
                    return data.ljust(dataLength + (16 - dataLength) % 16, b'\0')

                for srcPath in args.src_directories:
                    destPath = os.path.abspath(os.path.join(args.dest_directory, os.path.basename(os.path.abspath(srcPath))))
                    os.chdir(srcPath)

                    for root, _, fileNames in os.walk('.', followlinks=args.follow_symlinks):
                        for fileName in fileNames:
                            if fileName.endswith('.py'):
                                srcFilePath = os.path.join(root, fileName)
                                destFilePath = os.path.join(destPath, srcFilePath)
                                os.makedirs(os.path.dirname(destFilePath), exist_ok=True)
                                copyfile(srcFilePath, destFilePath)     # TODO: minify

                                with open(destFilePath, 'rb') as readHandler:
                                    content = readHandler.read()

                                    if content:
                                        readHandler.close()

                                        initializationVector = os.urandom(16)
                                        encryptor = Cipher(aes, modes.CBC(initializationVector), backend=backend).encryptor()
                                        encryptedContent = encryptor.update(adaptForAES(content)) + encryptor.finalize()

                                        protectedSource = PROTECTED_SOURCE_TEMPLATE.format(
                                            encryptedContent="'%s'" % b64encode(encryptedContent).decode('utf8'),
                                            initializationVector="'%s'" % b64encode(initializationVector).decode('utf8'),
                                            originalLength=len(content)
                                        )

                                        with open(destFilePath, 'w') as writeHandler:
                                            writeHandler.write(protectedSource)
                        
                    os.chdir(currentPath)
                
            parser.add_argument('--follow-symlinks', action='store_true', help='Follow symbolic links.')
            parser.add_argument('key_path', type=argparse.FileType('rb'), help='File containing the AES key for encrypting source code.')
            parser.add_argument('dest_directory', type=WritableDirectory, help='Directory path where all processed files will be stored.')
            parser.add_argument('src_directories', nargs='+', type=ReadableDirectory, help='Source directory paths. All **/*.py files from these directories will be processed.')
            return handler
        
        return 'Obfuscate and encrypt source code.', preparer
    
def main():
    parser = argparse.ArgumentParser(prog='codeclose')
    subparsers = parser.add_subparsers(title='Commands', description='Available commands.')

    for commandName in vars(Commands):
        commandMethod = getattr(Commands, commandName)
        
        if inspect.ismethod(commandMethod) and commandMethod.__self__ is Commands:
            description, preparer = commandMethod()
            subparser = subparsers.add_parser(toHyphenSeparated(commandName), help=description)
            subparser.set_defaults(handler=preparer(subparser))
    
    args = parser.parse_args()

    if hasattr(args, 'handler'):
        args.handler(args)
    else:
        parser.print_help(sys.stderr)
