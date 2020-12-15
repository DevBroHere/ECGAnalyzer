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
#Zrobiłem sobie coś
import urllib
import json

import pandas as pd
import numpy as np

LARGE_FONT = ("VERDANA", 12)
NORM_FONT = ("VERDANA", 10)
SMALL_FONT = ("VERDANA", 8)

sampleType = 16
sampleFrequency = None
sampleResolution = None
sampleVoltage = None

##print(style.available) #Wyświetlanie możliwych styli
style.use("bmh") #Wybranie danego stylu wyświetlania wykresów

f = Figure() #Tworzymy obiekt Figure
#figsize to wielkość tworzonej przestrzeni na wykres
#(szerokość, wysokość) w calach, dpi to piksele na cal.
filename = None
a = f.add_subplot(111)#Możemy dodawać kolejne okna wedle upodobań
#b = f.add_subplot(212)
x_global = None
y_global = None

class EcgAnalizer(tk.Tk):

    def __init__(self):
        tk.Tk.__init__(self)
        #tk.Tk.iconbitmap(self, default = "plik") Funkcja do ustawiania ikonki
        tk.Tk.wm_title(self, "EcgAnalizer")
        container = tk.Frame(self)

        container.pack(side = "top", fill="both", expand = True)

        container.grid_rowconfigure(0, weight = 1)
        container.grid_columnconfigure(0, weight = 1)

        #Tworzenie głównego paska menu
        menubar = tk.Menu(container)
        
        #Tworzenie części paska "File"
        filemenu = tk.Menu(menubar, tearoff = 0)
        filemenu.add_command(label = "Open...",
                             command = lambda: browseFiles())
        filemenu.add_separator()
        filemenu.add_command(label = "Save",
                             command = lambda: popupmsg("Not supported yet"))
        filemenu.add_command(label = "Save as...",
                             command = lambda: popupmsg("Not supported yet"))
        filemenu.add_separator()
        filemenu.add_command(label = "Exit",
                             command = exit)
        menubar.add_cascade(label = "File", menu = filemenu)
        
        #Tworzenie części paska "Options"
        optionsmenu = tk.Menu(menubar, tearoff = 0)
        optionsmenu.add_command(label = "Sample",
                                command = lambda: popupmsg("Not supported yet"))
        optionsmenu.add_command(label = "Configure window",
                                command = lambda: popupmsg("Not supported yet"))
        menubar.add_cascade(label = "Options", menu = optionsmenu)
        
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
        
        #Zatwierdzenie menu
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
        
    def refresh(self):
        None

    def plotData(self, x, y):
        ECG_page.plotData(self, x, y)


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

        canvas = FigureCanvasTkAgg(f, self)
        canvas.draw()
        canvas.get_tk_widget().pack(side = tk.TOP, fill=tk.BOTH, expand = True)

        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side = tk.TOP, fill=tk.BOTH, expand = True)
        
    def plotData(self, x, y):
        a.clear()
        a.plot(x, y)
        self.update()


        
app = EcgAnalizer()
app.geometry("800x600")

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

        app.plotData(x,y)

        window.destroy()
        

    applyButton = tk.Button(window, text = "Save and apply", command = lambda: apply())
    #saveButton = tk.Button(window, text = "Save configuration", command = None)
    applyButton.grid(row=2, column = 1, sticky = "E", pady = 5)
    #saveButton.grid(row=2, column = 0, sticky = "W", pady = 5)

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

    


app.mainloop()
