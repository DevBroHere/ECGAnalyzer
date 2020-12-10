import tkinter as tk
from tkinter import ttk

from tkinter import *
from tkinter import filedialog

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
try:
    from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg
except ImportError:
    from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
from matplotlib import pyplot as plt

import urllib
import json

import pandas as pd
import numpy as np

LARGE_FONT = ("VERDANA", 12)
NORM_FONT = ("VERDANA", 10)
SMALL_FONT = ("VERDANA", 8)



##print(style.available) #Wyświetlanie możliwych styli
style.use("bmh") #Wybranie danego stylu wyświetlania wykresów

f = Figure() #Tworzymy obiekt Figure
#figsize to wielkość tworzonej przestrzeni na wykres
#(szerokość, wysokość) w calach, dpi to piksele na cal.
filename = None
a = f.add_subplot(111)#Możemy dodawać kolejne okna wedle upodobań
##b = f.add_subplot(212)

def popupmsg(msg):
    popup = tk.Tk()
    
    popup.wm_title("!")
    label = ttk.Label(popup, text = msg, font = NORM_FONT)
    label.pack(side = "top", fill = "x", pady = 10)
    B1 = ttk.Button(popup, text = "Okay", command = popup.destroy)
    B1.pack()
    popup.mainloop()

def animate(i):
    if filename:
        ekgfile = np.fromfile(filename, dtype = np.int16)
        x = []
        y = []
        time = 0
        for row in ekgfile:
            y.append(row)
            x.append(time)
            time += 1/1000

        b = (2**12) - 1
        for i in range(len(y)):
            y[i] = y[i] * (20/b)

        a.clear()
        a.plot(x, y)

        

class EcgAnalizer(tk.Tk):

    def __init__(self):
        tk.Tk.__init__(self)
        #tk.Tk.iconbitmap(self, default = "plik") Funkcja do ustawiania ikonki
        tk.Tk.wm_title(self, "EcgAnalizer")
        container = tk.Frame(self)

        container.pack(side = "top", fill="both", expand = True)

        container.grid_rowconfigure(0, weight = 1)
        container.grid_columnconfigure(0, weight = 1)

        menubar = tk.Menu(container)
        filemenu = tk.Menu(menubar, tearoff = 0)
        filemenu.add_command(label = "Save settings",
                             command = lambda: popupmsg("Not supported yet!"))
        filemenu.add_separator()
        filemenu.add_command(label = "Exit", command = quit)
        menubar.add_cascade(label = "File", menu = filemenu)

        tk.Tk.config(self, menu = menubar)

        self.frames = {}

        for F in (StartPage, ECG_page):

            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row = 0, column = 0, sticky = "nsew")

        self.show_frame(StartPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    def browseFiles(self):
        global filename
        filename = filedialog.askopenfilename(initialdir = "/", 
                                          title = "Select a File", 
                                          filetypes = (("Text files", 
                                                        "*.txt*"), 
                                                       ("all files", 
                                                        "*.*")))

class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text = "BETA ECG analize application\n use a your own risk")
        label.pack(pady = 10, padx = 10)

        button1 = ttk.Button(self, text = "Agree",
                            command = lambda: controller.show_frame(ECG_page))
        button1.pack()

        button2 = ttk.Button(self, text = "Disagree",
                            command = quit)
        button2.pack()



class ECG_page(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text = "Graph page")
        label.pack(pady = 10, padx = 10)

        button1 = ttk.Button(self, text = "Back to menu",
                            command = lambda: controller.show_frame(StartPage))
        button1.pack()

        button2 = ttk.Button(self, text = "Browse files",
                            command = lambda: controller.browseFiles())
        button2.pack()

        

        canvas = FigureCanvasTkAgg(f, self)
        canvas.draw()
        canvas.get_tk_widget().pack(side = tk.TOP, fill=tk.BOTH, expand = True)

        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side = tk.TOP, fill=tk.BOTH, expand = True)

        
app = EcgAnalizer()
app.geometry("800x600")
anim = animation.FuncAnimation(f, animate, interval=1000)
app.mainloop()
