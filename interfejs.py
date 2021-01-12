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

import numpy as np
import scipy as scp
from scipy import signal

from PIL import Image, ImageTk

LARGE_FONT = ("VERDANA", 12)
NORM_FONT = ("VERDANA", 10)
SMALL_FONT = ("VERDANA", 8)

##print(style.available) #Wyświetlanie możliwych styli
style.use("bmh") #Wybranie danego stylu wyświetlania wykresów

#Globalne dane ekg (bieżące)
x_global = None
y_global = None

#Lista wyświetlanych wykresów
list_graphs = ["raw"]

#Zmienne opcji konfiguracji okna
windowsNumber = 1

def popupmsg(msg):
    popup = tk.Tk()
    
    popup.wm_title("!")
    label = ttk.Label(popup, text = msg, font = NORM_FONT)
    label.pack(side = "top", fill = "x", pady = 10)
    B1 = ttk.Button(popup, text = "Okay", command = popup.destroy)
    B1.pack()
    popup.mainloop()
    
def loadDataOptions():
    
    def apply():
        global x_global, y_global
        if rb_bitVar.get() == "16":
            ekgfile = np.fromfile(filename, dtype = np.int16)
        elif rb_bitVar.get() == "32":
            ekgfile = np.fromfile(filename, dtype = np.int32)
        x = []
        y = []
        time = 0
        for row in ekgfile:
            y.append(row)
            x.append(time)
            time += 1/float(entry_freq.get())

        b = (2**int(entry_res.get())) - 1
        for i in range(len(y)):
            y[i] = y[i] * (float(entry_volt.get())/b)

        x_global = x
        y_global = y

        a.clear()
        a.plot(x, y)
        canvas.draw()

        window_open.destroy()

    def setToDefault():
        entry_freq.delete(0, "end")
        entry_res.delete(0, "end")
        entry_volt.delete(0, "end")
        
        rb_bitVar.set("16")
        entry_freq.insert(0, 1000)
        entry_res.insert(0, 12)
        entry_volt.insert(0, 20)

    window_open = tk.Tk() # tworzenie okna głównego
    window_open.title( "Load settings" ) # ustawienie tytułu okna głównego
    window_open.resizable(False, False)
    labelFrame_bit = tk.LabelFrame(window_open, text = "Type of variables")
    labelFrame_bit.grid(row = 0, column = 0)
    rb_bitVar = tk.StringVar()
    rb_bit16 = tk.Radiobutton(labelFrame_bit, variable = rb_bitVar, value = "16", text = "16-bit")
    rb_bit32 = tk.Radiobutton(labelFrame_bit, variable = rb_bitVar, value = "32", text = "32-bit")
    rb_bit16.grid(row = 0, column = 0)
    rb_bit32.grid(row = 0, column = 1)

    labelFrame_freq = tk.LabelFrame(window_open, text = "Sampling frequency")
    labelFrame_freq.grid(row = 0, column = 1)
    entry_freq = tk.Entry(labelFrame_freq, width = 5)
    entry_freq.pack()

    labelFrame_res = tk.LabelFrame(window_open, text = "Resolution")
    labelFrame_res.grid(row = 1, column = 0)
    entry_res = tk.Entry(labelFrame_res, width = 5)
    entry_res.pack()

    labelFrame_volt = tk.LabelFrame(window_open, text = "Input voltage")
    labelFrame_volt.grid(row = 1, column = 1) #pack()#fill = "both", expand = "yes"
    entry_volt = tk.Entry(labelFrame_volt, width = 5)
    entry_volt.pack()

    button_default = tk.Button(window_open, text = "Set to default", command = lambda: setToDefault())
    button_default.grid(row=2, column = 0)
    applyButton = tk.Button(window_open, text = "Save and apply", command = lambda: apply())
    applyButton.grid(row=2, column = 1)

    window_open.mainloop() # wywołanie pętli komunikatów

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

