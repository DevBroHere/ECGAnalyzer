import tkinter as tk
from tkinter import ttk
import sys
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
import numpy as np
import scipy as scp
from scipy import signal
import neurokit2 as nk
import math
from PIL import Image, ImageTk

##print(style.available) #Wyświetlanie możliwych styli
style.use("bmh") #Wybranie danego stylu wyświetlania wykresów

#Globalne dane ekg (bieżące)
x_global = None
y_global = None

#Wybrany obszar analizy
analysisArea = []

def popupmsg(msg):
    popup = tk.Tk()
    
    popup.wm_title("!")
    label = ttk.Label(popup, text = msg, font = ("VERDANA", 10))
    label.pack(side = "top", fill = "x", pady = 10)
    B1 = ttk.Button(popup, text = "Okay", command = popup.destroy)
    B1.pack()
    popup.mainloop()
    
def loadDataOptions():
    
    def apply():
        global x_global, y_global
        if rb_bitVar.get() == 16:
            ekgfile = np.fromfile(filename, dtype = np.int16)
        elif rb_bitVar.get() == 32:
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
        plt.xlabel('time [s]')
        plt.ylabel('voltage [mV]')
        canvas.draw()

        window_open.destroy()

    def setToDefault():
        entry_freq.delete(0, "end")
        entry_res.delete(0, "end")
        entry_volt.delete(0, "end")
        
        rb_bitVar.set(16)
        entry_freq.insert(0, 1000)
        entry_res.insert(0, 12)
        entry_volt.insert(0, 20)

    def setVariable(var):
        rb_bitVar.set(var)

    window_open = tk.Tk() # tworzenie okna głównego
    window_open.title( "Load settings" ) # ustawienie tytułu okna głównego
    window_open.resizable(False, False)
    labelFrame_bit = tk.LabelFrame(window_open, text = "Type of variables")
    labelFrame_bit.grid(row = 0, column = 0)
    rb_bitVar = IntVar()
    rb_bit16 = tk.Radiobutton(labelFrame_bit, variable = rb_bitVar, value = 16, text = "16-bit", command = lambda: setVariable(16))
    rb_bit32 = tk.Radiobutton(labelFrame_bit, variable = rb_bitVar, value = 32, text = "32-bit", command = lambda: setVariable(32))
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
            defaultextension='.png', title="Window")
    if a:
        plt.savefig(a)
        
    
def savetxt():
    f = filedialog.asksaveasfile(mode='w', defaultextension=".txt")
    if f is None: # asksaveasfile return `None` if dialog closed with "cancel".
        return
    text = textbox.get("1.0","end-1c")
    f.write(text)
    f.close()

def changeAnalyzeSection(arg):
    global container, frame_Analysis
    if arg == "Top":
        container.grid(row=2, column=0, sticky="nsew")
        frame_Analysis.grid(row=1, column=0)

        window.grid_rowconfigure(1, weight=1)
        window.grid_rowconfigure(2, weight=3)
        window.grid_columnconfigure(0, weight=1)
        window.grid_columnconfigure(1, weight=0)
    if arg == "Down":
        container.grid(row = 1, column = 0, sticky = "nsew")
        frame_Analysis.grid(row = 2, column = 0)

        window.grid_rowconfigure(1, weight=1)
        window.grid_rowconfigure(2, weight=3)
        window.grid_columnconfigure(0, weight=1)
        window.grid_columnconfigure(1, weight=0)

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
        plt.xlabel('time [s]')
        plt.ylabel('voltage [mV]')
        canvas.draw()

        window_filter.destroy()

    def check():
        figure, axis = plt.subplots(1,1)
        x = x_global
        y = y_global
        axis.plot(x, y)
        y = bandpass_filter(y, float(entry_lowcut.get()), float(entry_highcut.get()), float(entry_signalfreq.get()), float(entry_order.get()))
        y = lowpass_filter(y, int(entry_numtaps.get()), float(entry_cutoff.get()), float(entry_signalfreq.get()))
        axis.plot(x, y)
        plt.xlabel('time [s]')
        plt.ylabel('voltage [mV]')
        figure.show()
        
        
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
    button_check = ttk.Button(window_filter, text = "Check", command = lambda: check())
    button_check.grid(row=1, column = 1)
    button_apply = ttk.Button(window_filter, text = "Apply", command = lambda: apply())
    button_apply.grid(row=2, column = 1)
    button_default = ttk.Button(window_filter, text = "Set to default", command = lambda: setToDefault())
    button_default.grid(row=5, column = 1)

    window_filter.mainloop()

