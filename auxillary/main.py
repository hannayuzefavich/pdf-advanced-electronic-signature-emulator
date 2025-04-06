import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.messagebox import showerror
from tkinter import filedialog
import rsa
import os
from encryption import encryptPrivateKey


class KeyGenerator(ttk.Frame):
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

    def generate(self):
        if not self.path.get():
            messagebox.showinfo("Missing Path", "Empty path")
            return
        if not self.code.get():
            messagebox.showinfo("Missing Pin", "Empty pin")
            return
        private_key, public_key = rsa.newkeys(4096)
        public_key_path = os.path.join(self.path.get(), "public.pem")
        with open(public_key_path, "wb") as pub_file:
            pub_file.write(public_key.save_pkcs1("PEM"))

        private_key_encrypted = self.encrypt_private_key()

        private_key_path = os.path.join(self.path.get(), "private.pem")
        with open(private_key_path, "wb") as priv_file:
            priv_file.write(private_key.save_pkcs1("PEM"))


    def encrypt_private_key(self):
        pass

    def browse_file(self):
        file_path = filedialog.askdirectory(
            title="Save file",
        )

        if file_path:
            self.path.config(state="normal")
            self.path.delete(0, tk.END)
            self.path.insert(0, file_path)
            self.path.config(state="readonly")

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title('Key generator')
        self.geometry('400x300')
        self.resizable(False, False)



if __name__ == "__main__":
    app = App()
    KeyGenerator(app)
    app.mainloop()
