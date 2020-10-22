# Codeclose

A license system and code obfuscator for Python.

Codeclose obfuscates source code to make it unreadable for humans and encrypts it to make it unreadable for machines. The resulting code can only be run if the user has a valid product key, provided by the developer.

## Example

In the following example we will *protect* a package that contains 3 files:

`__init__.py`, that is empty.

`__main__.py`, the entry point of the application:

```python
import argparse
from codeclose.runtime import configure, validate

parser = argparse.ArgumentParser()
parser.add_argument('productKey', help='Licensed product key.')
parser.add_argument('n', type=int, help='Number of elements of the Fibonacci sequence to compute.')
args = parser.parse_args()

configure(productKey=args.productKey, expectedProductIds=[1])
validate()

from . import model

for x in model.computeFibonacci(args.n):
    print(x)
```

`model.py`, the logic of the application:

```python
def computeFibonacci(n):
    a, b = 0, 1

    for _ in range(n):
        yield a
        a, b = b, a + b
```

In this example we need to obfuscate all files, but encrypt only `model.py`. File `__main__.py` must not be encrypted because it is the entry point that lets the user introduce a valid product key and must work even without a license.

This is the result after *protecting* the code:

`__init__.py` is left empty.

`__main__.py`:

```python
import argparse as FileNotFoundError_else
from ._max_divmod.runtime import NotImplementedError_getattr, id_int
global_InterruptedError = FileNotFoundError_else.ArgumentParser()
global_InterruptedError.add_argument((218070150015777706032726 + int(312945851559531341162275)).to_bytes(10, 'big').decode(), help=(13723243591861468797903987067343596087317109150007 + int(97952541485923637808708734225633910168209401669623)).to_bytes(21, 'big').decode())
global_InterruptedError.add_argument((60 + int(50)).to_bytes(1, 'big').decode(), type=int, help=(190820020530003600583445893195072181448475704265817386830394382290471668589086669633192431933410851105665532646255295303048759871964281 + int(31941001550368966262141651389957912397226707173036854376354526051957583420790840867291092208255019228961020537222244325363175807377589)).to_bytes(56, 'big').decode())
args = global_InterruptedError.parse_args()
exec_spec = open((461287876652164125207069875439750708728036679687470132119386593236936514360017432701816493620505866370663186813340994031482081058446033194095901042752031995 + int(440091872998125311072464636259588918938113672181667337892966700676731329571805300135346517686927493702592300165113155338469845786072764955800589476566161534)).to_bytes(65, 'big').decode(), (19166 + int(10116)).to_bytes(2, 'big').decode())
NameError_IOError = exec_spec.read()
exec_spec.close()
exec_spec = open((884210677664253629917141785328785264993245054821870424906275615485961356724104403220422748571450134837184642123525527473077402111029002875726232439448225934301057989 + int(2987185868360406935837734856523207820629687512674967480524962497871117880369906287984537678414854348376839838702732549545321628314202476716756687295418502390211580328)).to_bytes(69, 'big').decode(), (17390 + int(11892)).to_bytes(2, 'big').decode())
UnicodeTranslateError_all = exec_spec.read()
exec_spec.close()
NotImplementedError_getattr(verifyingPublicKey=UnicodeTranslateError_all, encryptingKey=NameError_IOError, expectedProductIds=[1], productKey=args.productKey)
id_int()
from . import model
for for_while in model.name_EnvironmentError(args.n):
 print(for_while)
```

`model.py`:

```python
from ._max_divmod.runtime import IndentationError_SyntaxError
exec(IndentationError_SyntaxError('mHE+isDVh1vos4pTP2Og/wJuh2Q5SNKXSijM4vvyTDvkZPAiF9uv+4+EP6CwlClBsvTLVtdTenTZt2GawvD+wUoqBCk3FCbX4qRelU+cdt5e3K0ukQtlDu2L9DSiYTQ3D0tKuzndXM0zgZA+oR60byhBwQHUivtTSl6Ra7KqmUfLLVspFG/Jx4Tjs1O1OV2YvexOcLEh89qAMOw37dXPngHwASF551DnHe98aK+RD1dq+MZXdCQ4gW7HzQOJBYZsUbA1IUu0GtiO5Uv6Rla7dMqP2xIRRd9T5zvknxdkl6Mt+AEybyOa0LD3aN0jPV9UXY3Vu9ihNRc4zV0KIAYHWjmbVNbHSEhLiPbDG6zJ0L2XYKSKhzOCX3n9Ocksylg/tLgkBQQ3AOQW/68nnun2LQ==', '6VJL8N03wqNwQTejK+oskg==', 297))
```

Anyone can run `__main__.py`, but only licensed users can run `model.py`.

A licensed user has access to the decrypting key, so in theory he could do reverse engineering to obtain the source code of `model.py`. However, he will be only able to see its obfuscated version:

```python
from ._spec_ProcessLookupError.runtime import name_not
def eval_pow(MemoryError_license):
 name_not()
 (ValueError_issubclass, continue_compile) = (0, 1)
 for _all_quit_ in range(MemoryError_license):
  (yield ValueError_issubclass)
  (ValueError_issubclass, continue_compile) = (continue_compile, (ValueError_issubclass + continue_compile))
```

## How does it work

### Protecting the code

Codeclose obfuscates and then encrypts Python source code. The encryption is performed with AES-256, an algorithm considered secure enough to protect national TOP SECRET information ([source](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard#Security)).

The protected result contains all the required Codeclose runtime resources for validating licenses and decrypting code, also obfuscated, so the final application does not need to mark Codeclose as a dependency.

### Creating product keys

A product key is a **signed** array of bits that represent a license and all its associated information. The array contains the following elements:

* **License ID**: an unsigned integer that identifies the license and, by extension, the customer.
* **Product ID**: an unsigned integer that identifies the licensed product.
* **Expiration date**: an unsigned integer that represents the expiration time of the product key as a Unix timestamp (seconds since Jan 01 1970 UTC).

The array of bits is signed with RSA and encoded in Base32, forming a product key (e.g. BSKQBE-ELZQ7S-B36QXU-HDDVAG). Signing the array guarantees that no one apart from you can create valid product keys. Note that the length of the generated product keys depends on the size of the RSA key you use for signing. Big RSA keys are safer, but short RSA keys generate shorter product keys, useful if users need to manually introduce them.

Codeclose offers a command line tool and a Python API for creating product keys.

### Validating product keys

License validation can be performed online or offline.

#### Online validation

In online mode users only need a product key to validate their license and use your product.

In this scenario the injected runtime components of Codeclose call an online server (of your choice) and sends the  product key provided by the user. Then the server verifies the RSA signature, reads the license data and returns it in JSON format, including the AES decrypting key if the license is valid and has not expired. Finally, the runtime components decrypt all the protected code.

#### Offline validation

In offline mode users need a product key, the public RSA key and the AES decrypting key to validate their license and use your product.

In this scenario the injected runtime components of Codeclose verify the RSA signature of the product key and read the license data. If the product key is valid and has not expired, the runtime components decrypt all the protected code.
