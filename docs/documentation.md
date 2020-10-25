<ul class="breadcrumb">
    <li><a href="">Home</a></li>
    <li>Documentation index</li>
</ul>

## Documentation

Warning: Codeclose is still in **beta**, and has only been used in [Protopipe](https://juanlao7.github.io/protopipe_web/). Use it on your own risk.

### What is Codeclose?

Codeclose is a tool for obfuscating and encrypting Python source code. The obfuscation makes the code hard to understand, while the encryption makes it impossible to run unless users provide a valid product key.

Please note that this system is not 100% bullet-proof. With enough time and dedication the obfuscated code can be understood, and the encrypted code can always be revealed with some reverse engineering, especially if the attacker has a valid product key.

It is impossible to distribute software aimed to be interpreted by a machine and prevent anyone and anything from reading it at the same time. Codeclose is an obstacle to deter some attempts, but not all of them.

### How does it work?

#### Code protection

Codeclose obfuscates **all** your code by replacing all identifiers (i.e., variables, functions, classes, etc.) with random names and converting all strings into numeric operations that are computed in runtime. In order to respect API's and keep reflection working, it is possible to specify a list of identifiers and attributes that must be kept intact.

After the obfuscation, Codeclose encrypts the result with AES-256. It also adds the required middleware for decrypting the code in runtime, completely and seamlessly integrated in your final product. It is not required (and actually, it is not recommended) to mark Codeclose as a dependence of your project.

Some parts of your code, like the main entry point, must be left unencrypted in order to set Codeclose's parameters and somehow retrieve the user's product key---from UI, a configuration file, command line arguments, or any other method---. It is possible to disable encryption for any specific file or even the entire project (for debugging purposes).

#### Product keys

Users will need a valid and not expired product key to use your product, and you will be the only entity that can create them.

Product keys are generated from streams of bits that contain the following fields:

* the ID of the license,
* the ID of the product (useful if you offer a multiple billing plans in the same package), and
* the expiration date of the key.

The stream of bits is then RSA-signed and encoded in base32. The result looks similar to this: <span class="nowrap">`BSKQBE-ELZQ7S-B36QXU-HDDVAG`</span>. This is the final product key, and it is ready to be delivered to your customer. 

As owner of your product, **you can create and sign an infinite number of product keys** for an infinite number of customers. You decide how many bits you want to use for specifying each field, including their ID.

You can also choose your RSA key size; the only restriction is that it must be bigger than the your stream of data. Huge RSA keys prevent attackers from supplanting you to create fake product keys, but the size of the resulting product keys is also huge. Small RSA keys are way less secure, but generate shorter product keys, which is desirable in some scenarios (e.g., printed keys that users must manually type). In the example above, the key was signed with RSA-120.

#### License validation

Codeclose will automatically and seamlessly add within your product all the required middleware for reading and verifying product keys. This validation is performed completely offline; users do not need an internet connection to get access to your product.

When users provide a product key, Codeclose will use your public RSA key to verify that it was signed by you. Then it will automatically decrypt and run the protected code, granting full access.

Please note that the AES key used for decrypting the code must be embedded within your product. This is a weak spot of the system, as explained in the [Limitations](#limitations) section.

### Downloading and installing Codeclose

Read [these instructions](download) to know how to download and install Codeclose.

### Example case

#### The plan

In this example we will use Codeclose to *protect* a package that contains 3 files:

* `example1/__init__.py`, that is empty.

* `example1/__main__.py`, the entry point of the application:

```python
import argparse
from . import model

parser = argparse.ArgumentParser()
parser.add_argument('n', type=int, help='Number of elements of the Fibonacci sequence to compute.')
args = parser.parse_args()

for x in model.computeFibonacci(args.n):
    print(x)
```

* `example1/model.py`, the logic of the application:

```python
def computeFibonacci(n):
    a, b = 0, 1

    for _ in range(n):
        yield a
        a, b = b, a + b
```

This application computes and prints the first N Fibonacci numbers.

```bash
$ python -m example1 10
0
1
1
2
3
5
8
13
21
34
```

In this example we will obfuscate all files, but encrypt only `model.py`.

File `__main__.py` must not be encrypted because it is the entry point of the application, and it will let the user provide a valid product key through command line arguments. This file must always work, even when the user does not have a valid product key.

#### Generating encryption, verification and signature keys

First of all we need to create an AES key for encrypting/decrypting the code and a public/private pair of RSA keys for verifying and signing product keys.

To create the AES key in `keys/code_encrypting.key`, run the following command:

```bash
$ codeclose generate-encrypting-key keys/code_encrypting.key
```

And to create the pair of RSA keys `keys/pk_signing-private.pem` and `keys/pk_verifying-public.pem`, run the following command:

```bash
$ codeclose generate-signing-keys keys/pk_signing-private.pem keys/pk_verifying-public.pem
```

The default size for the RSA key is 120 bits. Use argument `--size SIZE` in case you prefer to set a different one.

#### Integrating Codeclose within the application

Now we must adapt `__main__.py` to execute the following actions:

1. Retrieve the user's product key from command line arguments.
2. Configure Codeclose parameters.
3. Validate the user's product key.
4. Inform the user about his product key information (status, expiration date, etc.)

We will assume that the AES decryption key and the public RSA key will be copied from `keys/` to the final package's root. You can choose any other method to embed the keys within your product, like for example, writing the file byte literals inside the code, storing it in a variable.

The final version of `__main__.py` should look like this:

```python
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
```

#### Protecting the code

To obfuscate all the source code and encrypt `model.py`, just run the following command:

```bash
$ codeclose protect --src example1 --encryption-excluded example1/__main__.py --encryption-excluded example1/__init__.py keys/code_encrypting.key protected --keep-attributes args --keep-identifier args
```

Explanation:

* `protect`: we tell Codeclose command tool that we want to protect source code.
* `--src example1`: we specify the directory of the source code.
* `--encryption-excluded example1/__main__.py`: we exclude the entry point of the application from being encrypted, because we want it gets executed even if the user does not have a valid product key.
* `--encryption-excluded example1/__init__.py`: we exclude `__init__.py` from being encrypted because it is empty. This argument is optional.
* `keys/code_encrypting.key protected`: we specify the AES encryption key, for encrypting the code.
* `protected`: we specify that we want to store the resulting code in the directory "protected/". Codeclose will create this directory if it does not exist.
* `--keep-attributes args`: we specify that we do not want to obfuscate the attributes of the `args` identifier (because they are dynamically added by *argparse*).
* `--keep-identifier args`: we specify that we do not want to obfuscate the identifier `args`, because in order to keep its attributes intact, we must keep the identifier also intact.

After executing this command a new directory `protected/` will contain the obfuscated \& encrypted package.

* `protected/example1/__init__.py` stayed empty.

* `protected/example1/__main__.py`, the entry point of the application, has been obfuscated but not encrypted (i.e., it is hard to understand but it is possible to run it without a product key):

```python
import argparse as import_return
import os as TypeError_async
import sys as BaseException_max
import time as reversed_FileExistsError
from ._async_AssertionError.runtime import issubclass_ModuleNotFoundError, Warning_copyright, InterruptedError_return, super_ImportWarning, NotImplementedError_iter
OSError_int = import_return.ArgumentParser()
OSError_int.add_argument((452612707537990878461005 + int(78403294037318168733996)).to_bytes(10, 'big').decode(), help=(96290527526120269828457311984065871156495553835872 + int(15385257551664836778155409308911635099030956983758)).to_bytes(21, 'big').decode())
OSError_int.add_argument((24 + int(86)).to_bytes(1, 'big').decode(), type=int, help=(138889753588288338296340531952664530574485303810215174640923040002662531359291441353961346079511033677797005951050166997185390989290006 + int(83871268492084228549247012632365563271217107628639066565825868339766720650586069146522178062154836656829547232427372631226544690051864)).to_bytes(56, 'big').decode())
args = OSError_int.parse_args()
tuple_UnicodeEncodeError = TypeError_async.path.dirname(__file__)
ChildProcessError_SyntaxError = open(TypeError_async.path.join(tuple_UnicodeEncodeError, (509867381153097848235226077680191299870968377 + int(1707610020223904369083495793919735175948311360)).to_bytes(19, 'big').decode()), (19482 + int(9800)).to_bytes(2, 'big').decode())
encryptingKey = ChildProcessError_SyntaxError.read()
ChildProcessError_SyntaxError.close()
ChildProcessError_SyntaxError = open(TypeError_async.path.join(tuple_UnicodeEncodeError, (10201455759240830106755788935952104509792597403451636184 + int(566185998248959318986370992541678069076774772897655701)).to_bytes(23, 'big').decode()), (16672 + int(12610)).to_bytes(2, 'big').decode())
verifyingPublicKey = ChildProcessError_SyntaxError.read()
ChildProcessError_SyntaxError.close()
issubclass_ModuleNotFoundError(verifyingPublicKey=verifyingPublicKey, encryptingKey=encryptingKey, expectedProductIds=[1], productKey=args.productKey)
try:
 in_copyright = Warning_copyright(False)
 print(((485679788288496504979050320136390301014574036798772200962065468875175 + int(1683167370515899785943796789077455241262587267840492268722697876685772)).to_bytes(29, 'big').decode() % reversed_FileExistsError.strftime((404736349011679625 + int(2286495542087617499)).to_bytes(8, 'big').decode(), reversed_FileExistsError.localtime(in_copyright[(532611273280869493830692544261517 + int(1525454265988119491263555617701848)).to_bytes(14, 'big').decode()]))))
except InterruptedError_return as BlockingIOError_package:
 BaseException_max.exit((404054365744178361430647394466865783420410207125 + int(15165354899033676950055596667203851780425538969)).to_bytes(20, 'big').decode())
except super_ImportWarning as UnicodeEncodeError_vars:
 BaseException_max.exit((384589670252398889394215056437361442319710554 + int(1252987363510148135530406002680098070181317332)).to_bytes(19, 'big').decode())
except NotImplementedError_iter as FileNotFoundError_as:
 BaseException_max.exit(((469920102127731157036433715711268724396356402832662808747752 + int(35053977843562829487753105294152843794061440876779617928843)).to_bytes(25, 'big').decode() % reversed_FileExistsError.strftime((2063425090420274709 + int(627806800679022415)).to_bytes(8, 'big').decode(), reversed_FileExistsError.localtime(FileNotFoundError_as.id_next))))
from . import model
for RecursionError_debug in model.with_ord(args.n):
 print(RecursionError_debug)
```

* `protected/example1/model.py`, the logic of the application, has been obfuscated \& encrypted (i.e., it is not possible to run it without a valid product key):

```python
from ._async_AssertionError.runtime import MemoryError_EOFError
exec(MemoryError_EOFError('ld/rb5vncYYdqImosnYFoAMkPXZv6ZgiWiRiBnD73BFuzhfR/sKhty4/47T3BcRJ61TkuWUR1OwyfxPoEC2vp1ebPyaMZKRPNfiDn7F0VP6bfdxlRccuL8elp/5hpnXqN0kGJGRD47A27u71BbDV6GbBv+Aj08g29YEHF3HupNKkM2zXx4x2DJk+UNYArr7ss8N/I58HsKdHCOOtUuJXLvzOpR6b09gaU0bj7KJOuzVobGaDsPYgEf3R1bWZhJdONRo9YLj6B5GqBy/OD027eS0rInyQJVexgZQFgu3eNhIi5kvRlmO3XZLH2LJfDIxe00WiWrw8KWWkQpDW5bqF8FkrPh8nnKbF11uKlNiughjEYN+lT8BfT53GlRqDQonWyATx6lsVZJFy+N6b4YguQFYwmTByO2KxL7ZVRj03B84=', '9+VUh01utWnkjebroRG+Ug==', 319))
```

Do not forget to copy the AES encryption key and the RSA public key into your final package:

```bash
$ cp keys/code_encrypting.key protected/example1
$ cp keys/pk_verifying-public.pem protected/example1
```

If we try to run the application with an invalid product key, it will fail:

```bash
$ cd protected
$ python -m example1 THISIS-ANINVA-IDPROD-UCTKEY 10
Invalid product key.
```

#### Creating a product key

To create a product key, just run this command:

```bash
$ codeclose create-product-key keys/pk_signing-private.pem 7 1 2544307200 --divide 6
JCYBGU-K4ZPE3-WC2ODA-774CLC
```

Explanation:

* `create-product-key`: we tell Codeclose that we want to create a product key.
* `keys/pk_signing-private.pem`: the path of the private RSA key.
* `7`: the license ID ("7" is just an example). Each of your customers will have one or more licenses.
* `1`: the product ID ("1" is just an example). If your application has multiple billing plans, you can use this ID to grant access to its different features.
* `2544307200`: the expiration date of the product key, as Unix timestamp (seconds since Jan 01 1970 UTC). In this example, it corresponds to Aug 17 2050.
* `--divide 6`: we specify that we want to split the product key with dashes in groups of 6 characters.

Now we can run the protected application:

```bash
$ cd protected
$ python -m example1 JCYBGU-K4ZPE3-WC2ODA-774CLC 10
Product key is valid until 2050-08-17
0
1
1
2
3
5
8
13
21
34
```

If we generate a product key with product ID different than 1, the application will not work.

```bash
$ codeclose create-product-key keys/pk_signing-private.pem 7 2 2544307200 --divide 6
K6DLR5-COCN66-EMQATF-FFKMOL
```

```bash
$ cd protected
$ python -m example1 K6DLR5-COCN66-EMQATF-FFKMOL 10
Invalid product ID.
```

And if we generate an expired product key, the application will not work either:

```bash
$ codeclose create-product-key keys/pk_signing-private.pem 7 1 1566000000 --divide 6
S7EW55-AWQPPE-SQETCC-CWJGSI
```

```bash
$ cd protected
$ python -m example1 S7EW55-AWQPPE-SQETCC-CWJGSI 10
Product key expired on 2019-08-17
```

### Debugging

In case your application stops working after obfuscating its code, there are several interesting options for `codeclose protect` that may help you find the problematic point.

* `--disable-encryption`: disable encryption for the entire project. This way, if your application fails, you will know exactly at what line it happens.
* `--name-obfuscation light`: instead of replacing all identifiers by random keywords, it just adds a random number as a sufix. This way you can understand the code even if it is obfuscated.
* `--disable-string-obfuscation`: disables string obfuscation. All strings will remain intact.

After you find the problem, you will probably need to fix it by either keeping an specific identifier intact or keeping the attributes of an object intact.

For fixing those problems, you can use the `--keep-identifier IDENTIFIER` and `--keep-attributes IDENTIFIER` options. Just remember that, in order to keep the attributes of an identifier, you must also keep the identifier too---this means that if you use `--keep-attributes XXX`, you must also use `--keep-identifier XXX`, or otherwise Codeclose will replace "XXX" by some random keywords and will not keep its attributes.

### Limitations

Codeclose has lots of limitations. This section describes the most highlighted.

#### A long list of `--keep-identifier` elements is required

Python code is easy to parse syntactically, but due to its [duck typing nature](https://en.wikipedia.org/wiki/Duck_typing#:~:text=Duck%20typing%20in%20computer%20programming,determined%20by%20an%20object's%20type.), it is hard to parse semantically. When Codeclose finds an identifier, there is no easy way to know what kind of object it actually is without running the code.

If an object is an instance of a third-party library, Codeclose will obfuscate its attributes anyway, and you will need to use `--keep-identifier` and `--keep-attributes` to prevent it.

#### The AES decryption key is embedded within the product

Since the AES decryption key is embedded within the product, an attacker could do some reverse engineering through the obfuscated code to extract it and decrypt all the encrypted code.

However, your application **needs** this key to decrypt and run the encrypted source code, and it does not matter how it gets it: an attacker will always be able to extract it. If your application can read the key, an attacker with enough patience can too.

You can set up an online service to provide the AES key only to licensed users that provide valid product keys. However, an attacker then just needs a valid product key to be able to decrypt all the code.

#### The old time change trick

When Codeclose checks the expiration date of a product key, it compares it with the local time of the machine where it is running, so users can set back their clocks to bypass this protection.

You can implement some counter-measures to prevent this, like comparing the local time with an online service, or detecting if users set back their clocks since the last time they run your application.