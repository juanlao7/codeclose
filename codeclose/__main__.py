import argparse
import inspect
import os
import sys
import json
from datetime import datetime
from Cryptodome import Random

from . import model, errors

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

def addSizeArguments(parser):
    parser.add_argument('--license-id-size', default=model.DEFAULT_LICENSE_ID_SIZE, type=UnsignedInt, help='Specify the size of the license ID field, in bits. {} by default ({:,} possible ids).'.format(model.DEFAULT_LICENSE_ID_SIZE, 2 ** model.DEFAULT_LICENSE_ID_SIZE))
    parser.add_argument('--product-id-size', default=model.DEFAULT_PRODUCT_ID_SIZE, type=UnsignedInt, help='Specify the size of the product ID field, in bits. {} by default ({:,} possible ids).'.format(model.DEFAULT_PRODUCT_ID_SIZE, 2 ** model.DEFAULT_PRODUCT_ID_SIZE))
    parser.add_argument('--expiration-time-size', default=model.DEFAULT_EXPIRATION_TIME_SIZE, type=UnsignedInt, help='Specify the size of the expiration time field, in bits. {} by default (maximum expiration date: 36812-02-19 16:53 UTC).'.format(model.DEFAULT_EXPIRATION_TIME_SIZE))     # Too big for datetime.fromtimestamp.
    parser.add_argument('--hash-size', default=model.DEFAULT_HASH_SIZE, type=UnsignedInt, help='Specify the size of the hash needed for validating the product key, in bytes.')

class Commands(object):
    @classmethod
    def generateSigningKeys(cls):
        def preparer(parser):
            def handler(args):
                privateKey, publicKey = model.generateSigningKeys(args.size, args.public_exponent)
                args.private_key_path.write(privateKey)
                args.public_key_path.write(publicKey)
            
            parser.add_argument('--size', default=model.DEFAULT_RSA_KEY_SIZE, type=UnsignedInt, help='Specify the size of the RSA key, in bits. %s by default.' % model.DEFAULT_RSA_KEY_SIZE)
            parser.add_argument('--public-exponent', default=model.DEFAULT_RSA_PUBLIC_EXPONENT, type=int, help='Specify the RSA public exponent. %s by default.' % model.DEFAULT_RSA_PUBLIC_EXPONENT)
            parser.add_argument('private_key_path', type=argparse.FileType('wb'), help='File path where the RSA private key for creating and signing product keys will be stored.')
            parser.add_argument('public_key_path', type=argparse.FileType('wb'), help='File path where the RSA public key for reading and verifying product keys will be stored.')
            return handler
        
        return 'Generates RSA keys for signing and verifying product keys.', preparer
    
    @classmethod
    def generateEncryptingKey(cls):
        def preparer(parser):
            def handler(args):
                args.encrypting_key_path.write(model.generateEncryptingKey(args.size))
            
            parser.add_argument('--size', default=model.DEFAULT_AES_KEY_SIZE, type=int, choices=[128, 192, 256], help='Specify the size of the AES key, in bits (128, 192 or 256). %s by default.' % model.DEFAULT_AES_KEY_SIZE)
            parser.add_argument('encrypting_key_path', type=argparse.FileType('wb'), help='File path where the AES key for encrypting and decrypting source code will be stored.')
            return handler
        
        return 'Generates an AES key for encrypting and decrypting source code.', preparer

    @classmethod
    def protect(cls):
        def preparer(parser):
            def handler(args):
                model.protect(args.encrypting_key_path.read(), args.dest_directory, args.src, args.encryption_excluded, args.follow_symlinks)
                
            parser.add_argument('--src', '-s', action='append', type=ReadableDirectory, help='Specify a source directory path. All **/*.py files from this directory will be processed.', metavar='SOURCE_DIR')
            parser.add_argument('--encryption-excluded', '-e', action='append', help='Disable encryption for a specific file, to be able to run it without a valid product key.', metavar='FILE_PATH')
            parser.add_argument('--follow-symlinks', action='store_true', help='Follow symbolic links.')
            parser.add_argument('encrypting_key_path', type=argparse.FileType('rb'), help='File containing the AES key for encrypting and decrypting source code.')
            parser.add_argument('dest_directory', type=WritableDirectory, help='Directory path where all processed files will be stored.')
            return handler
        
        return 'Obfuscates and encrypts source code.', preparer
    
    @classmethod
    def createProductKey(cls):
        def preparer(parser):
            def handler(args):
                print(model.createProductKey(args.private_key_path.read(), args.license_id, args.product_id, args.expiration_time, args.groups_length, args.license_id_size, args.product_id_size, args.expiration_time_size, args.hash_size))

            parser.add_argument('--divide', type=UnsignedInt, help='Divide the resulting product key in groups of characters of the given length.', dest='groups_length')
            addSizeArguments(parser)
            parser.add_argument('private_key_path', type=argparse.FileType('rb'), help='File containing the RSA private key for creating and signing product keys.')
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
                    licenseId, productId, expirationTime = model.readProductKey(args.public_key_path.read(), args.product_key, args.license_id_size, args.product_id_size, args.expiration_time_size, args.hash_size)
                    print('License ID:', licenseId)
                    print('Product ID:', productId)
                    print('Expiration time:', expirationTime, '(%s)' % datetime.fromtimestamp(expirationTime).strftime('%Y-%m-%d %H:%M UTC'))
                except errors.InvalidProductKey:
                    print('Invalid product key.')

            addSizeArguments(parser)
            parser.add_argument('public_key_path', type=argparse.FileType('rb'), help='File containing the RSA public key for reading and verifying product keys.')
            parser.add_argument('product_key', type=str, help='The product key to verify and read.')
            return handler
        
        return 'Verifies and reads a product key.', preparer
    
    @classmethod
    def computeLicense(cls):
        def preparer(parser):
            def handler(args):
                expectedProductIds = [] if args.expected_product_id is None else args.expected_product_id
                configuration = model.configureLicenseComputation(args.public_key_path.read(), args.encrypting_key_path.read(), expectedProductIds, args.license_id_size, args.product_id_size, args.expiration_time_size, args.hash_size)
                license = model.computeLicense(configuration, args.product_key)
                print(json.dumps(license))
            
            parser.add_argument('--expected-product-id', '-e', action='append', type=UnsignedInt, help='Specify an expected product id.')
            addSizeArguments(parser)
            parser.add_argument('public_key_path', type=argparse.FileType('rb'), help='File containing the RSA public key for reading and verifying product keys.')
            parser.add_argument('encrypting_key_path', type=argparse.FileType('rb'), help='File containing the AES key for encrypting and decrypting source code.')
            parser.add_argument('product_key', type=str, help='The product key to verify and read.')
            return handler
        
        return 'Computes the license expected by the product.', preparer
    
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
