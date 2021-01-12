import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
import scipy as scp
import neurokit2 as nk
import math
plt.rcParams['figure.figsize'] = [8, 5]  # Bigger images

def loadData(data, frequency, bit, resolution):
    ekgfile = np.fromfile(data, dtype = np.int16)
    x = []
    y = []
    time = 0
    for row in ekgfile:
        y.append(row)
        x.append(time)
        time += 1/frequency
    b = (2**bit) - 1
    for i in range(len(y)):
        y[i] = y[i] * (resolution/b)

    return x, y

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

#algorytm wyznaczania pulsu
def getPulse(zalamkiR_x):
    L = []
    Lp = []
    for i in range(len(zalamkiR_x)):
        if i + 1 <= len(zalamkiR_x) - 1:
            L.append(zalamkiR_x[i+1] - zalamkiR_x[i])
    for i in L:
        Lp.append(60/i)
    pulse = round(np.mean(Lp))
    return pulse

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
    R_Amplitude = np.mean(R_peaks[1])
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
    info["R_Amplitude"] = round(R_Amplitude, 4)
    info["T_Amplitude"] = round(T_Amplitude, 4)
    info["PQ_Space"] = round(PQ_Space, 4)
    info["QT_Space"] = round(QT_Space, 4)
    info["PQ_Segment"] = round(PQ_Segment, 4)
    info["ST_Segment"] = round(ST_Segment, 4)

    for key, name in info.items():
        print(key, ":", name)

    return data, info

def showData(ecg, data, sampling_rate):
    #Funkcja umożliwiająca wyświetlenie przeanalizowanych danych
    fig, axs = plt.subplots(2,2)
    axs[0][0].plot(ecg[0], ecg[1])

    axs[1][0].plot(ecg[0], ecg[1])
    axs[1][0].plot(data["R_peaks"][0], data["R_peaks"][1], "bo")

    axs[0][1].plot(ecg[0], ecg[1])
    axs[0][1].plot(data["P_peaks"][0], data["P_peaks"][1], "bo")
    axs[0][1].plot(data["Q_peaks"][0], data["Q_peaks"][1], "go")
    axs[0][1].plot(data["S_peaks"][0], data["S_peaks"][1], "ro")
    axs[0][1].plot(data["T_peaks"][0], data["T_peaks"][1], "yo")

    axs[1][1].plot(ecg[0], ecg[1])
    axs[1][1].plot(data["P_onsets"][0], data["P_onsets"][1], "bo")
    axs[1][1].plot(data["P_offsets"][0], data["P_offsets"][1], "bo")
    axs[1][1].plot(data["R_onsets"][0], data["R_onsets"][1], "go")
    axs[1][1].plot(data["R_offsets"][0], data["R_offsets"][1], "go")
    axs[1][1].plot(data["T_onsets"][0], data["T_onsets"][1], "ro")
    axs[1][1].plot(data["T_offsets"][0], data["T_offsets"][1], "ro")

    hrv_time = nk.hrv_time(data["R_peaks"][1], sampling_rate=sampling_rate, show=True)
    hrv_non = nk.hrv_nonlinear(data["R_peaks"][1], sampling_rate=sampling_rate, show=True)

    plt.show()
        
    


x, y = loadData("rec_1.dat", 1000, 12, 20)
ecg = []
ecg.append(x)
ecg.append(y)
ecg[1] = nk.ecg_clean(ecg[1], sampling_rate = 1000)
data, info = analyzeECG(ecg, 1000, method = "dwt")
showData(ecg, data, 1000)
