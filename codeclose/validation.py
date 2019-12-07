import os

from .protection import getLicense
from .errors import InvalidProductId, ExpiredLicense

def validate(expectedProductIds, exitOnException=True):
    try:
        license = getLicense()

        if license['productId'] not in expectedProductIds:
            raise InvalidProductId

        if license['currentTime'] > license['expirationTime']:
            raise ExpiredLicense
    except BaseException as e:
        if exitOnException:
            os._exit(1)     # Without triggering SystemExit exception.
        else:
            raise e
