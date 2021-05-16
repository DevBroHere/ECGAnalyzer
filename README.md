# ECGAnalyzer
 Application for ecg analysis

The application is used for instant, automatic ECG analysis in terms of heart pathology. Made in python 3.x. The libraries used in project are: numpy, matplotlib, tkinter, scipy.
You can download .exe from dist folder. It should run on windows imimmediately. Warning: download icons too.

The purpose of the application is to help medical doctors in their work. The app is designed to help ensure a more effective diagnosis of heart disease. It should be recognized that it is not a substitute for the work of medical doctors.

User guide:
1. First you must import some useful data for analysis. To do this simply go to File>Open... or click on folder icon. Open a .dat file (I recommend to open the file from the default_graphs folder). Then the Load settings window will open up. There you can pass some values if you know from where the signal is or (recommended) click on Set to default option. Warning: Make sure the variable type is 16-bit. Click save and apply.
2. Now you should have signal on graph. Next step is signal filtering. You have two options, normal or automatic filtering. You can choose them from toolbar or from ECG analysis widget. If you want to pass some individual parameters, choose normal option (there's default button too) or if you want the program to do it for you, choose the automatic option. If you choose automatic option, special window will pop up. Type signal frequency (default is 1000) and hit Apply.
3. Now, when your signal is clear, it is time to set analysis area. To do this go to ECG analysis>Analysis area or simply take option from toolbar menu. Analysis area window should pop up. Enter time period and hit Apply.
4. Now it's time for a main part, analysis. To do this, go to ECG analysis>Analysis or choose loupe icon on toolbar. In analyis window type sampling rate (default 1000) and choose method. Hit Apply.
Everything is automated so it does not require too much effort. That's it, the program will now display the diagnosis information for you to save.

Here's an example of analysis:
![Example](https://user-images.githubusercontent.com/75490317/118397329-b8914100-b653-11eb-8eb2-90e1c972c656.PNG)

Implementation of applications is for the needs of studies and further engineering work. The intention is that the detection algorithms used in the software are to be used for machine learning.

Author:
Cezary Bujak

