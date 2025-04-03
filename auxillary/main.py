import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showerror
import rsa


class KeyGenerator(ttk.Frame):
    def __init__(self, container):
        super().__init__(container)

        self.generate_button = tk.Button(self, text='Generate key pair', command=self.begin_setup, width=30, relief='raised', height=10)
        self.generate_button.grid(column=3, row=3, columnspan=3, sticky=tk.NSEW)

        self.grid(padx=10, pady=10, sticky=tk.NSEW)

    def begin_setup(self):
        self.setup_window = tk.Toplevel(self)
        self.setup_window.title('Setup')
        self.setup_window.geometry('400x300')


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