def autofilterData():
    #Funkcja realizuje okno autofiltracji

    def apply(sampling_rate):
        global x_global, y_global
        ecg = []
        ecg.append(x_global)
        ecg.append(y_global)
        window_autofilter.destroy()
        ecg[1] = nk.ecg_clean(ecg[1], sampling_rate = sampling_rate)
        x_global = ecg[0]
        y_global = ecg[1]
        a.clear()
        a.plot(ecg[0], ecg[1])
        plt.xlabel('time [s]')
        plt.ylabel('voltage [mV]')
        canvas.draw()
        
        
    window_autofilter = tk.Tk() # tworzenie okna głównego
    window_autofilter.title( "Automatic filtering" ) # ustawienie tytułu okna głównego
    window_autofilter.resizable(False, False)

    label_signalfreq = Label(window_autofilter, text = "Signal frequency:")
    label_signalfreq.grid(row = 0, column = 0)
    entry_signalfreq = tk.Entry(window_autofilter)
    entry_signalfreq.grid(row = 0, column = 1)

    button_apply = ttk.Button(window_autofilter, text = "Apply",
                              command = lambda: apply(float(entry_signalfreq.get())))
    button_apply.grid(row=1, column = 0, columnspan = 2)

def setAnalysisArea():
    #Funkca realizuje okno umożliwiające wybranie obszaru przeznaczonego do analizy
    def clear():
        #a.axvspan(x_global[0], x_global[len(x_global)-1], color='white', alpha=1)
        a.clear()
        a.plot(x_global, y_global)
        canvas.draw()
        analysisArea.clear()
    def apply():
        global analysisArea
        a.axvspan(x_global[0], x_global[len(x_global)-1], color='white', alpha=1)
        a.axvspan(float(entry_timefrom.get()), float(entry_timeto.get()), color='red', alpha=0.3)
        analysisArea.append(float(entry_timefrom.get()))
        analysisArea.append(float(entry_timeto.get()))
        window_area.destroy()
        canvas.draw()
        
    window_area = tk.Tk()
    window_area.title( "Analysis area" )
    window_area.resizable(False, False)

    labelFrame_time = tk.LabelFrame(window_area, text = "Select a time period [in sec]")
    labelFrame_time.grid(row = 0, column = 0, columnspan = 2)
    label_timefrom = Label(labelFrame_time, text = "From: ")
    label_timefrom.grid(row = 0, column = 0)
    entry_timefrom = tk.Entry(labelFrame_time)
    entry_timefrom.grid(row = 0, column = 1)
    label_timeto = Label(labelFrame_time, text = "To: ")
    label_timeto.grid(row = 0, column = 2)
    entry_timeto = tk.Entry(labelFrame_time)
    entry_timeto.grid(row = 0, column = 3)

    button_clear = ttk.Button(window_area, text = "Clear", command = lambda: clear())
    button_clear.grid(row = 1, column = 0)
    button_apply = ttk.Button(window_area, text = "Apply", command = lambda: apply())
    button_apply.grid(row = 1, column = 1)
    

