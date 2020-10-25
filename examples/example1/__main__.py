import argparse

# The following package is now required for loading the AES and RSA keys from disk.
import os

# The following packages are now required to display the license information.
import sys
import time

# The following package is required to integrate Codeclose within the product.
# DO NOT MARK CODECLOSE AS A DEPENDENCY OF YOUR PROJECT.
# This import is global, but Codeclose will later replace it by a local import, from obfuscated embedded files.
from codeclose.runtime import configure, validate, InvalidProductKey, InvalidProductId, ExpiredLicense

parser = argparse.ArgumentParser()
parser.add_argument('productKey', help='Licensed product key.')
parser.add_argument('n', type=int, help='Number of elements of the Fibonacci sequence to compute.')
args = parser.parse_args()

# Loading keys from disk.
basePath = os.path.dirname(__file__)

handler = open(os.path.join(basePath, 'code_encrypting.key'), 'rb')
encryptingKey = handler.read()
handler.close()

handler = open(os.path.join(basePath, 'pk_verifying-public.pem'), 'rb')
verifyingPublicKey = handler.read()
handler.close()

# Configuring Codeclose.
# We will only accept product keys that grant access to the product with ID = 1.
configure(verifyingPublicKey=verifyingPublicKey, encryptingKey=encryptingKey, expectedProductIds=[1], productKey=args.productKey)

# Validating the license.
# If there is any problem, Codeclose will raise an exception. You can then catch it and inform the user.
try:
    license = validate(False)
    print('Product key is valid until %s' % time.strftime('%Y-%m-%d', time.localtime(license['expirationTime'])))
except InvalidProductKey:
    sys.exit('Invalid product key.')
except InvalidProductId:
    sys.exit('Invalid product ID.')
except ExpiredLicense as e:
    sys.exit('Product key expired on %s' % time.strftime('%Y-%m-%d', time.localtime(e.expirationTime)))

# Importing the model.
# Please note that we import the encrypted model AFTER validating the license, otherwise it would not work.
from . import model

# Finally, we call the model:

for x in model.computeFibonacci(args.n):
    print(x)
