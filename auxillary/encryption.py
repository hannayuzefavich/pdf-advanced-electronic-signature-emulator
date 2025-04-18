import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

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

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(private_key) + padder.finalize()

    cipher_algorithm = algorithms.AES(symmetric_key)
    cipher_mode = modes.CBC(iv) #todo: check what mode should be here

    cipher = Cipher(cipher_algorithm, cipher_mode, backend=default_backend())
    encryptor = cipher.encryptor()

    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    encrypted_data = iv + encrypted_data

    return encrypted_data

def decryptPrivateKey(symmetric_key, encrypted_private_key):
    IV_SIZE = 16
    cipher_algorithm = algorithms.AES(symmetric_key)
    iv = encrypted_private_key[:IV_SIZE]
    encrypted_private_key = encrypted_private_key[IV_SIZE:]

    cipher_mode = modes.CBC(iv)
    cipher = Cipher(cipher_algorithm, cipher_mode, backend=default_backend())
    decryptor = cipher.decryptor()

    decrypted_private_key = decryptor.update(encrypted_private_key) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    decrypted_data = unpadder.update(decrypted_private_key) + unpadder.finalize()

    return decrypted_data