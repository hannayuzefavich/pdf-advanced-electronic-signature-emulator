import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showerror
import rsa


class KeyGenerator(ttk.Frame):
    def __init__(self, container):
        super().__init__(container)

        self.generate_button = tk.Button(self, text='Generate key pair', command=self.begin_setup, width=30, relief='raised', height=10)
        #nie moge wycentrowac tego przycisku xd
        self.generate_button.grid(column=3, row=3, columnspan=3, sticky=tk.NSEW)

        self.grid(padx=10, pady=10, sticky=tk.NSEW)
    #tutaj chce zrobic takiego wizarda w osobnym oknie, z krokami:
    # 1.podanie sciezki do zapisania na dysku klucza publicznego
    # 2.podanie pina do zaszyfrowania klucza prywatnego
    # 3.po zweryfikowaniu, czy pola zostały wypełnione, wywołac funkcję generate() -> rsa.newkeys(4096), zapisanie klucza publicznego
    # na dysku, zaszyfrowanie prywatnego
    # 4. zamknięcie okna dodatkowego - "wizarda"
    # 5. messagebox że klucze wygenerowane
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
