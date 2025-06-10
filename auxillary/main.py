"""
@file auxillary/main.py
@brief Auxiliary application with keys creation and encryption, certificate generation
@details Auxiliary application with GUI which generates private and public keys, certificate
@author Hanna Yuzefavich, Szymon Liszewski
@date june 2025
@version 1.0
"""

import hashlib
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog
import os

from cryptography.hazmat.primitives import serialization

from auxillary.encryption import save_public_key
from encryption import encrypt_private_key, decrypt_private_key, generate_rsa_keys, create_self_signed_cert, \
    save_bytes_to_file

##@class KeyGenerator
    #@brief GUI frame for generating RSA key pairs and saving them securely after encryption
    #@details Allows users to enter a pin for encryption and select a directory to save public key, encrypted private key and certificate
class KeyGenerator(ttk.Frame):

    ## @brief Constructor for KeyGenerator

    ## @param container Parent tkinter library container (the root window)
    def __init__(self, container):


        super().__init__(container)

        self.code = None
        self.setup_window = None
        self.path = None
        self.grid(row=0, column=0, sticky=tk.NSEW)

        # grid configuration for centering button
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        self.generate_button = tk.Button(self, text='Generate key pair', command=self.begin_setup, relief='raised')
        self.generate_button.grid(column=1, row=1, sticky=tk.NSEW, padx=10, pady=10)

    ## @brief Opens a new setup window for key generation

    ## @details Allows user to input a PIN and choose directory for saving files

    ## :return:
    def begin_setup(self):


        self.setup_window = tk.Toplevel(self)
        self.setup_window.title('Setup')
        self.setup_window.geometry('400x300')

        for i in range(5):
            self.grid_rowconfigure(i, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # add path label
        label = tk.Label(self.setup_window, text="location where public key will be stored: ")
        label.grid(row=0, column=0)

        # add path input field
        self.path = tk.Entry(self.setup_window, state="readonly")
        self.path.grid(row=1, column=0)
        browse_button = tk.Button(self.setup_window, text="Browse", command=self.browse_file)
        browse_button.grid(row=1, column=1)

        # add pin label
        label = tk.Label(self.setup_window, text="input your pin: ")
        label.grid(row=2, column=0)

        # add pin input field
        self.code = tk.Entry(self.setup_window, show="•")
        self.code.grid(row=3, column=0)

        # add button that generate rsa keys
        btn = tk.Button(self.setup_window, text='Generate', command=self.generate, relief='raised')
        btn.grid(row=4, column=0, sticky=tk.NSEW)

    ## @brief Generates RSA key pair, encrypts the private key and saves all files

    ## @details Stores public key, certificate, encrypted private key

    ## :return:
    def generate(self):


        if not self.path.get():
            messagebox.showinfo("Missing Path", "Empty path")
            return
        if not self.code.get():
            messagebox.showinfo("Missing Pin", "Empty pin")
            return
        private_key, public_key = generate_rsa_keys()
        public_key_path = os.path.join(self.path.get(), "public.pem")
        cert = create_self_signed_cert(private_key, "test.pl")
        cert_bytes = cert.public_bytes(serialization.Encoding.PEM)
        cert_path = os.path.join(self.path.get(), "cert.pem")
        save_bytes_to_file(cert_bytes, cert_path)

        save_public_key(public_key, public_key_path)

        # todo: this is only for testing
        priv_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )


        private_key_encrypted = encrypt_private_key(hashlib.sha256(self.code.get().encode('utf-8')).digest(), priv_key_bytes)

        private_key_path = os.path.join(self.path.get(), "private.pem")
        save_bytes_to_file(private_key_encrypted, private_key_path)


    ## @brief Opens a file dialog to select directory

    ## @details Updates the entry field with selected directory path

    ## :return:
    def browse_file(self):


        file_path = filedialog.askdirectory(
            title="Save file",
        )

        if file_path:
            self.path.config(state="normal")
            self.path.delete(0, tk.END)
            self.path.insert(0, file_path)
            self.path.config(state="readonly")


##@class App
    #@brief Main application window for launching the KeyGenerator GUI
class App(tk.Tk):

    def __init__(self):

        ## @brief Initializes the main application window
        super().__init__()

        self.title('Key generator')
        self.geometry('400x300')
        self.resizable(False, False)



if __name__ == "__main__":
    app = App()
    KeyGenerator(app)
    app.mainloop()