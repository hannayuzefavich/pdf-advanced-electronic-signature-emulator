import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showerror
from tkinter import filedialog


class PADES(ttk.Frame):
    def __init__(self, container):
        super().__init__(container)

        self.grid(row=0, column=0, sticky=tk.NSEW)

        # grid configuration for centering button
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # add path input field
        self.path = tk.Entry(self, state="readonly")
        self.path.grid(row=0, column=0)
        browse_button = tk.Button(self, text="Browse", command=self.browse_file)
        browse_button.grid(row=0, column=1)

        sign_button = tk.Button(self, text="Sign", command=self.sign)
        sign_button.grid(row=1, column=0)

    def browse_file(self):
        file_path = filedialog.askopenfile(
            title="wybierz plik",
            filetypes=[("Pliki PDF", "*.pdf")]
        )

        #insert selected path into input field
        if file_path:
            self.path.config(state="normal")
            self.path.delete(0, tk.END)
            self.path.insert(0, file_path.name)
            self.path.config(state="readonly")

    #todo: finish function for signing documents
    def sign(self):
        pass

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