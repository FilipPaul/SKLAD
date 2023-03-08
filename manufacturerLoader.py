import requests
import pickle
from logger import LOGGER
log = LOGGER("ALL")
from PyQt6 import QtCore, QtGui, QtWidgets
from typing import List

MOUSER_SEARCH_API_KEY = "234ba5f6-eb12-4020-a50f-ef56390e0e1f" #MOUSER
request_url = f"https://api.mouser.com/api/v2/search/partnumber?apiKey={MOUSER_SEARCH_API_KEY}"
#
JSON_REQUEST_TEMPLATE = {
  "SearchByPartRequest": {
    "mouserPartNumber": "PARTNUMBER",
    "partSearchOptions": "string"
  }
}

from manufacturer_loaderGUI import Ui_Form
import webbrowser
import pyodbc
import yaml
import random
import time
import string
import os

import urllib.request
import urllib
import pprint
  
# Retrieving the resource located at the URL
# and storing it in the file name a.png
opener = urllib.request.build_opener()
opener.addheaders = [
    (
        "User-Agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
    )
]
urllib.request.install_opener(opener)

class pictureLabelWidget(QtWidgets.QLabel):
    def __init__(self, image_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pixmap = QtGui.QPixmap(image_path)
        self.setPixmap(pixmap)
        self.setScaledContents(True)
        self.setMinimumWidth(38)
        self.setMinimumHeight(38)
        self.setMaximumWidth(38)
        self.setMaximumHeight(38)


class signals(QtCore.QObject):
    signal_finished = QtCore.pyqtSignal(int,bool)



class loaderToDatabaseClass():
    dict_of_translations = {"Dodavatel": "Dodavatel",
                            "Dodavatel partNumber": "partNumberDodavatel",
                            "Výrobce": "Vyrobce",
                            "Výrobce partNumber": "NAZEV",
                            "Popis CZ": "POPIS",
                            "Popis EN": "POPIS_EN",
                            "Na skladě dodavatel": "skladDodavatel",
                            "Na skladě ČEVOR": "AktualniPocet",
                            "Factory Lead time": "DobaDodaniFabrika",
                            "Cena": "CenaZaKusKc",
                            "Ceník": "Cenik",
                            "Datasheet": "Datasheet",
                            "Link": "Odkaz",
                            "Pict": "Obrazek"}
    def __init__(self,table:QtWidgets.QTableWidget,database_connection:pyodbc.Connection,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table = table
        self.signals = signals()
        self.log = LOGGER("ALL").log
        self.dB = database_connection
        self.dBcursor = self.dB.cursor()


    def checkIfColumnIsStandartItem(self,column):
        if self.getColumnNameFromIndex(column) == "Vybrat" or self.getColumnNameFromIndex(column) == "Pict":
            return False
        else:
            return True

    def getIndexFromColumnName(self,column_name):
        for columns in range(self.table.columnCount()):
            if self.table.horizontalHeaderItem(columns).text() == column_name:
                return columns
        else:
            return False	

    def getColumnNameFromIndex(self,column_index):
        return self.table.horizontalHeaderItem(column_index).text()

    def checkIfColumnExists(self, column_name, table_name):
        query = f"SELECT TOP 1 * FROM {table_name}"
        self.dBcursor.execute(query)
        result = self.dBcursor.fetchall()
        #pprint.pprint(self.dBcursor.description)
        for columns in self.dBcursor.description:
            if str(columns[0]).upper() == str(column_name.upper()):
                self.log(f"Column {column_name.upper} exists in table {table_name}", "INFO")
                return True
        else:
            self.log(f"Column {column_name} does not exist in table {table_name}", "WARNING")
            return False
        
    def createColumn(self, column_name, table_name):
        query = f"ALTER TABLE {table_name} ADD {column_name} VARCHAR(255)"
        self.log(f"Creating column {column_name} in table {table_name}", "WARNING")
        self.dBcursor.execute(query)
        self.dB.commit()
        
    def checkIfPartNumberExistsInDb(self,part_number):
        query = f"SELECT TOP 1 * FROM Sklad WHERE {self.dict_of_translations['Výrobce partNumber']} = '{part_number}'"
        self.dBcursor.execute(query)
        result = self.dBcursor.fetchall()
        if len(result) == 0:
            return False
        else:
            return True

    def loadRowToDatabase(self,row):
        if self.checkIfPartNumberExistsInDb(self.table.item(row, self.getIndexFromColumnName("Výrobce partNumber")).text()): #ROW ALREADY EXISTS
            self.log(f"Part number {self.table.item(row, self.getIndexFromColumnName('Výrobce partNumber')).text()} already exists in database", "WARNING")
            #return
        else: #ROW DOESNT EXIST
            self.log(f"Part number {self.table.item(row, self.getIndexFromColumnName('Výrobce partNumber')).text()} does not exist in database", "INFO")
            query = f"INSERT INTO Sklad ("
            for column in range(self.table.columnCount()):
                if self.checkIfColumnIsStandartItem(column) == False:
                    continue
                query += f"{self.dict_of_translations[self.getColumnNameFromIndex(column)]},"

            query = query[:-1] + ",JakySklad, QRCODE) VALUES ("
            for column in range(self.table.columnCount()):
                if self.checkIfColumnIsStandartItem(column) == False:
                    continue
                
                if column == self.getIndexFromColumnName("Na skladě ČEVOR"):
                    query += f"{self.table.item(row, column).text()},"
                
                elif self.table.item(row, column) == None:
                    query += "NULL,"
                else:
                    query += f"'{self.table.item(row, column).text()}',"
            
            QRcode = f'QR_{self.table.item(row, self.getIndexFromColumnName("Výrobce partNumber")).text()}'
            query = query[:-1] + f", 'ELEKTRO', '{QRcode}')"

        self.log(f"QUERY: {query}", "DEBUG")
        self.dBcursor.execute(query)
        self.dB.commit()


    def loadDataFromTableToDatabase(self):
        self.log("Loading data from table to database", "DEBUG")
        number_of_columns = self.table.columnCount()
        for column in range(number_of_columns):
            if self.checkIfColumnIsStandartItem(column) == False:
                continue
            
            if self.checkIfColumnExists(self.dict_of_translations[self.getColumnNameFromIndex(column)], "Sklad") == False:
                self.createColumn(self.dict_of_translations[self.getColumnNameFromIndex(column)], "Sklad")
            
        for row in range(self.table.rowCount()):
            self.loadRowToDatabase(row)
        
    
from mouserResultPromptGUI import Ui_Form as mouserResultPromptGUI
class mouserResultPrompt(QtWidgets.QWidget):
    def __init__(self, number_of_results, *args, **kwargs):
        super().__init__(*args, **kwargs)
        log.log("Prompt was created", "SIGNAL")
        self.ui = mouserResultPromptGUI()
        self.ui.setupUi(self)
        self.ui.la_vysledky.setText(f"{number_of_results}")
        self.ui.pb_load.clicked.connect(self.accept)
        self.ui.pb_cancel.clicked.connect(self.reject)
        self.number_of_results = number_of_results

        if self.number_of_results < 50:
            self.ui.spin_nr_of_results.setMaximum(self.number_of_results)
        self.signals = signals()

    def accept(self):
        self.signals.signal_finished.emit(self.ui.spin_nr_of_results.value(),True)
        self.number_of_results = self.ui.spin_nr_of_results.value()
        self.close()
    
    def reject(self):
        self.number_of_results = 0
        self.signals.signal_finished.emit(0,False)
        self.close()

class ManufacturerLoader(QtWidgets.QWidget):
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        with open("config.yaml", "r") as f:
            self.yaml = yaml.safe_load(f)

        self.log = LOGGER("ALL").log
        self.path_to_images = self.yaml["PATH_TO_IMAGES"]
        self.ACCDB_connection = pyodbc.connect("Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + self.yaml["DATABASE"])
        self.ACCES = self.ACCDB_connection.cursor()
        do_not_create_table_flag = False
        self.prompt_is_running_flag = False
        self.databaseUpdater = loaderToDatabaseClass(self.ui.table_results,self.ACCDB_connection)
        try:
            with open("last_data.pkl", "rb") as f:
                self.json_response = pickle.load(f)
                pprint.pprint(self.json_response["Errors"])
        except:
            self.log("Initial file is missing","WARNING")
            do_not_create_table_flag = True

        if do_not_create_table_flag == False:
            self.createTableFromRequest(self.json_response)

        #self.parseResults(self.json_response)
        #self.createTableFromRequest(self.json_response)
        
        self.trials = 0
        self.clip = QtWidgets.QApplication.clipboard()
        self.ui.table_results.itemDoubleClicked.connect(self.OpenLink)
        self.ui.pb_search_single.clicked.connect(self.searchSinglePart)
        self.ui.che_add_overwrite.clicked.connect(self.addOverwrite)
        self.ui.pb_search_from_file.clicked.connect(self.notWorkingYet)
        self.ui.pb_load_to_database.clicked.connect(self.updateDatabase)
        
    def updateDatabase(self):
        self.databaseUpdater.loadDataFromTableToDatabase()
        self.createTableFromRequest(self.json_response)#update with new values
        

    def notWorkingYet(self):
        
        match self.trials:
            case 0:
                self.log("This function is not working yet","WARNING")
            case 1:
                self.log("Neklikej na mě debile!!","ERROR")
            case 2:
                self.log("Jsi debil?","ERROR")
            case 3:
                self.log("Ano jsi totálně omezená osoba","ERROR")
            case 4:
                self.log("Jasně klikni na mě víckrát to zabere!!", "ERROR")
            case 5:
                self.log("OUKEY TAK CO ti tak trochu zasekat počítač ?","ERROR")
            case 6:
                self.log("Poslední varování!!","ERROR")
            case 7:
                while True:
                    random_number = random.randint(0,110)
                    rnd_level = random.randint(0,6)
                    levels = ["CRITICAL","ERROR","WARNING","DEBUG","SIGNAL","HARDWARE","UNNECESSARY"]
                    rnd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=random_number))
                    self.log(f"{rnd}",levels[rnd_level])          
        self.trials += 1

    def addOverwrite(self):
        if self.ui.che_add_overwrite.isChecked():
            self.log("Results will be append to the table","WARNING")

        else:
            self.log("Results will overwrite table","WARNING")


    def checkIfPartIsInDatabase(self,partNumber):
        self.ACCES.execute(f"SELECT * FROM SKLAD WHERE [NAZEV] = '{partNumber}'")
        if self.ACCES.fetchone() is not None:
            self.log(f"Part {partNumber} is already in database","WARNING")
            return True
        else:
            return False

    def searchSinglePart(self):
        partNumber = self.ui.le_part_number.text()
        

        if self.ui.che_mouser.isChecked():
            self.log(f"MOUSER: Searching for part {partNumber} at remote server - this may take some time","INFO")
            if self.checkIfPartIsInDatabase(partNumber):
                self.log(f"Part {partNumber} is already in CEVOR database","WARNING")
            JSON_REQUEST_TEMPLATE["SearchByPartRequest"]["mouserPartNumber"] = partNumber
            self.json_response = requests.post(request_url, json= JSON_REQUEST_TEMPLATE).json()

        else:
            self.log(f"There is no manufacturer selected -> loading default values","WARNING")
            self.json_response = {}
        #self.parseResults(self.json_response)
        self.saveResultToPickle(self.json_response)
        self.createTableFromRequest(self.json_response)


    def saveResultToPickle(self,data):
        with open("last_data.pkl", "wb") as f:
            pickle.dump(data, f)

    def keyPressEvent(self, e):
        if (e.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
            if e.key() == QtCore.Qt.Key.Key_C: #copy
                data = self.getDataFromSelectedRange(self.ui.table_results.selectedRanges())
                self.clip.setText(data)

    def getDataFromSelectedRange(self, selection_ranges:List[QtWidgets.QTableWidgetSelectionRange]):
        data = ""
        list_of_rows = []
        list_of_columns = []
        for selection_range in selection_ranges:
            for rows in range(selection_range.topRow(), selection_range.bottomRow()+1):
                if rows not in list_of_rows:
                    list_of_rows.append(rows)
                    
            for columns in range(selection_range.leftColumn(), selection_range.rightColumn()+1):
                if columns not in list_of_columns:
                    list_of_columns.append(columns)
        
        #make header
        if self.ui.che_coppy_with_header.isChecked():
            for column in list_of_columns:
                if self.checkIfColumnIsStandartItem(column) == False:
                    continue
                data += self.ui.table_results.horizontalHeaderItem(column).text() + "\t"
            data += "\n"

        #Fill DAta
        for row in list_of_rows:
            #print(f"row: {row}")
            if self.ui.table_results.cellWidget(row, self.getIndexFromColumnName("Vybrat")).isChecked() == False:
                continue

            for column in list_of_columns:
                if self.checkIfColumnIsStandartItem(column) == False:
                    self.log(f"row: {row}, column: {column} -> this field is checkbox or picture -> ignore it!","INFO")
                    continue
                
                self.log(f"row: {row}, column: {column}, data:{self.ui.table_results.item(row, column).text()}","INFO")
                data += self.ui.table_results.item(row, column).text() + "\t"
            data += "\n"

        self.log("Successfully copied to the clipboard","DEBUG")
        return data


    def OpenLink(self,item:QtWidgets.QTableWidgetItem):
        if item.column() == self.getIndexFromColumnName("Datasheet") or item.column() == self.getIndexFromColumnName("Link"):
            webbrowser.open(self.ui.table_results.item(item.row(),item.column()).text())

        if item.column() == self.getIndexFromColumnName("Dodavatel partNumber"):
            webbrowser.open(self.ui.table_results.item(item.row(),self.getIndexFromColumnName("Link")).text())

    def getIndexFromColumnName(self,column_name):
        for columns in range(self.ui.table_results.columnCount()):
            if self.ui.table_results.horizontalHeaderItem(columns).text() == column_name:
                return columns
        else:
            return False	

    def getColumnNameFromIndex(self,column_index):
        return self.ui.table_results.horizontalHeaderItem(column_index).text()
    
    def _table_checkbox_clicked(self):
        checkbox:QtWidgets.QCheckBox = self.sender()

        if checkbox.isChecked() == True:
            if self.checkIfPartIsInDatabase(checkbox.partNumber):
                self.styleRow(checkbox.row, "blue")
            else:
                self.styleRow(checkbox.row, "green")

        elif checkbox.isChecked() == False:
            self.styleRow(checkbox.row, "red")


    def checkIfColumnIsStandartItem(self,column):
        if self.getColumnNameFromIndex(column) == "Vybrat" or self.getColumnNameFromIndex(column) == "Pict":
            return False
        else:
            return True

    def styleRow(self, row, style):
        for column in range(self.ui.table_results.columnCount()):
            #self.log(f"row: {row}, column: {column}, style: {style}","DEBUG")
            if self.checkIfColumnIsStandartItem(column) == False:
                continue

            if style == "red":
                self.ui.table_results.item(row, column).setBackground(QtGui.QColor(230, 180, 180))

            elif style == "green":
                self.ui.table_results.item(row, column).setBackground(QtGui.QColor(180, 230, 180))  

            elif style == "blue":
                self.ui.table_results.item(row, column).setBackground(QtGui.QColor(180, 180, 230))      

    @QtCore.pyqtSlot(int,bool)
    def continueWithSearch(self,number_of_results: int, status:bool):
        self.prompt_value = number_of_results
        self.prompt_is_running_flag = False
        self.createTableFromRequest(self.json_response,prompt_is_finished = True)
        
    def openPrompt(self, number_of_results:int):
        self.prompt_is_running_flag == True
        self.prompt = mouserResultPrompt(number_of_results)
        self.prompt.signals.signal_finished.connect(self.continueWithSearch)
        self.prompt.show()

    def createTableFromRequest(self,dict_from_json_request:dict, prompt_is_finished:bool = False):
        ##ERROR CHECKING########################################
        if self.ui.che_mouser.isChecked(): #check for mouser errors
            if len(dict_from_json_request["Errors"]) > 0:
                self.log(f"Error occured while searching for part, ERROR: {dict_from_json_request['Errors'][0]['Code']}\n if this is timeout error you can try it again","ERROR", oneline=False)
                return False
        

        ##LENGTH CHECKING#######################################
        if self.ui.che_mouser.isChecked(): #check for mouser number of results
            number_of_rows = dict_from_json_request["SearchResults"]['NumberOfResult']
        else:
            number_of_rows = 1 #default number of rows

        self.log(f"Received number of results: {number_of_rows}","INFO")
        if number_of_rows > 1 and self.ui.che_ignore_more_results.isChecked() == False: #multiple results are avaiable
            self.log("OPENING PROMPT","DEBUG")
            if prompt_is_finished == False:
                number_of_rows = self.openPrompt(number_of_rows)
                return
            else:
                number_of_rows = self.prompt_value

        elif number_of_rows > 1 and self.ui.che_ignore_more_results.isChecked() == True:#multiple results are avaiable but user wants to ignore it
            self.log(f"Search found {number_of_rows} results","INFO")
            
        if number_of_rows > 50:
            self.log(f"Search found {number_of_rows} results, but only first 50 will be added to the table","WARNING")
            number_of_rows = 50

        if number_of_rows == 0: #no results are avaiable
            self.log(f"Search found 0 results, nothing will be added to the table","WARNING")
            return False
        

        correction_index = 0
        if self.ui.che_add_overwrite.isChecked() == True: #ADD
            if self.ui.table_results.rowCount() == 0:
                loop_range = range(number_of_rows)
                self.ui.table_results.setRowCount(number_of_rows)
                
            else:
                correction_index = self.ui.table_results.rowCount()
                #self.log(f"loop_range: from:{self.ui.table_results.rowCount()} to: {self.ui.table_results.rowCount() + number_of_rows}", "CRITICAL")
                #self.log(f"loop_range with correction: from:{self.ui.table_results.rowCount() - correction_index} to: {self.ui.table_results.rowCount() + number_of_rows - correction_index}", "CRITICAL")
                loop_range = range(self.ui.table_results.rowCount(), self.ui.table_results.rowCount() + number_of_rows)
                
                self.ui.table_results.setRowCount(self.ui.table_results.rowCount() + number_of_rows)
                
            
        else: #OVERWRITE
            loop_range = range(number_of_rows)
            self.ui.table_results.setRowCount(number_of_rows)
        for rows in loop_range:
            for columns in range(self.ui.table_results.columnCount()):
                match self.ui.table_results.horizontalHeaderItem(columns).text():
                    case "Vybrat":
                        widget = QtWidgets.QCheckBox(text="Vybrat")
                        widget.clicked.connect(self._table_checkbox_clicked)
                        widget.setChecked(True)
                        widget.row = rows
                        if self.ui.che_mouser.isChecked() == True:
                            widget.partNumber = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['ManufacturerPartNumber']
                        else: #default
                            widget.partNumber = self.ui.le_part_number.text()

                        self.ui.table_results.setCellWidget(rows,columns,widget)
                        self.ui.table_results.cellWidget(rows,columns)

                    case "Dodavatel":                   
                        if self.ui.che_mouser.isChecked() == True:
                            data = "MOUSER"
                        else:
                            data = "DEFAULT"

                        self.createCellitem(rows,columns, data)
                        

                        
                    case "Dodavatel partNumber":
                        if self.ui.che_mouser.isChecked() == True:
                            data = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['MouserPartNumber']

                        else: #default
                            data = self.ui.le_part_number.text()

                        self.createCellitem(rows,columns, data)
    
                    case "Výrobce":
                        if self.ui.che_mouser.isChecked() == True:
                            data = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['Manufacturer']

                        else:
                            data = "DEFAULT"

                        self.createCellitem(rows,columns, data)
                        
                    case "Výrobce partNumber":
                        if self.ui.che_mouser.isChecked() == True:
                            data = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['ManufacturerPartNumber']

                        else:
                            data = self.ui.le_part_number.text()

                        self.createCellitem(rows,columns, data)
                        
                    case "Popis EN":
                        if self.ui.che_mouser.isChecked() == True:
                            data = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['Description']

                        else:
                            data = "DEFAULT"

                        self.createCellitem(rows,columns, data)
                        
                    case "Popis CZ":
                        if self.ui.che_mouser.isChecked() == True:
                            data = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['Description']

                        else:
                            data = "DEFAULT"

                        self.createCellitem(rows,columns, data)
                        
                    case "Na skladě dodavatel":
                        if self.ui.che_mouser.isChecked() == True:
                            data = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['AvailabilityInStock']

                        else:
                            data = "0"

                        self.createCellitem(rows,columns, data)
                        
                    case "Na skladě ČEVOR":
                        if self.ui.che_mouser.isChecked() == True:
                            if self.checkIfPartIsInDatabase(dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['ManufacturerPartNumber']) == True:
                                self.ACCES.execute(f"SELECT AktualniPocet FROM SKLAD WHERE NAZEV = '{dict_from_json_request['SearchResults']['Parts'][rows - correction_index]['ManufacturerPartNumber']}'")
                                data = str(self.ACCES.fetchone()[0])
                            else:
                                data = "0"
                        
                        else:
                            if self.checkIfPartIsInDatabase(self.ui.le_part_number.text() ) == True:
                                self.ACCES.execute(f"SELECT AktualniPocet FROM SKLAD WHERE NAZEV = '{self.ui.le_part_number.text()}'")
                                data = str(self.ACCES.fetchone()[0])
                            else:
                                data = "0"
                                
                        self.createCellitem(rows,columns, data)
                        
                    case "Factory Lead time":
                        if self.ui.che_mouser.isChecked() == True:
                            data = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['LeadTime']

                        else:
                            data = "DEFAULT"

                        self.createCellitem(rows,columns, data)
                        
                    case "Cena":
                        if self.ui.che_mouser.isChecked() == True:
                            if len(dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]["PriceBreaks"]) == 0:
                                data = "Neznámá"
                            else:
                                data = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]["PriceBreaks"][0]['Price']
                        else:
                            data = "DEFAULT"

                        self.createCellitem(rows,columns, data)


                    case "Pict":
                        url = None
                        if self.ui.che_mouser.isChecked() == True:
                            url = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['ImagePath']
                        #self.log(f"Image url: {url}", "INFO")
                        if url == None:
                            picture_safe_path = f'{self.path_to_images}/default.jpg'
                            self.log(f"Part has no image URL: loading default image -> Je to fešák", "INFO")

                        else:
                            image_extension = url.split(".")[-1]
                            pict_name = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]["MouserPartNumber"]
                            pict_name = str(pict_name).replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_").replace("*", "_").replace("?", "_").replace("\"", "_").replace("<", "_").replace(">", "_").replace("|", "_")
                            picture_safe_path = f'{self.path_to_images}/{pict_name}.{image_extension}'

                        if os.path.exists(picture_safe_path) == False and url != None:
                            self.log(f"Downloading image: {url}", "INFO")
                            request = urllib.request.urlopen(url = url, timeout=5)
                            with open(picture_safe_path, 'wb') as f:
                                try:
                                    f.write(request.read())
                                except:
                                    self.log(f"Error while downloading image: {url}", "CRITICAL")
                                    picture_safe_path = f'{self.path_to_images}/default.jpg'
                            #urllib.request.urlretrieve(url, f'{dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]["MouserPartNumber"]}.{image_extension}')
                        else:
                            self.log(f"Image was already downloaded and is located here: {picture_safe_path}", "WARNING")

                        widget = pictureLabelWidget(picture_safe_path)
                        self.ui.table_results.setCellWidget(rows,columns,widget)
                        self.ui.table_results.cellWidget(rows,columns)
                    case "Ceník":
                        if self.ui.che_mouser.isChecked() == True:
                            cena_str = ""
                            for cena in dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]["PriceBreaks"]:
                                cena_str += f"{cena['Quantity']}ks: {cena['Price']} | "

                        else:
                            cena_str = "DEFAULT"

                        self.createCellitem(rows,columns, cena_str)
                        
                    case "Datasheet":
                        if self.ui.che_mouser.isChecked() == True:
                            data = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['DataSheetUrl']

                        else:
                            data = "DEFAULT"

                        self.createCellitem(rows,columns, data)


                    case "Link":
                        if self.ui.che_mouser.isChecked() == True:
                            data = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['ProductDetailUrl']
                        
                        else:
                            data = "DEFAULT"

                        self.createCellitem(rows,columns, data)

            if self.ui.che_mouser.isChecked() == True:
                if self.checkIfPartIsInDatabase(dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['ManufacturerPartNumber']) == True:
                    self.styleRow(rows, "blue")
                else:
                    self.styleRow(rows, "green")

            else:
                self.styleRow(rows, "green")

            self.log(f"Add row: {rows+1} data link: {data}", "INFO")
            #pprint.pprint(dict_from_json_request["SearchResults"]["Parts"][rows])
        self.ui.table_results.resizeColumnsToContents()
        self.ui.table_results.update()
        self.ui.table_results.repaint()

                

            

    def createCellitem(self,row,columns, text):
        item = QtWidgets.QTableWidgetItem(text)
        self.ui.table_results.setItem(row,columns,item)
        if text == None or self.checkIfColumnIsStandartItem(columns) == False:
            return
        
        if "http" in text:
            item.setForeground(QtGui.QColor(0,0,255))

        if self.getIndexFromColumnName("Dodavatel partNumber") == columns:
            item.setForeground(QtGui.QColor(0,0,255))
    

    def getIndexOfColumnByName(self,column_name):
        for columns in range(self.ui.table_results.columnCount()):
            if self.ui.table_results.horizontalHeaderItem(columns).text() == column_name:
                return columns
        else:
            return False
        

    def parseResults(self,dict_from_json_request):
        #pprint.pprint(dict_from_json_request)
        number_of_rows = dict_from_json_request["SearchResults"]['NumberOfResult']
        result:dict
        if number_of_rows > 50:
            number_of_rows = 50
        for result in range(number_of_rows):
            self.part_data = dict_from_json_request["SearchResults"]["Parts"][result]
            self.Nazev_dodavatele = "MOUSER"
            self.Skladem_dodavatel = self.part_data['AvailabilityInStock']
            if len(self.part_data["AvailabilityOnOrder"]) > 0:
                self.Datum_naskladneni_dodavatel = f'{self.part_data["AvailabilityOnOrder"][0]["Quantity"]} : {self.part_data["AvailabilityOnOrder"][0]["Date"]}'  
            else:
                self.Datum_naskladneni_dodavatel = "NEZNÁMÝ"

            self.factory_lead_time = self.part_data['LeadTime']
            self.PartNumber_dodavatel = self.part_data['MouserPartNumber']
            self.Vyrobce_dodavatel = self.part_data['Manufacturer']
            self.POPISEN_dodavatel = self.part_data['Description']
            self.Datasheet_dodavatel = self.part_data['DataSheetUrl']
            self.partNumber = self.part_data['ManufacturerPartNumber']
            self.Odkaz_Pict_dodavatel = self.part_data['ImagePath']
            self.Odkaz_dodavatel = self.part_data["ProductDetailUrl"]
            cena_str = ""
            for ceny in self.part_data["PriceBreaks"]:
                cena_str += f"{ceny['Quantity']}ks: {ceny['Price']}; "
            self.Cena_dodavatel_multiple = cena_str
            self.Cena_dodavatel = self.part_data["PriceBreaks"][0]['Price']
            self.log(f"PART {result}","WARNING")
            self.printResults()


    def printResults(self):
            
        self.log(f"Nazev_dodavatele: {self.Nazev_dodavatele}","WARNING")
        self.log(f"partNumber: {self.partNumber}","DEBUG")
        self.log(f"PartNumber_dodavatel: {self.PartNumber_dodavatel}","INFO")
        self.log(f"POPISEN_dodavatel: {self.POPISEN_dodavatel}","INFO")
        self.log(f"Skladem_dodavatel: {self.Skladem_dodavatel}","CRITICAL")
        self.log(f"Datum_naskladneni_dodavatel: {self.Datum_naskladneni_dodavatel}","INFO")
        self.log(f"factory_lead_time: {self.factory_lead_time}","INFO")
        self.log(f"Cena_dodavatel:{self.Cena_dodavatel}","SIGNAL")
        self.log(f"Cena_dodavatel_multiple:{self.Cena_dodavatel_multiple}","INFO", oneline=False)
        self.log(f"Vyrobce: {self.Vyrobce_dodavatel}","INFO")
        self.log(f"Odkaz_dodavatel: {self.Odkaz_dodavatel}","HARDWARE")
        self.log(f"Datasheet_dodavatel: {self.Datasheet_dodavatel}","HARDWARE")


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = ManufacturerLoader()
    window.setWindowTitle("Test")
    #window.resize(500, 500)
    window.show()
    app.exec()
