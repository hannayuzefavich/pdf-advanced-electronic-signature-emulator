import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import os
import hashlib
from tkinter.simpledialog import askstring
from auxillary.encryption import sign_pdf, verify_pdf_signature, decrypt_private_key, load_bytes_from_file, save_bytes_to_file

class PADES(ttk.Frame):
    def __init__(self, container):
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
        for drive in [f"{d}:\\" for d in "DEFGHIJKLMNOPQRSTUVWXYZ"]:
            if os.path.exists(os.path.join(drive, "private.pem")):
                return drive
        return None


    def decrypt_private_key_from_usb(self, usb_drive_path):
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
        return hashlib.sha256((pin.encode("utf-8"))).digest()

    #todo: finish function for signing documents
    def sign(self):
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


    # todo: finish function for verifying signed documents
    def verify(self):
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
    def __init__(self):
        super().__init__()

        self.title('Key generator')
        self.geometry('400x300')
        self.resizable(False, False)


if __name__ == "__main__":
    app = mainApp()
    PADES(app)
    app.mainloop()