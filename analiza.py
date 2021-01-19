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

    for key, name in info.items():
        print(key, ":", name)

    return data, info

def diagnoseECG(info):
    #Analiza pulsu
    if info["ECG_Rate_Mean"] < 60:
        print("Częstotliwość pracy serca poniżej oczekiwanego przedziału \
60-100 uderzeń na minutę: bradykardia (rzadkoskurcz)")
    elif info["ECG_Rate_Mean"] > 100:
        print("Częstotliwość pracy serca powyżej oczekiwanego przedziału \
60-100 uderzeń na minutę: tachykardia (częstoskurcz)")
    elif info["ECG_Rate_Mean"] >= 60 and info["ECG_Rate_Mean"] <= 100:
        print("Częstotliwość pracy serca w normie")
    #Analiza współczynników HRV
    if info["HRV_MeanNN"] < 750:
        print("Średni odstęp RR nieprawidłowy (poniżej 750 ms): pacjent wymaga \
dalszej diagnozy.")
    elif info["HRV_MeanNN"] > 750:
        print("Średni odstęp RR w normie (powyżej 750 ms)")
    if info["HRV_RMSSD"] > 39 or info["HRV_RMSSD"] < 15:
        print("Współczynnik HRV rMSSD (pierwiastek kwadratowy ze średniej sumy \
kwadratów różnic między kolejnymi odstępami RR) nie mieści się w zakresie \
optymalnym 27±12 ms: pacjent wymaga dalszej diagnozy.")
    elif info["HRV_RMSSD"] <= 39 and info["HRV_RMSSD"] >= 15:
        print("Współczynnik HRV rMSSD (pierwiastek kwadratowy ze średniej sumy \
kwadratów różnic między kolejnymi odstępami RR) mieści się w zakresie \
optymalnym 27±12 ms: współczynnik w normie.")
    if info["HRV_SDNN"] < 102 or info["HRV_SDNN"] > 180:
        print("Współczynnik HRV SDNN (Odchylenie standardowe wszystkich odstępów \
RR) nie mieści się w zakresie 141±39 ms: pacjent wymaga dalszej diagnozy.")
        if info["HRV_SDNN"] > 16 and info["HRV_SDNN"] < 73:
            print("Podejrzenie jednego z powikłań typu: kardiomiopatia przerostowa lub \
rozstrzeniowa; zapalenie mięśnia sercowego")
        if info["HRV_SDNN"] > 73 and info["HRV_SDNN"] < 102:
            print("Podejrzenie wady aortalnej")
    elif info["HRV_SDNN"] >= 102 or info["HRV_SDNN"] <= 180:
        print("Współczynnik HRV SDNN (Odchylenie standardowe wszystkich odstępów \
RR) w normie")
    #Analiza czasu trwania załamków
    if info["P_Time"] < 0.08:
        print("Czas trwania załamka P nie mieści się zakresie normy (poniżej normy): pacjent \
wymaga dalszej diagnozy.")
        
        if info["P_Time"] > 0.12:
            print("Czas trwania załamka P nie mieści się zakresie normy (powyżej normy): podejrzenie powiększenia lewego przedsionka lub zaburzeń przewodzenia \
śródprzedsionkowego")
            
    elif info["P_Time"] >= 0.08 and info["P_Time"] <= 0.12:
        print("Czas załamka P w normie")
        
    if info["QRS_Time"] < 0.06:
        print("Czas trwania zespołu QRS nie mieści się w zakresie normy (poniżej normy): pacjent \
wymaga dalszej diagnozy")
        if info["QRS_Time"] > 0.1:
            print("Czas trwania zespołu QRS nie mieści się w zakresie normy (powyżej normy): podejrzenie przerostu komory")
        if abs(info["Q_Amplitude"]) > info["R_Amplitude"]/4:
            print("Nieprawidłowa proporcja między załamkiem Q a załamkiem R: podejrzenie zawału serca")
            
    elif info["QRS_Time"] >= 0.06 and info["QRS_Time"] <= 0.1:
        print("Czas zespołu QRS w normie")
        
    if info["PQ_Segment"] < 0.04:
        print("Czas trwania odcinka PQ nie mieści się w normie (poniżej normy): pacjent wymaga \
dalszej diagnozy")
        
    elif info["PQ_Segment"] > 0.1:
        print("Czas trwania odcinka PQ nie mieści się w normie (powyżej normy): pacjent wymaga \
dalszej diagnozy")
        
    elif info["PQ_Segment"] >= 0.04 or info["PQ_Segment"] <= 0.1:
        print("Czas trwania odcinka PQ mieści się w normie")
        
    if info["PQ_Space"] < 0.12:
        print("Czas trwania odstępu PQ nie mieści się w normie (poniżej normy): pacjent wymaga \
dalszej diagnozy")
    elif info["PQ_Space"] > 0.2:
        print("Czas trwania odstępu PQ nie mieści się w normie (powyżej normy): pacjent wymaga \
dalszej diagnozy")
    elif info["PQ_Space"] >= 0.12 and info["PQ_Space"] <= 0.2:
        print("Czas trwania odstępu PQ mieści się w normie")
    if info["ST_Segment"] < 0.06:
        print("Czas trwania odcinka ST nie mieści się w normie (poniżej normy): \
pacjent wymaga dalszej diagnozy")
    elif info["ST_Segment"] > 0.1:
        print("Czas trwania odcinka ST nie mieści się w normie (powyżej normy): \
pacjent wymaga dalszej diagnozy")
    elif info["ST_Segment"] >= 0.6 and info["ST_Segment"] <= 0.1:
        print("Czas trwania odcinka ST mieści się w normie")
    if info["T_Time"] < 0.12:
        print("Czas trwamia załamka T nie mieści się w normie (poniżej normy): \
pacjent wymaga dalszej diagnozy")
    if info["T_Time"] > 0.16:
        print("Czas trwamia załamka T nie mieści się w normie (powyżej normy): \
pacjent wymaga dalszej diagnozy")
    if info["T_Time"] >= 0.12 and info["T_Time"] <= 0.16:
        print("Czas trwania załamka T w normie")
    if info["QT_Space"]/(info["HRV_MeanNN"]/1000) > 0.455:
        print("Podejrzenie zespołu długiego QT")
    if info["QT_Space"]/(info["HRV_MeanNN"]/1000) < 0.33:
        print("Podejrzenie jednej z chorób: hiperkaliemia, hiperkalcemia lub \
zespół krótkiego QT.")
    if info["QT_Space"]/(info["HRV_MeanNN"]/1000) >= 0.33 and info["QT_Space"]/(info["HRV_MeanNN"]/1000) <= 0.455:
        print("Odstęp QT w normie")
    #Prawie skończone, jeszcze pozostałe odcinki i załamki oraz poprawa
    #wartości spoza zakresu.
    

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
#x, y = loadData("s0015lre.dat", 10000, 16, 32)
ecg = []
ecg.append(x)
ecg.append(y)
ecg[1] = nk.ecg_clean(ecg[1], sampling_rate = 1000)
ecgnew = []
ecgnew.append(ecg[0][5000:15000])
ecgnew.append(ecg[1][5000:15000])
data, info = analyzeECG(ecgnew, 1000, method = "dwt")
diagnoseECG(info)
showData(ecg, data, 1000)
