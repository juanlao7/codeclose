# Example to reproduce https://github.com/juanlao7/codeclose/issues/1#issuecomment-814175447

# These identifiers should be obfuscated.
import copy
sort = 1

# But the attributes of this object should be kept.
attributesKept = [2, 1]
attributesKept.copy()
attributesKept.sort()
