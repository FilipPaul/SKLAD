import os
import traceback
import yaml
from PyQt5 import QtWidgets,QtCore
import datetime
from unidecode import unidecode
#Automaticaly update files from QT designer
if os.path.exists("scanSimulatorUi.py"):
    os.remove("scanSimulatorUi.py")
bashCommand = "pyuic5 -o scanSimulatorUi.py scanSimulatorUi.ui"
os.system(bashCommand)


from AutomateSuperPackage.AutomateSuperModule import SuperClass
from LOT_GENERATOR import LoTGenerator
from QR_code_generator import QRcodeGenerator

#PyQT IMPORTS
from scanSimulatorUi import Ui_Form as designer_UI

class MainWindowApp(QtWidgets.QWidget):
    class STATES():
        def __init__(self):
            self.LOGIN = "PRIHLASTE SE!"
            self.SCAN_LOT = "NASKENUJTE ZAKAZKU LO"
            self.SCAN_QR = "NAKSENUJTE PRODUKT SN"
            self.COUNT = "ZADEJTE POCET"
            self.READY_TO_SEND = "SEND PRO ODESLANI"

        
    def __init__(self,*args, **kwargs):#args = multiple input variables, **kvargs multiple keyword variables (dictionaries, touples etc.)
    ################ INIT Function ##################
        super().__init__(*args, **kwargs)#super inherits all methods and properties from its parent  (QWIDGET classes)
        #Load UI forms creaated in QTdDesigner
        self.ui = designer_UI() #UI form generated by UI designe
        self.ui.setupUi(self)
       
        self.ui.pb_scan.clicked.connect(self.scanNumber)
        self.ui.pb_ok.clicked.connect(self.scanNumber)
        self.ui.pb_logout.clicked.connect(self.scanNumber)
        self.ui.pb_change_lot.clicked.connect(self.scanNumber)
        self.ui.pb_change_qr.clicked.connect(self.scanNumber)
        self.ui.pb_cancel.clicked.connect(self.scanNumber)
        self.ui.pb_qr_gen.clicked.connect(self.generateQR)
        self.ui.pb_lot_gen.clicked.connect(self.generateLot)

        self.popis_zakazky = ""
        self.states = self.STATES()
        self.current_state = self.states.LOGIN
        self.ui.la_status.setText(self.states.LOGIN)

        self.uzivatel = ""
        self.ui.la_count.setText("")
        self.ui.la_lot.setText("")
        self.ui.la_SN.setText("")
        self.loadConfigData()
        self.login_flag = 0
        self.lot_flag = 0

        self.ACCES = SuperClass().database.AccesDatabase
        print(self.database_path)
        self.ACCES.SimplyConnectByPath(self.database_path)

        try:
            self.SCAN = SuperClass().Hardware.HWellScanner.SerialCommunication()
            self.SCAN.ComInstance.baudrate = 115200
            self.SCAN.ComInstance.port = self.YAML["PORT"]
            self.SCAN.ComInstance.timeout = 1
            self.SCAN.ComInstance.parity = "N"
            self.SCAN.ComInstance.stopbits = 1
            self.SCAN.ComInstance.bytesize = 8
            self.SCAN.setCOM(self.SCAN.ComInstance)

            self.resetLabels()
            self.sendData()

            self.main_timer = QtCore.QTimer()
            self.main_timer.timeout.connect(self.scanNumber)
            self.main_timer.start(300)
        
        except Exception:
            self.ui.la_status.setText(f"Nepodařilo se připojit na\nPORT {self.YAML['PORT']}")
            print(traceback.format_exc())


    def generateQR(self):
        QRcodeGenerator()
    
    def generateLot(self):
        LoTGenerator()

    def loadConfigData(self):
        with open("config.yaml") as f:    
            self.YAML = yaml.safe_load(f)
        
        self.database_path = self.YAML["DATABASE"]
        self.LOT_prefix = self.YAML["LOT"]["PREFIX"]
        self.LOT_suffix = self.YAML["LOT"]["SUFFIX"]
        self.QR_prefix = self.YAML["PRODUCT_ID"]["PREFIX"]
        self.QR_suffix = self.YAML["PRODUCT_ID"]["SUFFIX"]
        self.COUNT_prefix = self.YAML["POCET"]["PREFIX"]
        self.COUNT_suffix = self.YAML["POCET"]["SUFFIX"]
        self.YES_string = self.YAML["POTVRZOVANI"]["OKEY"]
        self.NO_string = self.YAML["POTVRZOVANI"]["CANCEL"]
    
    def inputMethod(self):
        status, packet = self.SCAN.NonBlockingRead()
        if status:
            return status, packet[:-1]
        else:
            return status, None

    def resetLabels(self):
        self.ui.la_prijmeni.setText("Neprihlasen")
        self.ui.la_osobni_cislo.setText("Neprihlasen")
        self.ui.la_count.setText("")
        self.ui.la_lot.setText("")
        self.ui.la_SN.setText("")
        self.ui.la_info.setText("Prihlaste se")
        
        ...


    def scanNumber(self):
        #print(self.login_flag,self.lot_flag)
        if "pb" in self.sender().objectName():
            scanned_string =self.sender().text()

            if self.sender() == self.ui.pb_scan:
                scanned_string = self.ui.le_SCAN.text()
            print(f"scanned_string BTN",scanned_string)
        else:
            status, scanned_string = self.inputMethod()
            if status:
                ...
            else:
                return
        
        print(f"scanned_string",scanned_string)

        if scanned_string == "LOGIN":
            self.ui.la_info.setText("Odhlaseno")
            self.resetLabels()
            self.setState(self.states.LOGIN)
            self.login_flag = 0
            self.sendData()
            return

        if scanned_string == "SN" and self.login_flag == 1 and self.lot_flag == 1:
            self.ui.la_count.setText("")
            self.ui.la_SN.setText("")
            self.ui.la_info.setText("Zmena Produktu")
            self.setState(self.states.SCAN_QR)
            self.sendData()
            return

        if scanned_string == "LO" and self.login_flag == 1:
            self.ui.la_count.setText("")
            self.ui.la_lot.setText("")
            self.ui.la_SN.setText("")
            self.ui.la_info.setText("Zmena zakazky")
            self.setState(self.states.SCAN_LOT)
            self.lot_flag = 0
            self.sendData()
            return

        if self.current_state == self.states.LOGIN:
            prijmeni,osobni_cislo = self.checkIfUzivateExists(scanned_string)
            if prijmeni != False:
                self.ui.la_prijmeni.setText(prijmeni)
                self.ui.la_osobni_cislo.setText(str(osobni_cislo))
                self.setState(self.states.SCAN_LOT)
                self.ui.la_info.setText("uspesne prihlasen")
                self.login_flag = 1

            else:
                self.ui.la_prijmeni.setText("Neprihlasen")
                self.ui.la_osobni_cislo.setText("Neprihlasen")
                self.ui.la_info.setText("Nespravne udaje")
                self.login_flag = 0
            self.sendData()
            return
        
        if self.current_state == self.states.SCAN_LOT:
            status,self.zakazka,self.popis_zakazky,self.lot_ID = self.checkIfLotExists(scanned_string)
            if status:
                self.ui.la_lot.setText(self.popis_zakazky)
                self.ui.la_info.setText(f"LO: OK")
                self.setState(self.states.SCAN_QR)
                self.lot_flag = 1
            else:
                self.ui.la_lot.setText("Neznama zakazka")
                self.ui.la_info.setText(f"Neznama zakazka")
                self.lot_flag = 0
            self.sendData()
            return

        
        if self.current_state == self.states.SCAN_QR:
            status,nazev,popis,self.QR_akutal_pocet_kusu,self.QR_ID,self.jednotka = self.checkIfQRExists(scanned_string)
            if status:
                self.ui.la_SN.setText(f"{nazev} ({self.QR_akutal_pocet_kusu}{self.jednotka})")
                self.ui.la_info.setText(f"+ pred poct.: nasklad.")
                self.setState(self.states.COUNT)
            
            else:
                self.ui.la_info.setText(f"NEZNAME SN")

            self.sendData()
            return

        if self.current_state == self.states.COUNT:
            status,self.count_to_change = self.checkIfCountExists(scanned_string)
            if status:
                self.ui.la_count.setText(f"{self.count_to_change}")
                self.ui.la_info.setText(f"Zadan pocet: {self.count_to_change}")
                self.setState(self.states.READY_TO_SEND)
            
            else:
                self.ui.la_info.setText(f"SPATNY POCET !")
            self.sendData()
            return

        
        if self.current_state == self.states.READY_TO_SEND:
            if scanned_string == "SEND":
                if self.updateDatabase():
                    self.ui.la_info.setText("uspesne odeslano")
                    self.ui.la_count.setText("")
                    self.ui.la_SN.setText("")
                    self.setState(self.states.SCAN_QR)
                else:
                    self.ui.la_info.setText("Chyba pri odesilani")
            elif scanned_string == "CANCEL":
                self.ui.la_info.setText("Odesilani zruseno")
                self.ui.la_count.setText("")
                self.ui.la_SN.setText("")

            else:
                self.ui.la_info.setText("Chyba pri odesilani")
            self.sendData()
            return

               
        
    def checkIfLotExists(self,QRcode)-> bool:
        self.ACCES.WriteQuery(f"SELECT Zakazka, POPIS,ID FROM ZAKAZKY where Zakazka = '{QRcode}'")
        result = self.ACCES.ResultFromQuery()
        print(result)

        if len(result) == 0:
            return False, False, False, False
        
        else:
            zakazka = result[0][0]
            popis = result[0][1]         
            lotID = result[0][2]
            return True, zakazka, popis,lotID

    def checkIfQRExists(self,QRcode)-> bool:
        print(f"SELECT NAZEV,POPIS,AktualniPocet,ID,Jednotka FROM SKLAD where QRCODE = '{QRcode}'")
        self.ACCES.WriteQuery(f"SELECT NAZEV,POPIS,AktualniPocet,ID,Jednotka FROM SKLAD where QRCODE = '{QRcode}'")
        result = self.ACCES.ResultFromQuery()
        print(result)

        if len(result) == 0:
            return False,False,False,False, False,False
        
        else:
            nazev = result[0][0]
            popis = result[0][1]
            aktualni_stav = result[0][2]        
            QR_ID = result[0][3]
            jednotka = result[0][4]
            return True,nazev,popis,aktualni_stav,QR_ID,jednotka

    def checkIfCountExists(self,QRcode)-> bool:
        try:
            if "+" in QRcode:
                pocet = -int(QRcode[1:])
            else:
                pocet = int(QRcode)
            return True,pocet
        except:
            return False, False
        
    def updateDatabase(self):
        try:
            #UPDATE sklad
            lot = self.zakazka
            uzivatel = self.ui.la_prijmeni.text()

            pocet_sklad = self.QR_akutal_pocet_kusu - self.count_to_change
            if pocet_sklad < 0:
                pocet_sklad = 0

            self.ACCES.WriteQuery(f"UPDATE SKLAD SET AktualniPocet = {pocet_sklad}  WHERE ID = {self.QR_ID}")

            #update zakazky
            self.ACCES.WriteQuery(f"SELECT POCET FROM [{lot}] WHERE refSkladID = {self.QR_ID}")
            result = self.ACCES.ResultFromQuery()
            if len(result) > 0:
                pocet_zakazky = int(result[0][0])
                self.ACCES.WriteQuery(f"UPDATE [{lot}] SET POCET = {pocet_zakazky + self.count_to_change}  WHERE refSkladID = {self.QR_ID}")
            else:
                self.ACCES.WriteQuery(f"INSERT INTO [{lot}] (refSkladID,POCET) VALUES ({self.QR_ID},{self.count_to_change})")

            #update LOG
            print(f"INSERT INTO LOGY (refSkladID,refZakazkaID,POCET,AKCE,DatumCas) VALUES ({self.QR_ID},{self.lot_ID},{self.count_to_change},\
                'SCAN',#{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}#)")
            self.ACCES.WriteQuery(f"INSERT INTO LOGY (refSkladID,refZakazkaID,POCET,AKCE,DatumCas,UZIVATEL) VALUES ({self.QR_ID},{self.lot_ID},{self.count_to_change},\
                'SCAN',#{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}#,'{uzivatel}')")
        
            self.ACCES.UpdateDatabase()
            return True

        except Exception as e:
            print(e)
            return False

    def setState(self, state,update_label = True):
        self.current_state = state
        if update_label:
            self.ui.la_status.setText(state)
    
    def checkIfUzivateExists(self,input_from_scanner : str)-> str:
        try: #if input is convertible to int
            osobni_cislo = int(input_from_scanner)
            query = f"SELECT OsobniCislo, PRIJMENI FROM UZIVATELE WHERE OsobniCislo = {osobni_cislo}"
        
        except: #input is another string (probably name)
            query = f"SELECT OsobniCislo,PRIJMENI FROM UZIVATELE WHERE PRIJMENI = '{input_from_scanner}'"

        print(query)
        self.ACCES.WriteQuery(query)
        result = self.ACCES.ResultFromQuery()
        print(result)

        if len(result) > 0:
            osobni_cislo = result[0][0]
            prijmeni = result[0][1]
            return prijmeni,osobni_cislo
        
        else :
            return False,False

    def sendData(self,scanner_ID = 0):
        jmeno = self.ui.la_prijmeni.text()
        osobni_cislo = self.ui.la_osobni_cislo.text()
        lot = self.ui.la_lot.text()
        product_info = self.ui.la_SN.text()
        count = self.ui.la_count.text()
        last_info = self.ui.la_info.text()
        main_info = self.ui.la_status.text()

        sablona_text = f"""JMENO (OSOBNICISLO)
LO: LOT
SN: PRODUCT_INFO
POCET: COUNT
MAIN_INFO
INFO"""
        final_text = sablona_text.replace("JMENO",jmeno).replace("OSOBNICISLO",osobni_cislo).replace("LOT",lot)\
            .replace("PRODUCT_INFO",product_info).replace("COUNT",count).replace("MAIN_INFO",main_info).replace("INFO",last_info).replace("POPIS_ZAKAZKY",str(self.popis_zakazky))
        #print(final_text)

        rows_in_final_text = final_text.split("\n")
        final_rows = []
        for rows in rows_in_final_text:
            if len(rows) < 22:
                rows += " " * (22 - len(rows))
            else:
                rows = rows[:22]
            


            final_rows.append(rows)

        scanner_text = "\x12"
        #print(final_rows)
        for rows in final_rows:
            #print(len(rows))
            scanner_text += rows

        scanner_text = f"\x12{unidecode(scanner_text)}\x0D"
        self.SCAN.ComInstance.write(scanner_text.encode("utf-8"))
        print(scanner_text)
        

if __name__ == '__main__':
    #Read config file:

    app = QtWidgets.QApplication([])
    MainWindow = MainWindowApp()
    #MainWindow.setWindowFlags(QtCore.Qt.FramelessWindowHint)
    MainWindow.show() 
        # return self.currentText()
    #MainWindow.showMaximized()
    #self.showFullScreen()
    app.exec_()