def analyzeData():
    #Funkcja realizuje okno analizy oraz związane z nim operacje
    
    def calculateTime(list_offsets, list_onsets):
        list_time = []
        minimum = 0
        if len(list_offsets) != len(list_onsets):
            minimum = min(len(list_offsets), len(list_onsets))
        else:
            minimum = len(list_offsets)
        for i in range(minimum):
            if list_offsets[i] - list_onsets[i] < 0:
                if i + 1 >= minimum:
                    break
                list_time.append(list_offsets[i+1] - list_onsets[i])
            else:
                list_time.append(list_offsets[i] - list_onsets[i])
        time = np.quantile(list_time, 0.5)
        return time

    def analyzeECG(ecg, sampling_rate, method = "dwt"):
        #Funkcja zwraca parametry analizy, które mogą być wykorzystane do wyświetlania oraz do dalszej analizy.
        #Zwraca puls, średnią HRV, HRVSDNN, HRVRMSSD, informacje związane z załamkami (długość, czas, amplituda)
        a, peaks = nk.ecg_process(ecg[1], sampling_rate = sampling_rate)
        info = nk.ecg_analyze(a, sampling_rate = sampling_rate)
        ECG_Rate_Mean = info["ECG_Rate_Mean"][0]
        HRV_RMSSD = info["HRV_RMSSD"][0]
        HRV_MeanNN = info["HRV_MeanNN"][0]
        HRV_SDNN = info["HRV_SDNN"][0]

        _,rpeaksnk = nk.ecg_peaks(ecg[1], sampling_rate = sampling_rate)
        R_peaks = [[],[]]
        for i in rpeaksnk["ECG_R_Peaks"]:
            R_peaks[0].append(ecg[0][i])
            R_peaks[1].append(ecg[1][i])

        # Delineate the ECG signal
        _, waves_peak = nk.ecg_delineate(ecg[1], rpeaksnk, sampling_rate = sampling_rate, show = False,
                                         show_type = "peaks")
        if method == "cwt":
            _, waves_other = nk.ecg_delineate(ecg[1], rpeaksnk, sampling_rate = sampling_rate,
                                            method="cwt", show=False, show_type='all')
        if method == "dwt":
            _, waves_other = nk.ecg_delineate(ecg[1], rpeaksnk, sampling_rate = sampling_rate,
                                            method="dwt", show=False, show_type='all')

        #Wyznaczanie załamków P, Q, S, T
        P_peaks = [[],[]]
        Q_peaks = [[],[]]
        S_peaks = [[],[]]
        T_peaks = [[],[]]
        for name in waves_peak:
            for i in waves_peak[str(name)]:
                if math.isnan(i):
                    continue
                if str(name) == "ECG_P_Peaks":
                    P_peaks[0].append(ecg[0][i])
                    P_peaks[1].append(ecg[1][i])
                if str(name) == "ECG_Q_Peaks":
                    Q_peaks[0].append(ecg[0][i])
                    Q_peaks[1].append(ecg[1][i])
                if str(name) == "ECG_S_Peaks":
                    S_peaks[0].append(ecg[0][i])
                    S_peaks[1].append(ecg[1][i])
                if str(name) == "ECG_T_Peaks":
                    T_peaks[0].append(ecg[0][i])
                    T_peaks[1].append(ecg[1][i])

        #Wyznaczanie początków i końców załamków P, Q, S, T
        P_onsets = [[],[]]
        P_offsets = [[],[]]
        R_onsets = [[],[]]
        R_offsets = [[],[]]
        T_onsets = [[],[]]
        T_offsets = [[],[]]

        for name in waves_other:
            for i in waves_other[str(name)]:
                if math.isnan(i):
                    continue
                if str(name) == "ECG_P_Onsets":
                    P_onsets[0].append(ecg[0][i])
                    P_onsets[1].append(ecg[1][i])
                if str(name) == "ECG_P_Offsets":
                    P_offsets[0].append(ecg[0][i])
                    P_offsets[1].append(ecg[1][i])
                if str(name) == "ECG_R_Onsets":
                    R_onsets[0].append(ecg[0][i])
                    R_onsets[1].append(ecg[1][i])
                if str(name) == "ECG_R_Offsets":
                    R_offsets[0].append(ecg[0][i])
                    R_offsets[1].append(ecg[1][i])
                if str(name) == "ECG_T_Onsets":
                    T_onsets[0].append(ecg[0][i])
                    T_onsets[1].append(ecg[1][i])
                if str(name) == "ECG_T_Offsets":
                    T_offsets[0].append(ecg[0][i])
                    T_offsets[1].append(ecg[1][i])

        #Czasy załamków
        P_Time = calculateTime(P_offsets[0], P_onsets[0])
        QRS_Time = calculateTime(R_offsets[0], R_onsets[0])
        T_Time = calculateTime(T_offsets[0], T_onsets[0])

        #Amplitudy załamków
        P_Amplitude = np.mean(P_peaks[1])
        Q_Amplitude = np.mean(Q_peaks[1])
        R_Amplitude = np.mean(R_peaks[1])
        S_Amplitude = np.mean(S_peaks[1])
        T_Amplitude = np.mean(T_peaks[1])

        #Odstępy
        PQ_Space = calculateTime(R_onsets[0], P_onsets[0])
        QT_Space = calculateTime(T_offsets[0], R_onsets[0])

        #Odcinki
        PQ_Segment = calculateTime(R_onsets[0], P_offsets[0])
        ST_Segment = calculateTime(T_onsets[0], R_offsets[0])

        #Słowniki z pozyskanymi informacjami
        data = {}
        info = {}

        data["P_peaks"] = P_peaks
        data["Q_peaks"] = Q_peaks
        data["R_peaks"] = R_peaks
        data["S_peaks"] = S_peaks
        data["T_peaks"] = T_peaks
        data["P_onsets"] = P_onsets
        data["P_offsets"] = P_offsets
        data["R_onsets"] = R_onsets
        data["R_offsets"] = R_offsets
        data["T_onsets"] = T_onsets
        data["T_offsets"] = T_offsets

        info["ECG_Rate_Mean"] = round(ECG_Rate_Mean, 4)
        info["HRV_MeanNN"] = round(HRV_MeanNN, 4)
        info["HRV_RMSSD"] = round(HRV_RMSSD, 4)
        info["HRV_SDNN"] = round(HRV_SDNN, 4)
        info["P_Time"] = round(P_Time, 4)
        info["QRS_Time"] = round(QRS_Time, 4)
        info["T_Time"] = round(T_Time, 4)
        info["P_Amplitude"] = round(P_Amplitude, 4)
        info["Q_Amplitude"] = round(Q_Amplitude, 4)
        info["R_Amplitude"] = round(R_Amplitude, 4)
        info["S_Amplitude"] = round(S_Amplitude, 4)
        info["T_Amplitude"] = round(T_Amplitude, 4)
        info["PQ_Space"] = round(PQ_Space, 4)
        info["QT_Space"] = round(QT_Space, 4)
        info["PQ_Segment"] = round(PQ_Segment, 4)
        info["ST_Segment"] = round(ST_Segment, 4)

        return data, info

    def showData(ecg, data, sampling_rate):
        #Funkcja umożliwiająca wyświetlenie przeanalizowanych danych
        
        a.clear()
        a.plot(ecg[0], ecg[1])
        a.plot(data["R_peaks"][0], data["R_peaks"][1], "ro", label = "R peaks")
        a.plot(data["P_peaks"][0], data["P_peaks"][1], "bv", label = "P peaks")
        a.plot(data["Q_peaks"][0], data["Q_peaks"][1], "kv", label = "Q peaks")
        a.plot(data["S_peaks"][0], data["S_peaks"][1], "wv", label = "S peaks")
        a.plot(data["T_peaks"][0], data["T_peaks"][1], "yv", label = "T peaks")
        a.plot(data["P_onsets"][0], data["P_onsets"][1], "b^", label = "P onsets")
        a.plot(data["P_offsets"][0], data["P_offsets"][1], "b^", label = "P offsets")
        a.plot(data["R_onsets"][0], data["R_onsets"][1], "r^", label = "R onsets")
        a.plot(data["R_offsets"][0], data["R_offsets"][1], "r^", label = "R offsets")
        a.plot(data["T_onsets"][0], data["T_onsets"][1], "y^", label = "T onsets")
        a.plot(data["T_offsets"][0], data["T_offsets"][1], "y^", label = "T offsets")
        plt.xlabel('time [s]')
        plt.ylabel('voltage [mV]')
        plt.legend()
        canvas.draw()

        hrv_time = nk.hrv_time(data["R_peaks"][1], sampling_rate=sampling_rate, show=True)
        hrv_non = nk.hrv_nonlinear(data["R_peaks"][1], sampling_rate=sampling_rate, show=True)

        plt.figure(2).show()
        plt.figure(3).show()

    def diagnoseECG(info):
        #Analiza pulsu
        textbox.delete(1.0, END)
        list_diseases = []
        for key, name in info.items():
            textbox.insert(tk.END, "{0}:{1}".format(key,name))
            textbox.insert(tk.END, "\n")
            
        if info["ECG_Rate_Mean"] < 60:
            textbox.insert(tk.END, "Częstotliwość pracy serca poniżej normy")
            list_diseases.append("Arytmia (Bradykardia)")
            textbox.insert(tk.END, "\n")
        elif info["ECG_Rate_Mean"] > 100:
            textbox.insert(tk.END, "Częstotliwość pracy serca powyżej normy")
            list_diseases.append("Arytmia (Tachykardia)")
            textbox.insert(tk.END, "\n")
        elif info["ECG_Rate_Mean"] >= 60 and info["ECG_Rate_Mean"] <= 100:
            textbox.insert(tk.END, "Częstotliwość pracy serca w normie")
            textbox.insert(tk.END, "\n")
            
        #Analiza współczynników HRV
        if info["HRV_MeanNN"] < 750:
            textbox.insert(tk.END, "Średni odstęp RR nieprawidłowy")
            textbox.insert(tk.END, "\n")
        elif info["HRV_MeanNN"] > 750:
            textbox.insert(tk.END, "Średni odstęp RR w normie")
            textbox.insert(tk.END, "\n")
        if info["HRV_RMSSD"] > 39 or info["HRV_RMSSD"] < 15:
            textbox.insert(tk.END, "Współczynnik HRV rMSSD nie mieści się w normie")
            textbox.insert(tk.END, "\n")
        elif info["HRV_RMSSD"] <= 39 and info["HRV_RMSSD"] >= 15:
            textbox.insert(tk.END, "Współczynnik HRV rMSSD mieści się w normie")
            textbox.insert(tk.END, "\n")
        if info["HRV_SDNN"] < 102 or info["HRV_SDNN"] > 180:
            textbox.insert(tk.END, "Współczynnik HRV SDNN nie mieści się w normie")
            textbox.insert(tk.END, "\n")
            if info["HRV_SDNN"] < 73:
                list_diseases.append("Jedno z powikłań typu: kardiomiopatia przerostowa; kardiomiopatia rozstrzeniowa; zapalenie mięśnia sercowego")
                textbox.insert(tk.END, "\n")
            if info["HRV_SDNN"] > 73 and info["HRV_SDNN"] < 102:
                list_diseases.append("Podejrzenie wady aortalnej")
                textbox.insert(tk.END, "\n")
        elif info["HRV_SDNN"] >= 102 or info["HRV_SDNN"] <= 180:
            textbox.insert(tk.END, "Współczynnik HRV SDNN w normie")
            textbox.insert(tk.END, "\n")
        #Analiza czasu trwania załamków
        if info["P_Time"] < 0.08:
            textbox.insert(tk.END, "Czas trwania załamka P nie mieści się zakresie normy (poniżej normy)")
            textbox.insert(tk.END, "\n")
            
            if info["P_Time"] > 0.12:
                textbox.insert(tk.END, "Czas trwania załamka P nie mieści się zakresie normy (powyżej normy)")
                list_diseases.append("Podejrzenie powiększenia lewego przedsionka lub zaburzeń przewodzenia śródprzedsionkowego")
                textbox.insert(tk.END, "\n")
                
        elif info["P_Time"] >= 0.08 and info["P_Time"] <= 0.12:
            textbox.insert(tk.END, "Czas załamka P w normie")
            textbox.insert(tk.END, "\n")
            
        if info["QRS_Time"] < 0.06:
            textbox.insert(tk.END, "Czas trwania zespołu QRS nie mieści się w zakresie normy (poniżej normy)")
            textbox.insert(tk.END, "\n")
        elif info["QRS_Time"] > 0.1:
            textbox.insert(tk.END, "Czas trwania zespołu QRS nie mieści się w zakresie normy (powyżej normy)")
            list_diseases.append("Podejrzenie przerostu komory")
            textbox.insert(tk.END, "\n")
        elif info["QRS_Time"] >= 0.06 and info["QRS_Time"] <= 0.1:
            textbox.insert(tk.END, "Czas zespołu QRS w normie")
            textbox.insert(tk.END, "\n")
        if abs(info["Q_Amplitude"]) > info["R_Amplitude"]/4:
            textbox.insert(tk.END, "Nieprawidłowa proporcja między załamkiem Q a załamkiem R")
            list_diseases.append("Podejrzenie zawału serca")
            textbox.insert(tk.END, "\n")
            
        if info["PQ_Segment"] < 0.04:
            textbox.insert(tk.END, "Czas trwania odcinka PQ nie mieści się w normie (poniżej normy)")
            textbox.insert(tk.END, "\n")
        elif info["PQ_Segment"] > 0.1:
            textbox.insert(tk.END, "Czas trwania odcinka PQ nie mieści się w normie (powyżej normy)")
            textbox.insert(tk.END, "\n")
        elif info["PQ_Segment"] >= 0.04 or info["PQ_Segment"] <= 0.1:
            textbox.insert(tk.END, "Czas trwania odcinka PQ mieści się w normie")
            textbox.insert(tk.END, "\n")
            
        if info["PQ_Space"] < 0.12:
            textbox.insert(tk.END, "Czas trwania odstępu PQ nie mieści się w normie (poniżej normy)")
            textbox.insert(tk.END, "\n")
        elif info["PQ_Space"] > 0.2:
            textbox.insert(tk.END, "Czas trwania odstępu PQ nie mieści się w normie (powyżej normy)")
            textbox.insert(tk.END, "\n")
        elif info["PQ_Space"] >= 0.12 and info["PQ_Space"] <= 0.2:
            textbox.insert(tk.END, "Czas trwania odstępu PQ mieści się w normie")
            textbox.insert(tk.END, "\n")
            
        if info["ST_Segment"] < 0.06:
            textbox.insert(tk.END, "Czas trwania odcinka ST nie mieści się w normie (poniżej normy)")
            textbox.insert(tk.END, "\n")
        elif info["ST_Segment"] > 0.1:
            textbox.insert(tk.END, "Czas trwania odcinka ST nie mieści się w normie (powyżej normy)")
            textbox.insert(tk.END, "\n")
        elif info["ST_Segment"] >= 0.06 and info["ST_Segment"] <= 0.1:
            textbox.insert(tk.END, "Czas trwania odcinka ST mieści się w normie")
            textbox.insert(tk.END, "\n")
            
        if info["T_Time"] < 0.12:
            textbox.insert(tk.END, "Czas trwamia załamka T nie mieści się w normie (poniżej normy)")
            textbox.insert(tk.END, "\n")
        if info["T_Time"] > 0.16:
            textbox.insert(tk.END, "Czas trwamia załamka T nie mieści się w normie (powyżej normy)")
            textbox.insert(tk.END, "\n")
        if info["T_Time"] >= 0.12 and info["T_Time"] <= 0.16:
            textbox.insert(tk.END, "Czas trwania załamka T w normie")
            textbox.insert(tk.END, "\n")
            
        if info["QT_Space"]/(info["HRV_MeanNN"]/1000) > 0.455:
            list_diseases.append("Podejrzenie zespołu długiego QT")
            textbox.insert(tk.END, "Odstęp QT powyżej normy")
            textbox.insert(tk.END, "\n")
        if info["QT_Space"]/(info["HRV_MeanNN"]/1000) < 0.33:
            textbox.insert(tk.END, "Odstęp QT poniżej normy")
            list_diseases.append("Podejrzenie jednej z chorób: hiperkaliemia; hiperkalcemia; zespół krótkiego QT")
            textbox.insert(tk.END, "\n")
        if info["QT_Space"]/(info["HRV_MeanNN"]/1000) >= 0.33 and info["QT_Space"]/(info["HRV_MeanNN"]/1000) <= 0.455:
            textbox.insert(tk.END, "Odstęp QT w normie")
            textbox.insert(tk.END, "\n")
            
        textbox.insert(tk.END, "Podsumowanie: ")
        if list_diseases:
            for i in list_diseases:
                textbox.insert(tk.END, i + "; ")
        else:
            textbox.insert(tk.END, "Brak przypuszczeń, pacjent potencjalnie zdrowy")

    def apply(sampling_rate, method):
        global x_global, y_global
        ecg = []
        ecg.append(x_global)
        ecg.append(y_global)
        if method == "Continuous Wavelet Method (CWT)":
            method = "cwt"
        if method == "Discrete Wavelet Method (DWT)":
            method = "dwt"
        window_analyze.destroy()
        if not analysisArea:
            tk.messagebox.showinfo(title = "Information", message = "First, mark the area of ​​analysis.")
        else:
            temporaryecg = []
            temporaryecg.append(x_global[int(analysisArea[0] * float(sampling_rate)) : int(analysisArea[1] * float(sampling_rate))])
            temporaryecg.append(y_global[int(analysisArea[0] * float(sampling_rate)) : int(analysisArea[1] * float(sampling_rate))])
            data, info = analyzeECG(temporaryecg, float(sampling_rate), method)
            diagnoseECG(info)
            showData(temporaryecg, data, float(sampling_rate))
            x_global = ecg[0]
            y_global = ecg[1]
        

        
    

    window_analyze = tk.Tk() # tworzenie okna głównego
    window_analyze.title( "Analysis window" ) # ustawienie tytułu okna głównego
    window_analyze.resizable(False, False)

    label_Rate = Label(window_analyze, text = "Sampling rate: ")
    label_Rate.grid(row = 0, column = 0)
    entry_Rate = tk.Entry(window_analyze)
    entry_Rate.grid(row = 0, column = 1)

    label_Method = Label(window_analyze, text = "Analyze method: ")
    label_Method.grid(row = 1, column = 0)
    combobox_Value = tk.StringVar()
    combobox_Method = ttk.Combobox(window_analyze, width = 33, justify = "center", 
                                   textvariable = combobox_Value)
    combobox_Method.grid(row = 1, column = 1)
    combobox_Method["values"] = ("Continuous Wavelet Method (CWT)", "Discrete Wavelet Method (DWT)")
    combobox_Method.current(0)

    button_apply = ttk.Button(window_analyze, text = "Apply",
                              command = lambda: apply(entry_Rate.get(),
                                                      combobox_Method.get()))
    button_apply.grid(row=2, column = 0, columnspan = 2)

    window_analyze.mainloop()

