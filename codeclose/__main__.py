import argparse
import inspect
import os
import sys
from Cryptodome import Random

from . import generateSigningKeys, generateEncryptingKey, protect, createProductKey, readProductKey, InvalidProductKey

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

def UnsignedInt(value):
    value = int(value)

    if value <= 0:
        raise argparse.ArgumentTypeError('Invalid unsigned integer "%s".' % value)
    
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
                privateKey, publicKey = generateSigningKeys(args.size, args.public_exponent)
                args.private_key_path.write(privateKey)
                args.public_key_path.write(publicKey)
            
            parser.add_argument('--size', default=120, type=UnsignedInt, help='RSA key size, in bits. 120 by default.')
            parser.add_argument('--public-exponent', default=65537, type=int, help='RSA public exponent. 65537 by default.')
            parser.add_argument('private_key_path', type=argparse.FileType('wb'), help='File path where the RSA private key for creating and signing product keys will be stored.')
            parser.add_argument('public_key_path', type=argparse.FileType('wb'), help='File path where the RSA public key for reading and verifying product keys will be stored.')
            return handler
        
        return 'Generates RSA keys for signing/verifying product keys.', preparer
    
    @classmethod
    def generateEncryptingKey(cls):
        def preparer(parser):
            def handler(args):
                args.key_path.write(generateEncryptingKey(args.size))
            
            parser.add_argument('--size', default=256, type=int, choices=[128, 192, 256], help='AES key size, in bits (128, 192 or 256). 256 by default.')
            parser.add_argument('key_path', type=argparse.FileType('wb'), help='File path where the AES key for encrypting source code will be stored.')
            return handler
        
        return 'Generates an AES key for encrypting/decrypting source code.', preparer

    @classmethod
    def protect(cls):
        def preparer(parser):
            def handler(args):
                protect(args.key_path.read(), args.dest_directory, args.src_directories, args.follow_symlinks)
                
            parser.add_argument('--follow-symlinks', action='store_true', help='Follow symbolic links.')
            parser.add_argument('key_path', type=argparse.FileType('rb'), help='File containing the AES key for encrypting source code.')
            parser.add_argument('dest_directory', type=WritableDirectory, help='Directory path where all processed files will be stored.')
            parser.add_argument('src_directories', nargs='+', type=ReadableDirectory, help='Source directory paths. All **/*.py files from these directories will be processed.')
            return handler
        
        return 'Obfuscates and encrypts source code.', preparer
    
    @classmethod
    def createProductKey(cls):
        def preparer(parser):
            def handler(args):
                print(createProductKey(args.key_path.read(), args.license_id, args.product_id, args.expiration_time, args.groups_length, args.license_id_size, args.product_id_size, args.expiration_time_size, args.hash_size))

            parser.add_argument('--divide', type=UnsignedInt, help='Divide the resulting product key in groups of characters of the given length.', dest='groups_length')
            parser.add_argument('--license-id-size', default=24, type=UnsignedInt, help='Size, in bits, of the license ID field. 24 by default (16,777,216 possible ids).')
            parser.add_argument('--product-id-size', default=8, type=UnsignedInt, help='Size, in bits, of the product ID field. 8 by default (256 possible ids).')
            parser.add_argument('--expiration-time-size', default=40, type=UnsignedInt, help='Size, in bits, of the expiration time field. 40 by default (maximum expiration date: 36812-02-19 16:53 UTC).')
            parser.add_argument('--hash-size', default=6, type=UnsignedInt, help='Size, in bytes, of the hash needed for validating the product key.')
            parser.add_argument('key_path', type=argparse.FileType('rb'), help='File containing the RSA private key for creating and signing product keys.')
            parser.add_argument('license_id', type=UnsignedInt, help='An unsigned integer representing the license ID.')
            parser.add_argument('product_id', type=UnsignedInt, help='An unsigned integer representing the product ID.')
            parser.add_argument('expiration_time', type=UnsignedInt, help='An unsigned integer representing the expiration time of the product key as a Unix timestamp (seconds since Jan 01 1970 UTC).')
            return handler
        
        return 'Creates a licensed product key.', preparer
    
    @classmethod
    def readProductKey(cls):
        def preparer(parser):
            def handler(args):
                try:
                    licenseId, productId, expirationTime = readProductKey(args.key_path.read(), args.product_key, args.license_id_size, args.product_id_size, args.expiration_time_size, args.hash_size)
                    print('License ID:', licenseId)
                    print('Product ID:', productId)
                    print('Expiration time:', expirationTime)
                except InvalidProductKey:
                    print('Invalid product key.')

            parser.add_argument('--license-id-size', default=24, type=UnsignedInt, help='Size, in bits, of the license ID field. 24 by default (16,777,216 possible ids).')
            parser.add_argument('--product-id-size', default=8, type=UnsignedInt, help='Size, in bits, of the product ID field. 8 by default (256 possible ids).')
            parser.add_argument('--expiration-time-size', default=40, type=UnsignedInt, help='Size, in bits, of the expiration time field. 40 by default (maximum expiration date: 36812-02-19 16:53 UTC).')
            parser.add_argument('--hash-size', default=6, type=UnsignedInt, help='Size, in bytes, of the hash needed for validating the product key. 6 by default.')
            parser.add_argument('key_path', type=argparse.FileType('rb'), help='File containing the RSA public key for reading and verifying product keys.')
            parser.add_argument('product_key', type=str, help='The product key to read.')
            return handler
        
        return '', preparer
    
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