def changeAnalyzeSection(arg):
    if arg == "Right":
        container.grid(row=1, column=0, sticky="nsew")
        container2.grid(row=1, column=1, sticky="nsew")

        window.grid_columnconfigure(0, weight=3)
        window.grid_columnconfigure(1, weight=1)
        window.grid_rowconfigure(1, weight=1)
        window.grid_rowconfigure(2, weight=0)
    if arg == "Down":
        container.grid(row=1, column=0, sticky="nsew")
        container2.grid(row=2, column=0, sticky="nsew")

        window.grid_rowconfigure(1, weight = 3)
        window.grid_rowconfigure(2, weight = 1)
        window.grid_columnconfigure(1, weight = 0)
    if arg == "Left":
        container.grid(row=1, column=1, sticky="nsew")
        container2.grid(row=1, column=0, sticky="nsew")

        window.grid_rowconfigure(1, weight=1)
        window.grid_rowconfigure(2, weight=0)
        window.grid_columnconfigure(0, weight=1)
        window.grid_columnconfigure(1, weight=3)
    if arg == "Top":
        container.grid(row=2, column=0, sticky ="nsew")
        container2.grid(row=1, column=0, sticky="nsew")

        window.grid_rowconfigure(1, weight = 1)
        window.grid_rowconfigure(2, weight = 3)
        window.grid_columnconfigure(1, weight = 0)

def changeGraphsShow(arg):
    if arg == "raw":
        None