def exitprogram():
    window.destroy()
    sys.exit()
    
    
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
                             command = lambda: exitprogram())
menubar.add_cascade(label = "File", menu = filemenu)
        
#Tworzenie części paska "Options"
optionsmenu = tk.Menu(menubar, tearoff = 0)
windowmenu = tk.Menu(optionsmenu, tearoff = 0)
analyzesectionMenu = tk.Menu(windowmenu, tearoff = 0)

optionsmenu.add_command(label = "Graph customization",
                                command = lambda: popupmsg("Not supported yet"))

analyzesectionMenu.add_radiobutton(label = "Top", command = lambda: changeAnalyzeSection("Top"))
analyzesectionMenu.add_radiobutton(label = "Down", command = lambda: changeAnalyzeSection("Down"))


menubar.add_cascade(label = "Options", menu = optionsmenu)
optionsmenu.add_cascade(label = "Configure window", menu = windowmenu)
windowmenu.add_cascade(label = "Analyze section", menu = analyzesectionMenu)
        
#Tworzenie części paska "ECG analysis"
ecgmenu = tk.Menu(menubar, tearoff = 0)
ecgmenu.add_command(label = "Filtering",
                                command = lambda: filterData())
ecgmenu.add_command(label = "Auto filtering",
                                command = lambda: autofilterData())
