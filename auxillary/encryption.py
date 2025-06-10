"""
@file encryption.py
@brief Keys creation and encryption, certificate creation utilities for PDF signing
@details Helper module providing RSA keys generation, certificate creation and AES key encryption
@author Hanna Yuzefavich, Szymon Liszewski
@date june 2025
@version 1.0
"""
#Imports
import os
import hashlib
from datetime import datetime, timedelta

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization, padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.x509.oid import NameOID

from pyhanko.sign import signers
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter

from pyhanko.keys import load_cert_from_pemder
from pyhanko_certvalidator import ValidationContext
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import validate_pdf_signature


## @brief Generate RSA keys: private and public

## @details Function creates a private-public key pair using cryptography library.

## @return Tuple containing (private_key, public_key)

## @note Key size is set to 4096 bits for enhanced security and due to project requirements
def generate_rsa_keys():

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )
    return private_key, private_key.public_key()

## @brief Creates a self-signed certificate

    ## @details Function generates an X.509 certificate for the given private

    ## key with basic constraints ank key usage extensions suitable for

    ## digital signing.

    ## @param private_key RSA private key for signing the certificate

    ## @param common_name string containing the common name for the certificate subject

    ## @return X.509 certificate object

    ## @note organization name is hardcoded to 'test'
def create_self_signed_cert(private_key, common_name):


    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"PL"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"test"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    key_usage = x509.KeyUsage(
        digital_signature=True,
        content_commitment=True,
        key_encipherment=False,
        data_encipherment=False,
        key_agreement=False,
        key_cert_sign=True,
        crl_sign=True,
        encipher_only=False,
        decipher_only=False
    )

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True
        )
        .add_extension(
            key_usage, critical=True
        )
        .sign(private_key, hashes.SHA256(), default_backend())
    )
    return cert


##@brief Encrypts private key usng AES algorithm
#@details Function uses AES in CBC mode with PKCS7 padding. A random 16-byte IV
         #is generated and prepended to the encrypted data.
#@param symmetric_key 32-byte key for AES encryption
#@param private_key_bytes Raw bytes of the private key to encrypt
#@return encrypted data with prepended iv
def encrypt_private_key(symmetric_key: bytes, private_key_bytes: bytes) -> bytes:

    iv = os.urandom(16)

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(private_key_bytes) + padder.finalize()

    cipher = Cipher(algorithms.AES(symmetric_key), modes.CBC(iv))
    encryptor = cipher.encryptor()

    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    return iv + encrypted_data

##@brief Decrypts data using AES in CBC mode with given symmetric key
#@details Function decrypts data encrypted by encrypt_private_key()
#Extracts IV from the first 16 bytes and uses it to decrypt the remaining data.
#@param symmetric_key 32-byte key used for decryption (same as encryption)
#@param encrypted_data encrypted data with IV prepended
#@return decrypted private key data
#@note symmetric_key must be the same key used for encryption
def decrypt_private_key(symmetric_key: bytes, encrypted_data: bytes) -> bytes:

    iv = encrypted_data[:16]
    encrypted = encrypted_data[16:]

    cipher = Cipher(algorithms.AES(symmetric_key), modes.CBC(iv))
    decryptor = cipher.decryptor()

    padded_data = decryptor.update(encrypted) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    return data

##@brief Saves byte data to a file
#@details Writes raw byte data to a file with a given name
#@param data Byte data to save
#@param filename File name
#@return None
def save_bytes_to_file(data: bytes, filename: str):
    with open(filename, 'wb') as f:
        f.write(data)


def load_bytes_from_file(filename: str) -> bytes:
    """
    @brief Loads byte data from a file
    @details Opens and reads the data from a file into memory as bytes
    @param filename Path to file to be read
    @return Byte content of file
    """
    with open(filename, 'rb') as f:
        return f.read()

 ## @brief Saves public key to PEM-formatted file

    ## @details Serializes the public key using PEM format and writes it to file

    ## @param public_key Public key to be serialized and saved

    ## @param filename Path to the file to be saved
def save_public_key(public_key, filename: str):



    ## @return None
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    with open(filename, 'wb') as f:
        f.write(pub_bytes)

 ## @brief Loads public key from PEM-formatted file

    ## @details Reads and deserializes the public key from PEM-formatted file

    ## @param filename Path to the file to be read

    ## @return Deserialized public key from file
def load_public_key(filename: str):


    with open(filename, 'rb') as f:
        data = f.read()
    return serialization.load_pem_public_key(data, backend=default_backend())


## @brief Digitally signs a PDF file using RSA private key and X.509 certificate

    ## @details Loads a signer from the given private key and X509 certificate paths,

    ## signs the input PDF file and saves the signed version

    ## @param pdf_path Path to PDF file to be signed

    ## @param signed_pdf_path Path to save signed PDF file

    ## @param private_key_path Path to private key file

    ## @param cert_path Path to certificate file

    ## @return None
def sign_pdf(pdf_path: str, signed_pdf_path: str,
             private_key_path: str, cert_path: str):


    cms_signer = signers.SimpleSigner.load(
        private_key_path, cert_path,
    )

    with open(pdf_path, 'rb') as doc:
        w = IncrementalPdfFileWriter(doc)
        out = signers.sign_pdf(
            w, signers.PdfSignatureMetadata(field_name='Signature1'),
            signer=cms_signer,
        )

    with open(signed_pdf_path, 'wb') as f:
        f.write(out.getvalue())
    print(f"PDF signed and saved to {signed_pdf_path}")

## @brief Verifies digital PDF signature of a signed PDF file

    ## @details Uses the given certificate as a trust source to verify the signature

    ## @param pdf_path Path to PDF file to be verified

    ## @param cert_path Path to certificate file

    ## @return None
def verify_pdf_signature(pdf_path: str, cert_path: str):
    root_cert = load_cert_from_pemder(cert_path)
    vc = ValidationContext(trust_roots=[root_cert])

    with open(pdf_path, 'rb') as doc:
        r = PdfFileReader(doc)
        sig = r.embedded_signatures[0]
        status = validate_pdf_signature(sig, vc)
        print(status.pretty_print_details())

