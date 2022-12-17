import serial
import time as tim
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, time, datetime
import PySimpleGUI as sg 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial.tools.list_ports

sg.theme('SystemDefault1')
# ser = serial.Serial("COM7", 9600) 
ports = serial.tools.list_ports.comports()
readCommand = b'\xAA\x04\x91\x00\x00\x40\x00\x40\x05\x00\x00\x30\x75\xB8\x0B\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x2E'
commandPC = b'\xAA\x04\x92\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x42'
commandON = b'\xAA\x04\x92\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x43'
commandOFF = b'\xAA\x04\x92\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x42'

def readData():
    ser.flushInput()
    ser.flushOutput()
    ser.write(readCommand)
    data = ser.read(26)
    datahex = data.hex()
    bytelist = [datahex[i:i+2] for i in range(0,len(datahex),2)]
    current = bytelist[4] + bytelist[3]
    current = int(current,16)/1000

    voltage = bytelist[8] + bytelist[7] + bytelist[6] + bytelist[5]
    voltage = int(voltage,16)/1000

    power = bytelist[10] + bytelist[9]
    power = int(power,16)/10
    return (current, voltage, power)

def writeCurrent(current):
    ser.flushInput()
    ser.flushOutput()
    setCommand = bytearray(b'\xAA\x04\x90\x30\x75\xB8\x0B\x04\x01')
    hexSet = current.to_bytes(2,'little')
    setCommand.extend(hexSet)
    endCommand = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    setCommand.extend(endCommand)
    checksum = int(hex(sum(setCommand))[-2:],16)
    setCommand.append(checksum)
    ser.write(setCommand)

def get_Characteristics(data):
    df = pd.DataFrame(data, columns = ['prad', 'napiecie', 'power','setcurrent'])
    answer=plt.figure()
    plt.plot(df['napiecie'], df['prad'])
    plt.plot(df['napiecie'], df['power'])
    plt.title("Charakterystyka I-U, P-U")
    plt.xlabel("Napięcie [V]")
    plt.ylabel("Prąd [A]")
    return answer

def measure(startCurrent, endCurrent, stepSize, delay):
    data = []
    startTime = int(tim.time() * 1000)
    for i in range(startCurrent,endCurrent,stepSize):
        writeCurrent(i)
        tim.sleep(delay)
        curr = readData()
        curr = curr + (i,)
        data.append(curr)
        print(curr)
        
    writeCurrent(0)
    stopTime = int(tim.time() * 1000)
    print("Czas pomiaru: " + str(stopTime-startTime) + "ms")
    df = pd.DataFrame(data, columns = ['prad', 'napiecie', 'power', 'setcurrent'])
    now = datetime.now()
    date_time = now.strftime("%m_%d_%Y %H-%M-%S")
    df.to_csv("Wyniki/results" + date_time + ".csv", index=False)
    return data

#---------------------------
def caluclate_efficiency(pole,liczba_ogniw,natezenie_swiatla,moc_pradu):
    moc_przyjeta=pole*liczba_ogniw*natezenie_swiatla/100000
    sprawnosc=(moc_pradu/moc_przyjeta)*100
    return sprawnosc

#--------------------------- added by Piotrek


def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side="top", fill="both", expand=1)
    return figure_canvas_agg

logo_column = [[sg.Image('AGH.png', size=(80,80))]]

layout2=[[sg.Text('COM:'),sg.Combo(ports,key='com',size=(10,1))],
        [sg.Button('Rozpocznij pomiar',size=(15,1))],
        [sg.Button('Zapisz jako CSV',size=(15,1))],
        [sg.Button('Generuj raport PDF',size=(15,1))]]

layout3=[[sg.Text('Parametry ogniwa:')],
        [sg.Text("Pole ogniwa[cm2]:")],
        [sg.Text("Liczba ogniw:")],
        [sg.Text("")]]
inputs_3=[[sg.Text('')],[sg.InputText(size=(10,1),key='-POLE_OGNIWA-', default_text = "153")],[sg.InputText(size=(10,1),key='-LICZBA_OGNIW-')],[sg.Text("")]]

layout4=[[sg.Text('Parametry pomiaru:')],
        [sg.Text("Prąd maksymalny [A]:")],
        [sg.Text("Skok:")],
        [sg.Text("Natężenie [W/m^2]:")]]

inputs_4=[[sg.Text('')],[sg.InputText(size=(10,1),key='-PRAD_MAX-', default_text = "8000")],[sg.InputText(size=(10,1),key='-SKOK-', default_text = "100")],[sg.InputText(size=(10,1),key='-NATEZENIE-')]]

layout_main=[[sg.Column(logo_column,justification="left"),sg.VSeperator(),sg.Column(layout2),sg.VSeperator(),sg.Column(layout3),sg.Column(inputs_3),sg.VSeperator(),sg.Column(layout4),sg.Column(inputs_4)],
        [sg.Canvas(size=(500,500),key="-CANVAS-")],
        [sg.Text("Parametry ogniwa",justification='left')],
        [sg.Text("Sprawnosc=",justification='left'), sg.Text("", size=(0, 1), key='OUTPUT')]]



def main():
    #START
    empty_df = pd.DataFrame(columns=["prad","napiecie","power","setcurrent"])
    answer=get_Characteristics(empty_df)

    window=sg.Window("Badanie ogniw fotowoltaicznych ver 1.0",layout_main,location=(0,0),finalize=True,element_justification="center")
    fig_agg = draw_figure(window["-CANVAS-"].TKCanvas, answer)

    while True:
        event,values=window.read()
        if event=='Rozpocznij pomiar':
            # data=pd.read_csv('prawe_przetarte_11_30_2022 11-39-38.csv')
            # answer=get_Characteristics(data)
            # fig_agg.get_tk_widget().forget()
            # fig_agg = draw_figure(window["-CANVAS-"].TKCanvas, answer)
            # window.refresh()
            # # wybor portu
            global ser
            try: ser
            except: ser = serial.Serial(values["com"].device, 9600)
            # window['OUTPUT'].update("test") # aktualizacja sprawnosci
            # # rozpoczęcie pomiaru
            ser.write(commandPC)
            tim.sleep(0.1)
            ser.write(commandON)
            data = measure(1,int(values["-PRAD_MAX-"]),int(values["-SKOK-"]),0.1)
            answer=get_Characteristics(data)
            fig_agg.get_tk_widget().forget()
            fig_agg = draw_figure(window["-CANVAS-"].TKCanvas, answer)
            window.refresh()
            pass
       
        if event=='Generuj raport PDF':
            #TODO zaimplementować generowanie i zapis raportu
            pass
        if event=='Zapisz jako CSV':
            #TODO zaimplementować zapis
            pass

        elif event == sg.WIN_CLOSED:
            window.close()
            break

main()


