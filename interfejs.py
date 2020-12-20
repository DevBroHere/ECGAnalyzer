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

from PIL import Image, ImageTk

LARGE_FONT = ("VERDANA", 12)
NORM_FONT = ("VERDANA", 10)
SMALL_FONT = ("VERDANA", 8)

#Stałe używane do tymczasowego zapisu
sampleType = 16
sampleFrequency = None
sampleResolution = None
sampleVoltage = None

##print(style.available) #Wyświetlanie możliwych styli
style.use("bmh") #Wybranie danego stylu wyświetlania wykresów

#Globalne dane ekg (bieżące)
x_global = None
y_global = None

def popupmsg(msg):
    popup = tk.Tk()
    
    popup.wm_title("!")
    label = ttk.Label(popup, text = msg, font = NORM_FONT)
    label.pack(side = "top", fill = "x", pady = 10)
    B1 = ttk.Button(popup, text = "Okay", command = popup.destroy)
    B1.pack()
    popup.mainloop()
    
def loadDataOptions():
    typed = None
    frequencyd = None
    resolutiond = None
    voltaged = None

    window = tk.Tk() # tworzenie okna głównego
    window.title( "Load settings" ) # ustawienie tytułu okna głównego
    window.resizable(False, False)
    labelFrame1 = tk.LabelFrame(window, text = "Type of variables")
    labelFrame1.grid(row = 0, column = 0)
    rb_var = tk.StringVar()
    rb_16 = tk.Radiobutton(labelFrame1, variable = rb_var, value = "16", text = "16-bit")
    rb_32 = tk.Radiobutton(labelFrame1, variable = rb_var, value = "32", text = "32-bit")
    rb_var.set(str(sampleType))
    rb_16.pack()
    rb_32.pack()

    labelFrame2 = tk.LabelFrame(window, text = "Sampling frequency", width = 1, height = 10)
    labelFrame2.grid(row = 0, column = 1)
    frequency = tk.Entry(labelFrame2, width = 5)
    if sampleFrequency:   
        frequency.delete(0, "end")
        frequency.insert(0, sampleFrequency)
    frequency.pack()

    labelFrame3 = tk.LabelFrame(window, text = "Resolution", width = 1, height = 10)
    labelFrame3.grid(row = 1, column = 0)
    resolution = tk.Entry(labelFrame3, width = 5)
    if sampleResolution:
        resolution.delete(0, "end")
        resolution.insert(0, sampleResolution)
    resolution.pack()

    labelFrame4 = tk.LabelFrame(window, text = "Input voltage", width = 1, height = 10)
    labelFrame4.grid(row = 1, column = 1) #pack()#fill = "both", expand = "yes"
    voltage = tk.Entry(labelFrame4, width = 5)
    if sampleVoltage:
        voltage.delete(0, "end")
        voltage.insert(0, sampleVoltage)
    voltage.pack()

    def apply():
        global x_global, y_global
        global sampleType, sampleFrequency, sampleResolution, sampleVoltage
        sampleType = int(rb_var.get())
        sampleFrequency = int(frequency.get())
        sampleResolution = int(resolution.get())
        sampleVoltage = int(voltage.get())
        if sampleType == 16:
            ekgfile = np.fromfile(filename, dtype = np.int16)
        elif sampleType == 32:
            ekgfile = np.fromfile(filename, dtype = np.int32)
        x = []
        y = []
        time = 0
        for row in ekgfile:
            y.append(row)
            x.append(time)
            time += 1/sampleFrequency

        b = (2**sampleResolution) - 1
        for i in range(len(y)):
            y[i] = y[i] * (sampleVoltage/b)

        x_global = x
        y_global = y

        a.clear()
        a.plot(x, y)
        canvas.draw()

        window.destroy()
        

    applyButton = tk.Button(window, text = "Save and apply", command = lambda: apply())
    applyButton.grid(row=2, column = 1, sticky = "E", pady = 5)

    window.mainloop() # wywołanie pętli komunikatów

def browseFiles():
        global filename
        filename = filedialog.askopenfilename(initialdir = "/", 
                                          title = "Select a File", 
                                          filetypes = (("all files", 
                                                        "*.*"),
                                                       ("Text files", 
                                                        "*.txt*")))
        if filename: 
            loadDataOptions()

def saveFiles(): 
    a = filedialog.asksaveasfilename(filetypes=(("PNG Image", "*.png"),("All Files", "*.*")), 
            defaultextension='.png', title="Window-2")
    if a:
        plt.savefig(a)

window = tk.Tk()
#tk.Tk.iconbitmap(self, default = "plik") Funkcja do ustawiania ikonki
window.state('zoomed')
window.title("EcgAnalizer")

#Tworzenie głównego paska menu
menubar = tk.Menu(window)
        
