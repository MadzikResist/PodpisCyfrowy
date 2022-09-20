import datetime
import Crypto.Signature.PKCS1_v1_5
import customtkinter
from tkinter import filedialog
import cv2
from tkinter import messagebox
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA3_512
from scipy.io.wavfile import read as wavread
import os
from moviepy.editor import VideoFileClip
import numpy as np


def getColorxy(image, x, y):
    cmpR = image[:, :, 0]
    cmpG = image[:, :, 1]
    cmpB = image[:, :, 2]
    return cmpR[x // 2][y // 2] << 16 + \
           cmpG[x // 2][y // 2] << 8 + \
           cmpB[x // 2][y // 2]


def convert_video_to_audio_moviepy(video_file, output_ext="wav"):
    """Converts video to audio using MoviePy library
    that uses `ffmpeg` under the hood"""
    filename, ext = os.path.splitext(video_file)
    clip = VideoFileClip(video_file)
    clip.audio.write_audiofile(f"{filename}.{output_ext}")


def getSoundBits(data, R, G, B, i, K, runcnt):
    retList = []

    SN1 = data[int(10 + (R * i + (G << 2) + B + runcnt) % (K / 2))]
    SN2 = data[int(15 + (R * i + (G << 3) + B + runcnt) % (K / 2))]
    SN3 = data[int(20 + (R * i + (G << 4) + B + runcnt) % (K / 2))]
    SN4 = data[int(5 + (R * i + (G << 1) + B + runcnt) % (K / 2))]
    SN5 = data[int(25 + (R * i + (G << 5) + B + runcnt) % (K / 2))]

    retList.append(SN1)
    retList.append(SN2)
    retList.append(SN3)
    retList.append(SN4)
    retList.append(SN5)

    return retList


def trng(someValue):
    outputNumbers = []  # wyjściowa tablica

    breaked = False  # if watchdog >th jeżeli przerwana pętla

    framerate = 25  # ilośc klatek na sekundę

    K = int(rate * 2 * 2 // framerate)  # ilość bitów na klatkę

    success, image = vidcap.read()  # odczyt pierwszej klatki z pliku
    frameNumber = 0  # numer klatki
    R = 0
    G = 0
    B = 0
    R1 = 0
    G1 = 0
    B1 = 0
    R2 = 0
    G2 = 0
    B2 = 0
    runcnt = 0
    watchdog = 0
    colori = ((getColorxy(image, image.shape[1] - 1, image.shape[0] - 1) + getColorxy(image, image.shape[1] - 1,
                                                                                      image.shape[0]) + getColorxy(
        image,
        image.shape[1] - 1, image.shape[0] + 1)) +
              (getColorxy(image, image.shape[1], image.shape[0] - 1) + getColorxy(image, image.shape[1],
                                                                                  image.shape[0]) + getColorxy(
                  image,
                  image.shape[
                      1],
                  image.shape[
                      0] + 1)) +
              (getColorxy(image, image.shape[1] + 1, image.shape[0] - 1) + getColorxy(image, image.shape[1] + 1,
                                                                                      image.shape[0]) + getColorxy(
                  image,
                  image.shape[1] + 1, image.shape[0] + 1))) / 9

    # First Block

    x = int(colori % (image.shape[1] // 2) + (image.shape[1] // 4))
    y = int(colori % (image.shape[0] // 2) + (image.shape[0] // 4))

    vt = (np.var(imagetemp[:, :, 0]) + np.var(imagetemp[:, :, 1]) + np.var(imagetemp[:, :, 2])) / 6
    # obliczenie wariancji dla obrazka z 3 kanałów RGB i zabranie z niej średniej
    th = 100

    while (len(outputNumbers) < (someValue * 8)) and success:
        # do momentu aż odczytujemy klatki i nie wygenerowaliśmy wymaganej ilości liczb
        # Second Block
        if len(outputNumbers) != 0 and len(outputNumbers) % 100000 == 0:
            runcnt += 1

        frameSound = sounddata[K * frameNumber:K * (frameNumber + 1) - 1]
        # wycięcie bitów z dźwięku odpowiadających dźwiękowi z klatki

        cmpR = image[:, :, 0]
        cmpG = image[:, :, 1]
        cmpB = image[:, :, 2]

        # indexNumber += 1
        # third Block
        for i in range(8):

            R = image[:, :, 0][y][x]
            G = image[:, :, 1][y][x]
            B = image[:, :, 2][y][x]

            # print(vt)
            # print(image.shape)
            if (R - R1) ** 2 + (G - G1) ** 2 + (B - B1) ** 2 < vt:
                x = (x + (R ^ G) + 1) % image.shape[1]
                y = (y + (G ^ B) + 1) % image.shape[0]
                # print(f"first x: {x}, y: {y}")
                watchdog += 1

                if watchdog > th:
                    # indexNumber += 1
                    watchdog = 0
                    breaked = True
                    break
                else:
                    R = image[:, :, 0][y][x]
                    G = image[:, :, 1][y][x]
                    B = image[:, :, 2][y][x]
                    continue
            else:

                soundDataSamples = getSoundBits(frameSound,
                                                cmpR[y][x],
                                                cmpG[y][x],
                                                cmpB[y][x],
                                                len(outputNumbers) + 1,
                                                K,
                                                runcnt)  # zabranie SN z dźwięku klatki

                toAdd = 1 & (R ^ G ^ B ^
                             R1 ^ G1 ^ B1 ^
                             R2 ^ G2 ^ B2 ^
                             soundDataSamples[0] ^
                             soundDataSamples[1] ^
                             soundDataSamples[2] ^
                             soundDataSamples[3] ^
                             soundDataSamples[4])  # Bit wyjściowy

                outputNumbers.append(toAdd)
                # print(toAdd[0], end="")
                R1 = R
                G1 = G
                B1 = B

                x = (((R ^ x) << 4) ^ (G ^ y)) % image.shape[1]
                y = (((G ^ x) << 4) ^ (B ^ y)) % image.shape[0]
            # print(image.shape[1])
            # print(f"second x: {x}, y: {y}")

        if not breaked:
            R2 = R
            G2 = G
            B2 = B
        # print(type(toAdd))

        success, image = vidcap.read()
        # frameNumber+=1
        breaked = False

    # print(outputNumbers)
    finalbinarylist = [x[0] for x in outputNumbers]

    # print(finalbinarylist)

    finalbinarylistgrou8 = [finalbinarylist[n:n + 8] for n in range(0, len(finalbinarylist), 8)]

    # print(finalbinarylistgrou8)

    finalDecimalList = []
    temp = ""
    for line in finalbinarylistgrou8:
        for elem in line:
            temp += str(elem)
        finalDecimalList.append(int(temp, 2))
        temp = ""
    # print(finalDecimalList[:someValue])
    print(f"somevalue: {someValue}", end=" | ")
    print(finalDecimalList, end=" | ")
    print(len(finalDecimalList))

    return bytes(finalDecimalList)[:someValue]


class App(customtkinter.CTk):
    WIDTH = 780
    HEIGHT = 520

    def __init__(self):

        global rate, sounddata, vidcap, vidcap1, imagetemp
        start_time = datetime.datetime.now()
        print(start_time)
        videoname = 'INFORMATYKA PODSTAWY odc. #15.mp4'  # nazwa wideo do dźwięku

        vidcap = cv2.VideoCapture(0)  # deklaracja źródła obrazu jako kamera
        vidcap1 = cv2.VideoCapture(videoname)  # deklaracja źródła obrazu jako plik dźwiękowy
        vidcap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
        vidcap1.set(cv2.CAP_PROP_BUFFERSIZE, 3)

        success1, imagetemp = vidcap1.read()  # odczytanie pierwszej klatki
        i = 0
        imax = 25 * 3 - 1  # określenie numeru klatki w 3 sekundzie
        while success1 and (i < imax):  # do kiedy odczytujemy klatkę z wideo i nie jest to klatka z 3 sekundy filmu
            success1, imagetemp = vidcap1.read()  # odczyt klatki z wideo
            i += 1

        # convert_video_to_audio_moviepy(videoname)  # wyciągnięcie dźwięku z wideo
        rate, sounddata = wavread(videoname[:-4] + ".wav")  # odczyt pliku dźwiękowego

        super().__init__()
        self.geometry(f"{App.WIDTH}x{App.HEIGHT}")
        self.protocol("WM_DELETE_WINDOW", self.onDestroy)

        # GRID
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # LEFT
        self.left = customtkinter.CTkFrame(master=self,
                                           width=390,
                                           corner_radius=0)
        self.left.grid(row=0, column=0, sticky="ns")

        self.left.grid_rowconfigure(0, minsize=10)
        self.left.grid_rowconfigure(10, weight=1)

        # RIGHT
        self.right = customtkinter.CTkFrame(master=self,
                                            width=390,
                                            corner_radius=0)
        self.right.grid(row=0, column=1, sticky="")

        self.right.grid_rowconfigure(0, minsize=10)
        self.right.grid_rowconfigure(10, weight=1)

        # LABELS
        self.label = customtkinter.CTkLabel(master=self.left,
                                            text="Sender")
        self.label.grid(row=1, column=0, pady=20)

        self.labelReciever = customtkinter.CTkLabel(master=self.right,
                                                    text="Receiver")
        self.labelReciever.grid(row=1, column=1, pady=10, padx=30)

        # BUTTONS
        self.button1 = customtkinter.CTkButton(master=self.left,
                                               text="Message",
                                               command=self.save)
        self.button1.grid(row=3, column=0, pady=10)

        self.button2 = customtkinter.CTkButton(master=self.left,
                                               text="Generate a key",
                                               command=self.genereteKey)
        self.button2.grid(row=4, column=0, pady=10)

        self.button3 = customtkinter.CTkButton(master=self.left,
                                               text="Hashing",
                                               command=self.hashing)
        self.button3.grid(row=5, column=0, pady=10)

        self.button4 = customtkinter.CTkButton(master=self.right,
                                               text="Check",
                                               command=self.check)
        self.button4.grid(row=2, column=1, pady=10)

        # INPUT
        self.text_column = customtkinter.CTkFrame(master=self.left,
                                                  width=390,
                                                  corner_radius=0)
        self.text_column.grid(row=2, column=0, sticky="", padx=20)

        self.text_column.rowconfigure(2, weight=10)
        self.text_column.columnconfigure(0, weight=0)

        self.entry = customtkinter.CTkEntry(master=self.text_column,
                                            width=250,
                                            placeholder_text="Type message")
        self.entry.grid(row=2, column=0, columnspan=1, sticky="nswe")

        # SAVE FILE

    def save(self):
        file = filedialog.asksaveasfile(initialdir=os.getcwd(),
                                        defaultextension='.txt',
                                        filetypes=[
                                            ("Text file", ".txt"),
                                            ("All files", ".*"),
                                        ])
        if file is None:
            return
        filetext = str(self.entry.get())
        file.write(filetext)
        file.close()

        # GENERETE A KEY

    def genereteKey(self):
        # key = RSA.generate(2048, trng)
        key = RSA.generate(2048)
        # public key
        with open('publickey.key', 'wb') as f:
            f.write(key.public_key().exportKey('PEM'))
        with open('publickey.key') as f:
            lines = f.read()
            print(lines)
        # private key
        with open('privatekey.key', 'wb') as f:
            f.write(key.exportKey('PEM'))
        with open('privatekey.key') as f:
            lines = f.read()
            print(lines)

        # HASHING MESSAGE

    def hashing(self):
        def fileOpen(file):
            keyFile = open(file, 'r')
            keyData = keyFile.read()
            keyFile.close()
            return keyData

        privateKey = RSA.importKey(fileOpen('privatekey.key'))
        message = fileOpen('message.txt')
        hashValue = SHA3_512.new(bytes(message, encoding='utf8'))
        signature = Crypto.Signature.pkcs1_15.new(privateKey).sign(hashValue)
        sign = open('signatureFile', 'wb')
        sign.write(signature)

        # CHECKING KEY AND MESSAGE

    def check(self):
        def openFile(file):
            f = open(file, 'rb')
            keyData = f.read()
            f.close()
            return keyData

        # Opening with public key
        publicKey = RSA.importKey(openFile('privatekey.key'))
        message = openFile('message.txt')
        signature = openFile('signatureFile')

        # Verification
        try:
            hash = SHA3_512.new(message)
            Crypto.Signature.pkcs1_15.new(publicKey).verify(hash, signature)
            messagebox.showinfo('Attention', 'Successful')
        except:
            messagebox.showinfo('Attention', 'Verification error')

    def onDestroy(self, event=0):
        self.destroy()


if __name__ == '__main__':
    app = App()
    app.mainloop()