ecgmenu.add_command(label = "Analysis area",
                                command = lambda: setAnalysisArea())
ecgmenu.add_command(label = "Analysis",
                                command = lambda: analyzeData())
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

autofilter_img = Image.open("autofilter_icon.png")
autofilter_eimg = ImageTk.PhotoImage(autofilter_img)

autofilterButton = tk.Button(labelFrame2, image=autofilter_eimg, relief=FLAT,
                    command = lambda: autofilterData())
autofilterButton.image = autofilter_eimg
autofilterButton.pack(side=LEFT, padx=2, pady=2)


analysisarea_img = Image.open("analysisarea_icon.png")
analysisarea_eimg = ImageTk.PhotoImage(analysisarea_img)

analysisareaButton = tk.Button(labelFrame2, image=analysisarea_eimg, relief=FLAT,
                    command = lambda: setAnalysisArea())
analysisareaButton.image = analysisarea_eimg
analysisareaButton.pack(side=LEFT, padx=2, pady=2)


analysis_img = Image.open("analysis_icon.png")
analysis_eimg = ImageTk.PhotoImage(analysis_img)

analysisButton = tk.Button(labelFrame2, image=analysis_eimg, relief=FLAT,
                    command = lambda: analyzeData())
analysisButton.image = analysis_eimg
analysisButton.pack(side=LEFT, padx=2, pady=2)
#analysisButton.grid(row = 0, column = 1)