def filterData():
    #Funkcja wyświetlająca okno filtracji wcześniej wczytanego sygnału
    #Umożliwia dostosowanie przez użytkownika parametrów filtracji
    
    def bandpass_filter(data, lowcut, highcut, signal_freq, filter_order):
        """
        Method responsible for creating and applying Butterworth filter.
        data: raw data
        float lowcut: filter lowcut frequency value
        float highcut: filter highcut frequency value
        int signal_freq: signal frequency in samples per second (Hz)
        int filter_order: filter order
        array: filtered data
        """
        nyquist_freq = 0.5 * signal_freq
        low = lowcut / nyquist_freq
        high = highcut / nyquist_freq
        b, a = scp.signal.butter(filter_order, [low, high], btype="band")
        y = scp.signal.lfilter(b, a, data)
        return y

    def lowpass_filter(data, numtaps, cutoff, signal_freq):
        #filtr dolnoprzepustowy
        nyquist_freq = 0.5 * signal_freq
        cutoff = cutoff / nyquist_freq
        b = signal.firwin(numtaps = numtaps, cutoff = cutoff, nyq = nyquist_freq)
        y = signal.lfilter(b, [1], data)
        return y
    
    def setToDefault():
        entry_lowcut.delete(0, "end")
        entry_signalfreq.delete(0, "end")
        entry_highcut.delete(0, "end")
        entry_order.delete(0, "end")
        entry_numtaps.delete(0, "end")
        entry_cutoff.delete(0, "end")
        
        entry_lowcut.insert(0, 0.05)
        entry_signalfreq.insert(0, 1000)
        entry_highcut.insert(0, 150)
        entry_order.insert(0, 1)
        entry_numtaps.insert(0, 21)
        entry_cutoff.insert(0, 50)

    def apply():
        global y_global
        y_global = bandpass_filter(y_global, float(entry_lowcut.get()), float(entry_highcut.get()), float(entry_signalfreq.get()), float(entry_order.get()))
        y_global = lowpass_filter(y_global, int(entry_numtaps.get()), float(entry_cutoff.get()), float(entry_signalfreq.get()))
        a.clear()
        a.plot(x_global, y_global)
        canvas.draw()

        window_filter.destroy()

    def check():
        window_check = tk.Tk()
        window_check.title("Checking graph")
        fig, axs = plt.subplots(1,1)
        axs.plot(x_global, y_global)
        y = bandpass_filter(y_global, float(entry_lowcut.get()), float(entry_highcut.get()), float(entry_signalfreq.get()), float(entry_order.get()))
        y = lowpass_filter(y_global, int(entry_numtaps.get()), float(entry_cutoff.get()), float(entry_signalfreq.get()))
        axs.plot(x_global, y)
        canvas = FigureCanvasTkAgg(fig, master = window_check)
        canvas.draw()
        canvas.get_tk_widget().pack(side = tk.TOP, fill=tk.BOTH, expand = True)

        toolbar = NavigationToolbar2TkAgg(canvas, window_check)
        toolbar.update()
        canvas._tkcanvas.pack(side = tk.TOP, fill=tk.BOTH, expand = True)
        
    window_filter = tk.Tk() # tworzenie okna głównego
    window_filter.title( "Filtering customization" ) # ustawienie tytułu okna głównego
    window_filter.resizable(False, False)

    #Sekcja parametrów filtra pasmowoprzepustowego*************
    #**********************************************************
    labelFrame_bandpass = tk.LabelFrame(window_filter, text = "Bandpass filter parameters")
    labelFrame_bandpass.grid(row = 0, column = 0, rowspan = 3)

    label_lowcut = Label(labelFrame_bandpass, text = "Lowcut:")
    label_lowcut.grid(row = 0, column = 0)
    entry_lowcut = tk.Entry(labelFrame_bandpass, width = 5)
    entry_lowcut.grid(row = 0, column = 1)
    #**********************************************************
    label_signalfreq = Label(labelFrame_bandpass, text = "Signal frequency:")
    label_signalfreq.grid(row = 0, column = 2)
    entry_signalfreq = tk.Entry(labelFrame_bandpass, width = 5)
    entry_signalfreq.grid(row = 0, column = 3)
    #**********************************************************
    label_highcut = Label(labelFrame_bandpass, text = "Highcut:")
    label_highcut.grid(row = 1, column = 0)
    entry_highcut = tk.Entry(labelFrame_bandpass, width = 5)
    entry_highcut.grid(row = 1, column = 1)
    #**********************************************************
    label_order = Label(labelFrame_bandpass, text = "Filter order:")
    label_order.grid(row = 1, column = 2)
    entry_order = tk.Entry(labelFrame_bandpass, width = 5)
    entry_order.grid(row = 1, column = 3)
    
    #Sekcja parametrów filtra dolnoprzepustowego***************
    #**********************************************************
    labelFrame_lowpass = tk.LabelFrame(window_filter, text = "Lowpass filter parameters")
    labelFrame_lowpass.grid(row = 4, column = 0, rowspan = 3)
    
    label_numtaps = Label(labelFrame_lowpass, text = "Numtaps:")
    label_numtaps.grid(row = 0, column = 0)
    entry_numtaps = tk.Entry(labelFrame_lowpass, width = 5)
    entry_numtaps.grid(row = 0, column = 1)
    #**********************************************************
    label_cutoff = Label(labelFrame_lowpass, text = "Cutoff:")
    label_cutoff.grid(row = 0, column = 2)
    entry_cutoff = tk.Entry(labelFrame_lowpass, width = 5)
    entry_cutoff.grid(row = 0, column = 3)
    
    #Sekcja przycisków*****************************************
    #**********************************************************
    button_check = tk.Button(window_filter, text = "Check", command = lambda: check())
    button_check.grid(row=1, column = 1)
    button_apply = tk.Button(window_filter, text = "Apply", command = lambda: apply())
    button_apply.grid(row=2, column = 1)
    button_default = tk.Button(window_filter, text = "Set to default", command = lambda: setToDefault())
    button_default.grid(row=6, column = 1)

    window_filter.mainloop()
    
    
    
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

numberofwindowsMenu.add_checkbutton(label = "Raw")
numberofwindowsMenu.add_checkbutton(label = "Filtered")
numberofwindowsMenu.add_checkbutton(label = "Analyzed")

analyzesectionMenu.add_radiobutton(label = "Right", command = lambda: changeAnalyzeSection("Right"))
analyzesectionMenu.add_radiobutton(label = "Left", command = lambda: changeAnalyzeSection("Left"))
analyzesectionMenu.add_radiobutton(label = "Top", command = lambda: changeAnalyzeSection("Top"))
analyzesectionMenu.add_radiobutton(label = "Down", command = lambda: changeAnalyzeSection("Down"))