#Tworzenie części paska "File"
filemenu = tk.Menu(menubar, tearoff = 0)
filemenu.add_command(label = "Open...",
                             command = lambda: browseFiles())
filemenu.add_separator()
filemenu.add_command(label = "Save",
                             command = lambda: saveFiles())
filemenu.add_command(label = "Save as...",
                             command = lambda: popupmsg("Not supported yet"))
filemenu.add_separator()
filemenu.add_command(label = "Exit",
                             command = exit)
menubar.add_cascade(label = "File", menu = filemenu)
        
#Tworzenie części paska "Options"
optionsmenu = tk.Menu(menubar, tearoff = 0)
windowmenu = tk.Menu(optionsmenu, tearoff = 0)
numberofwindowsMenu = tk.Menu(windowmenu, tearoff = 0)
analyzesectionMenu = tk.Menu(windowmenu, tearoff = 0)

optionsmenu.add_command(label = "Samples",
                                command = lambda: popupmsg("Not supported yet"))

numberofwindowsMenu.add_radiobutton(label = "1 window")
numberofwindowsMenu.add_radiobutton(label = "2 windows")

analyzesectionMenu.add_radiobutton(label = "right")
analyzesectionMenu.add_radiobutton(label = "left")
analyzesectionMenu.add_radiobutton(label = "top")
analyzesectionMenu.add_radiobutton(label = "down")


menubar.add_cascade(label = "Options", menu = optionsmenu)
optionsmenu.add_cascade(label = "Configure window", menu = windowmenu)
windowmenu.add_cascade(label = "Windows", menu = numberofwindowsMenu)
windowmenu.add_cascade(label = "Analyze section", menu = analyzesectionMenu)
        
#Tworzenie części paska "ECG analysis"
ecgmenu = tk.Menu(menubar, tearoff = 0)
ecgmenu.add_command(label = "Filter",
                                command = lambda: popupmsg("Not supported yet"))
ecgmenu.add_command(label = "Analyze",
                                command = lambda: popupmsg("Not supported yet"))
menubar.add_cascade(label = "ECG analysis", menu = ecgmenu)
        
#Tworzenie części paska "Help"
helpmenu = tk.Menu(menubar, tearoff = 0)
helpmenu.add_command(label = "About program",
                                command = lambda: popupmsg("Not supported yet"))
helpmenu.add_separator()
helpmenu.add_command(label = "Help",
                                command = lambda: popupmsg("Not supported yet"))
menubar.add_cascade(label = "Help", menu = helpmenu)

#Tworzenie sekcji toolbar
toolbar = tk.Frame(window, bd=1, relief=RAISED)

img = Image.open("save icon3.png")
eimg = ImageTk.PhotoImage(img)

exitButton = tk.Button(toolbar, image=eimg, relief=FLAT,
                    command=quit)
exitButton.image = eimg
exitButton.pack(side=LEFT, padx=2, pady=2)

toolbar.grid(row = 0, column = 0, columnspan = 2, sticky = "nsew")
        
#Zatwierdzenie menu
window.config(menu = menubar)


container = tk.Frame()
container2 = tk.Frame()

container.grid(row=1, column=0, sticky="nsew")
container2.grid(row=1, column=1, sticky="nsew")
#********************************
#container.grid(row=0, column=0, sticky="nsew")
#container2.grid(row=1, column=0, sticky="nsew")
#********************************
#container2.grid(row=0, column=0, sticky="nsew")
#container.grid(row=0, column=1, sticky="nsew")

window.grid_columnconfigure(0, weight=3)
window.grid_columnconfigure(1, weight=1)
window.grid_rowconfigure(0, weight=1)
window.grid_rowconfigure(1, weight=1000)
#********************************
#window.grid_rowconfigure(0, weight = 3)
#window.grid_rowconfigure(1, weight = 1)
#window.grid_columnconfigure(0, weight = 1)
#********************************
#window.grid_columnconfigure(0, weight=1)
#window.grid_columnconfigure(1, weight=3)
#window.grid_rowconfigure(0, weight=1)

var = StringVar()
label = Label( container2, textvariable=var)

var.set("ECG analysis")
label.pack()

f = Figure() #Tworzymy obiekt Figure
#figsize to wielkość tworzonej przestrzeni na wykres
#(szerokość, wysokość) w calach, dpi to piksele na cal.
a = f.add_subplot(212)#Możemy dodawać kolejne okna wedle upodobań
b = f.add_subplot(211)

canvas = FigureCanvasTkAgg(f, master = container)
canvas.draw()
canvas.get_tk_widget().pack(side = tk.TOP, fill=tk.BOTH, expand = True)

toolbar = NavigationToolbar2TkAgg(canvas, container)
toolbar.update()
canvas._tkcanvas.pack(side = tk.TOP, fill=tk.BOTH, expand = True)


window.mainloop()
