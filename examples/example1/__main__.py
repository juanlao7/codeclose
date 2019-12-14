import argparse
from codeclose.runtime import configure, validate

parser = argparse.ArgumentParser()
parser.add_argument('productKey', help='Licensed product key.')
parser.add_argument('n', type=int, help='Number of elements of the Fibonacci sequence to compute.')
args = parser.parse_args()

handler = open('C:\\projects\\protopipe\\codeclose\\examples\\keys\\code_encrypting.key', 'rb')
encryptingKey = handler.read()
handler.close()

handler = open('C:\\projects\\protopipe\\codeclose\\examples\\keys\\pk_verifying-public.pem', 'rb')
verifyingPublicKey = handler.read()
handler.close()

configure(verifyingPublicKey=verifyingPublicKey, encryptingKey=encryptingKey, expectedProductIds=[1], productKey=args.productKey)

#configure(productKey=args.productKey, expectedProductIds=[1])
validate()

from . import model

for x in model.computeFibonacci(args.n):
    print(x)