labelFrame3 = tk.LabelFrame(toolbar, text = "Help", labelanchor = "s")
labelFrame3.grid(row = 0, column = 2)
help_img = Image.open("help_icon.png")
help_eimg = ImageTk.PhotoImage(help_img)

helpButton = tk.Button(labelFrame3, image=help_eimg, relief=FLAT,
                    command = lambda: popupmsg("Not supported yet"))
helpButton.image = help_eimg
helpButton.pack(padx=2, pady=2)


toolbar.grid(row = 0, column = 0, columnspan = 2, sticky = "nsew")
        
#Zatwierdzenie menu
window.config(menu = menubar)

container = tk.Frame(window)

frame_Analysis = tk.Frame(window)
#frame_Analysis.grid_propagate(False)

var = StringVar()
label = Label(frame_Analysis, textvariable=var)
var.set("ECG analysis")
label.grid(row = 0, column = 0)

sb_textbox = tk.Scrollbar(frame_Analysis)
textbox = tk.Text(frame_Analysis, width = 150, height = 10, yscrollcommand = sb_textbox.set)
textbox.grid(row = 1, column = 0)
sb_textbox.grid(row = 1, column = 1, sticky = "ns")

sb_textbox.config(command = textbox.yview)
        
button_savetxt = ttk.Button(frame_Analysis, text = "Save",
                              command = lambda: savetxt())
button_savetxt.grid(row=2, column = 0)


changeAnalyzeSection("Down")

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

