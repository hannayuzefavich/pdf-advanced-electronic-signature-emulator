import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def generateRSAkeys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key

def encryptPrivateKey(symmetric_key, private_key):
    iv = os.urandom(16)
    cipher_algorithm = algorithms.AES(symmetric_key)
    cipher_mode = modes.CBC(iv) #todo: check what mode should be here

    cipher = Cipher(cipher_algorithm, cipher_mode, backend=default_backend())
    encryptor = cipher.encryptor()

    encrypted_data = encryptor.update(private_key) + encryptor.finalize()

    return encrypted_data