menubar.add_cascade(label = "Options", menu = optionsmenu)
optionsmenu.add_cascade(label = "Configure window", menu = windowmenu)
windowmenu.add_cascade(label = "Displaying charts", menu = numberofwindowsMenu)
windowmenu.add_cascade(label = "Analyze section", menu = analyzesectionMenu)
        
#Tworzenie części paska "ECG analysis"
ecgmenu = tk.Menu(menubar, tearoff = 0)
ecgmenu.add_command(label = "Filter",
                                command = lambda: filterData())
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

labelFrame1 = tk.LabelFrame(toolbar, text = "File", labelanchor = "s")
labelFrame1.grid(row = 0, column = 0)
open_img = Image.open("open_icon.png")
open_eimg = ImageTk.PhotoImage(open_img)

openButton = tk.Button(labelFrame1, image=open_eimg, relief=FLAT,
                    command = lambda: browseFiles())
openButton.image = open_eimg
openButton.pack(side=LEFT, padx=2, pady=2)
#openButton.grid(row = 0, column = 0)


save_img = Image.open("save_icon.png")
save_eimg = ImageTk.PhotoImage(save_img)

saveButton = tk.Button(labelFrame1, image=save_eimg, relief=FLAT,
                    command = lambda: saveFiles())
saveButton.image = save_eimg
saveButton.pack(side=LEFT, padx=2, pady=2)
#saveButton.grid(row = 0, column = 1)

labelFrame2 = tk.LabelFrame(toolbar, text = "Analysis", labelanchor = "s")
labelFrame2.grid(row = 0, column = 1)
filter_img = Image.open("filter_icon.png")
filter_eimg = ImageTk.PhotoImage(filter_img)

filterButton = tk.Button(labelFrame2, image=filter_eimg, relief=FLAT,
                    command = lambda: filterData())
filterButton.image = filter_eimg
filterButton.pack(side=LEFT, padx=2, pady=2)
#filterButton.grid(row = 0, column = 0)


analysis_img = Image.open("analysis_icon.png")
analysis_eimg = ImageTk.PhotoImage(analysis_img)

analysisButton = tk.Button(labelFrame2, image=analysis_eimg, relief=FLAT,
                    command = lambda: analysisFiles())
analysisButton.image = analysis_eimg
analysisButton.pack(side=LEFT, padx=2, pady=2)
#analysisButton.grid(row = 0, column = 1)


labelFrame3 = tk.LabelFrame(toolbar, text = "Help", labelanchor = "s")
labelFrame3.grid(row = 0, column = 2)
help_img = Image.open("help_icon.png")
help_eimg = ImageTk.PhotoImage(help_img)

helpButton = tk.Button(labelFrame3, image=help_eimg, relief=FLAT,
                    command = lambda: helpFiles())
helpButton.image = help_eimg
helpButton.pack(padx=2, pady=2)


toolbar.grid(row = 0, column = 0, columnspan = 2, sticky = "nsew")
        
#Zatwierdzenie menu
window.config(menu = menubar)


container = tk.Frame()
container2 = tk.Frame()
changeAnalyzeSection("Right")


var = StringVar()
label = Label( container2, textvariable=var)

var.set("ECG analysis")
label.pack()

#f = Figure() #Tworzymy obiekt Figure
#figsize to wielkość tworzonej przestrzeni na wykres
#(szerokość, wysokość) w calach, dpi to piksele na cal.
fig, axs = plt.subplots(1,1)
a = axs
canvas = FigureCanvasTkAgg(fig, master = container)
canvas.draw()
canvas.get_tk_widget().pack(side = tk.TOP, fill=tk.BOTH, expand = True)

toolbar = NavigationToolbar2TkAgg(canvas, container)
toolbar.update()
canvas._tkcanvas.pack(side = tk.TOP, fill=tk.BOTH, expand = True)

window.mainloop()
