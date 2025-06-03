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

def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )
    return private_key, private_key.public_key()


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


def encrypt_private_key(symmetric_key: bytes, private_key_bytes: bytes) -> bytes:
    iv = os.urandom(16)

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(private_key_bytes) + padder.finalize()

    cipher = Cipher(algorithms.AES(symmetric_key), modes.CBC(iv))
    encryptor = cipher.encryptor()

    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    return iv + encrypted_data


def decrypt_private_key(symmetric_key: bytes, encrypted_data: bytes) -> bytes:
    iv = encrypted_data[:16]
    encrypted = encrypted_data[16:]

    cipher = Cipher(algorithms.AES(symmetric_key), modes.CBC(iv))
    decryptor = cipher.decryptor()

    padded_data = decryptor.update(encrypted) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    return data


def save_bytes_to_file(data: bytes, filename: str):
    with open(filename, 'wb') as f:
        f.write(data)


def load_bytes_from_file(filename: str) -> bytes:
    with open(filename, 'rb') as f:
        return f.read()


def save_public_key(public_key, filename: str):
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    with open(filename, 'wb') as f:
        f.write(pub_bytes)


def load_public_key(filename: str):
    with open(filename, 'rb') as f:
        data = f.read()
    return serialization.load_pem_public_key(data, backend=default_backend())



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




def verify_pdf_signature(pdf_path: str, cert_path: str):
    root_cert = load_cert_from_pemder(cert_path)
    vc = ValidationContext(trust_roots=[root_cert])

    with open(pdf_path, 'rb') as doc:
        r = PdfFileReader(doc)
        sig = r.embedded_signatures[0]
        status = validate_pdf_signature(sig, vc)
        print(status.pretty_print_details())

if __name__ == "__main__":
    password = "1234"
    password_hash = hashlib.sha256(password.encode("utf-8")).digest()

    # generating keys and certificate
    priv_key, pub_key = generate_rsa_keys()
    cert = create_self_signed_cert(priv_key, "test.pl")

    # change PEM to bytes (without encoding, for comparison)
    priv_key_bytes = priv_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # encoding with AES
    encrypted_priv_key = encrypt_private_key(password_hash, priv_key_bytes)

    # Saving keys to file
    save_bytes_to_file(encrypted_priv_key, 'private_key_encrypted.bin')
    save_bytes_to_file(cert.public_bytes(serialization.Encoding.PEM), 'cert.pem')
    save_bytes_to_file(priv_key_bytes, 'private_key.pem')
    save_public_key(pub_key, 'public_key.pem')

    print("Saved private and public keys and certificate")

    # read and validation
    encrypted_priv_key_loaded = load_bytes_from_file('private_key_encrypted.bin')
    cert_pem_loaded = load_bytes_from_file('cert.pem')

    # key decryption
    decrypted_priv_key_bytes = decrypt_private_key(password_hash, encrypted_priv_key_loaded)

    # comparing decrypted key with original
    assert decrypted_priv_key_bytes == priv_key_bytes
    print("Key was decrypted and verified")

    # loading cert
    loaded_cert = x509.load_pem_x509_certificate(cert_pem_loaded, default_backend())
    print(f"Certificate loaded: {loaded_cert.subject.rfc4514_string()}")

    # read public key
    loaded_pub_key = load_public_key('public_key.pem')
    print(f"Loaded public key: {type(loaded_pub_key)}")

    # write private key to PEM file
    save_bytes_to_file(decrypted_priv_key_bytes, 'private_key_decrypted.pem')
    print("Saved encrypted key to 'private_key_decrypted.pem'")

    sign_pdf('RPI_2023_5_Scrum_Retrospektywa.pdf', 'signed_output.pdf', 'private_key_decrypted.pem', 'cert.pem')

    verify_pdf_signature('signed_output.pdf', 'cert.pem')