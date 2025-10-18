import hashlib

data1 = b"hello world"
data2 = b"Hello world"

print(hashlib.sha256(data1).hexdigest())
print(hashlib.sha256(data2).hexdigest())