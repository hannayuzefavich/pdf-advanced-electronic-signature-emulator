"""
@file main-app/main.py
@brief Main application with GUI for signing and verifying PDF documents using qualified electronic signatures
@details Implements the PAdES standard using a USB drive containing an AES-encrypted private RSA key.Includes file selection, signature creation, and signature verification GUI components.
@author Hanna Yuzefavich, Szymon Liszewski
@date june 2025
@version 1.0
"""
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import os
import hashlib
from tkinter.simpledialog import askstring
from auxillary.encryption import sign_pdf, verify_pdf_signature, decrypt_private_key, load_bytes_from_file, save_bytes_to_file

class PADES(ttk.Frame):
    """
    @class PADES
    @brief GUI frame for PDF signing and signature verification.
    @details Provides functionality to browse a PDF, sign it using a USB-stored private key, or verify an existing signature.
    """
    def __init__(self, container):
        """
        @brief Constructor for PADES GUI frame
        @param container Parent tkinter library container (root window)
        """
        super().__init__(container)

        self.grid(row=0, column=0, sticky=tk.NSEW)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.path = tk.Entry(self, state="readonly")
        self.path.grid(row=0, column=0)
        browse_button = tk.Button(self, text="Browse", command=self.browse_file)
        browse_button.grid(row=0, column=1)

        sign_button = tk.Button(self, text="Sign", command=self.sign)
        sign_button.grid(row=1, column=0)

        verify_button = tk.Button(self, text="Verify", command=self.verify)
        verify_button.grid(row=1, column=1)

        self.status = tk.Label(self, text="Status: ready", fg="blue")
        self.status.grid(row=2, column=0, columnspan=2, pady=10)

    def browse_file(self):
        """
        @brief Opens file dialog to select a PDF file.
        @details The selected file path is displayed in a read-only text field.
        """

        file_path = filedialog.askopenfile(
            title="wybierz plik",
            filetypes=[("Pliki PDF", "*.pdf")]
        )

        #insert selected path into input field
        if file_path is not None and file_path.name.endswith(".pdf"):
            self.path.config(state="normal")
            self.path.delete(0, tk.END)
            self.path.insert(0, file_path.name)
            self.path.config(state="readonly")
        else:
            messagebox.showerror("Only pdf files are allowed.")
            file_path = None

    def find_usb_drive(self):
        """
        @brief Attempts to detect a USB drive containing the encrypted private key.
        @return Drive path string if found, otherwise None.
        """
        for drive in [f"{d}:\\" for d in "DEFGHIJKLMNOPQRSTUVWXYZ"]:
            if os.path.exists(os.path.join(drive, "private.pem")):
                return drive
        return None


    def decrypt_private_key_from_usb(self, usb_drive_path):
        """
        @brief Prompts user for PIN and decrypts private key from USB.
        @param usb_drive_path Path to the USB drive.
        @return Tuple of (decrypted_key_bytes, error_message). Error message is None on success.
        """
        pin = askstring("PIN", "Enter your PIN:", show="*")
        if not pin:
            return None, "PIN not provided"
        try:
            pin_hash = self.hash_pin(pin)
            encrypted = load_bytes_from_file(os.path.join(usb_drive_path, "private.pem"))
            decrypted = decrypt_private_key(pin_hash, encrypted)
            return decrypted, None
        except Exception as e:
            return None, f"Decryption failed: {e}"


    def hash_pin(self, pin):
        """
        @brief Hashes PIN with SHA-256.
        @param pin String containing the user PIN.
        @return 32-byte hash digest.
        """
        return hashlib.sha256((pin.encode("utf-8"))).digest()


    def sign(self):
        """
        @brief Signs the selected PDF file.
        @details Loads the private key from USB, decrypts it using user PIN, and signs the document.
        """
        file_path = self.path.get()
        if not file_path:
            messagebox.showerror("No file selected")
            return
        self.status.config(text="Status: Detecting USB drive", fg="yellow")
        usb_path = self.find_usb_drive()
        if not usb_path:
            messagebox.showerror("Error", "No USB drive")
            self.status.config(text="Status: USB drive not found", fg="red")
            return
        self.status.config(text="Status: Decrypting key", fg="yellow")
        decrypted_key, error = self.decrypt_private_key_from_usb(usb_path)
        if error:
            messagebox.showerror("Error", error)
            self.status.config(text="Status: Decryption failed", fg="red")
            return
        temp_key_file = "temp_key.pem"
        save_bytes_to_file(decrypted_key, temp_key_file)
        cert_path = os.path.join(usb_path, "cert.pem")
        output_path = file_path.replace(".pdf", "_signed.pdf")
        try:
            sign_pdf(file_path, output_path, temp_key_file, cert_path)
            self.status.config(text="Success: Signed PDF saved as:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Signing PDF failed: {e}")
            self.status.config(text="Status: Signed PDF failed", fg="red")
            return


    def verify(self):
        """
        @brief Verifies the signature of the selected PDF.
        @details Uses the user-selected certificate file to verify the digital signature.
        """
        file_path = self.path.get()
        if not file_path:
            messagebox.showerror("Error", "No PDF selected.")
            return

        cert_path = filedialog.askopenfilename(
            title="Select cert.pem file",
            filetypes=[("PEM", "*.pem")]
        )
        if not cert_path:
            return

        try:
            self.status.config(text="Status: Verifying...", fg="orange")
            verify_pdf_signature(file_path, cert_path)
            self.status.config(text="Status: Signature valid", fg="green")
            messagebox.showinfo("Verified", "Signature is valid.")
        except Exception as e:
            self.status.config(text="Status: Invalid signature", fg="red")
            messagebox.showerror("Verification failed", str(e))

class mainApp(tk.Tk):
    """
    @class mainApp
    @brief Main application window for the PADES GUI.
    """
    def __init__(self):
        """
        @brief Initializes the main application window.
        """
        super().__init__()

        self.title('Key generator')
        self.geometry('400x300')
        self.resizable(False, False)


if __name__ == "__main__":
    app = mainApp()
    PADES(app)
    app.mainloop()