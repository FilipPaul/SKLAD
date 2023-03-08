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
import string

class ManufacturerLoader(QtWidgets.QWidget):
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        with open("config.yaml", "r") as f:
            self.yaml = yaml.safe_load(f)

        self.log = LOGGER("ALL").log
        self.ACCDB_connection = pyodbc.connect("Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + self.yaml["DATABASE"])
        self.ACCES = self.ACCDB_connection.cursor()
        do_not_create_table_flag = False
        try:
            with open("last_data.pkl", "rb") as f:
                self.json_response = pickle.load(f)
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
        self.ui.pb_load_to_database.clicked.connect(self.notWorkingYet)


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
        self.log(f"Searching for part {partNumber} at remote server - this may take some time","INFO")
        if self.checkIfPartIsInDatabase(partNumber):
            self.log(f"Part {partNumber} is already in CEVOR database","WARNING")
        JSON_REQUEST_TEMPLATE["SearchByPartRequest"]["mouserPartNumber"] = partNumber
        self.json_response = requests.post(request_url, json= JSON_REQUEST_TEMPLATE).json()
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
        for column in list_of_columns:
            if column == self.getIndexFromColumnName("Vybrat"):
                continue
            data += self.ui.table_results.horizontalHeaderItem(column).text() + "\t"
        data += "\n"

        #Fill DAta
        for row in list_of_rows:
            #print(f"row: {row}")
            if self.ui.table_results.cellWidget(row, self.getIndexFromColumnName("Vybrat")).isChecked() == False:
                continue

            for column in list_of_columns:
                self.log(f"row: {row}, column: {column}, data:{self.ui.table_results.item(row, column).text()}","INFO")
                if column == self.getIndexFromColumnName("Vybrat"):
                    continue
                data += self.ui.table_results.item(row, column).text() + "\t"
            data += "\n"

        self.log("Succesfully coppied to the clipboard","DEBUG")
        return data


    def OpenLink(self,item:QtWidgets.QTableWidgetItem):
        if item.column() == self.getIndexFromColumnName("Datasheet") or item.column() == self.getIndexFromColumnName("Link"):
            webbrowser.open(self.ui.table_results.item(item.row(),item.column()).text())

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



    def styleRow(self, row, style):
        for column in range(self.ui.table_results.columnCount()):
            if self.getColumnNameFromIndex(column) == "Vybrat":
                continue

            if style == "red":
                self.ui.table_results.item(row, column).setBackground(QtGui.QColor(230, 180, 180))

            elif style == "green":
                self.ui.table_results.item(row, column).setBackground(QtGui.QColor(180, 230, 180))  

            elif style == "blue":
                self.ui.table_results.item(row, column).setBackground(QtGui.QColor(180, 180, 230))      

    def createTableFromRequest(self,dict_from_json_request:dict):
        if len(dict_from_json_request["Errors"]) > 0:
            self.log(f"Error occured while searching for part, ERROR: {dict_from_json_request['Errors'][0]['Code']}\n if this is timeout error you can try it again","ERROR", oneline=False)
            return False
        
        number_of_rows = dict_from_json_request["SearchResults"]['NumberOfResult']
        self.log(f"Received number of results: {number_of_rows}","INFO")
        if number_of_rows > 50:
            self.log(f"Search found {number_of_rows} results, but 50 will be added to the table !!: {number_of_rows}","WARNING")
            number_of_rows = 50

        if number_of_rows == 0:
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
                        widget.partNumber = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['ManufacturerPartNumber']
                        self.ui.table_results.setCellWidget(rows,columns,widget)
                        self.ui.table_results.cellWidget(rows,columns)
                        
                    case "Dodavatel":
                        self.createCellitem(rows,columns, "MOUSER")
                        
                    case "Dodavatel partNumber":
                        data = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['MouserPartNumber']
                        self.createCellitem(rows,columns, data)
    
                    case "Výrobce":
                        data = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['Manufacturer']
                        self.createCellitem(rows,columns, data)
                        
                    case "Výrobce partNumber":
                        data = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['ManufacturerPartNumber']
                        self.createCellitem(rows,columns, data)
                        
                    case "Popis EN":
                        data = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['Description']
                        self.createCellitem(rows,columns, data)
                        
                    case "Popis CZ":
                        data = "načíst z DB"
                        self.createCellitem(rows,columns, data)
                        
                    case "Na skladě dodavatel":
                        data = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['AvailabilityInStock']
                        self.createCellitem(rows,columns, data)
                        
                    case "Na skladě ČEVOR":
                        if self.checkIfPartIsInDatabase(dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['ManufacturerPartNumber']) == True:
                            self.ACCES.execute(f"SELECT AktualniPocet FROM SKLAD WHERE NAZEV = '{dict_from_json_request['SearchResults']['Parts'][rows - correction_index]['ManufacturerPartNumber']}'")
                            data = str(self.ACCES.fetchone()[0])
                        else:
                            data = "0"

                        self.createCellitem(rows,columns, data)
                        
                    case "Factory Lead time":
                        data = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['LeadTime']
                        self.createCellitem(rows,columns, data)
                        
                    case "Cena":
                        data = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]["PriceBreaks"][0]['Price']
                        self.createCellitem(rows,columns, data)
                        
                    case "Ceník":
                        cena_str = ""
                        for cena in dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]["PriceBreaks"]:
                            cena_str += f"{cena['Quantity']}ks: {cena['Price']} | "
                        self.createCellitem(rows,columns, cena_str)
                        
                    case "Datasheet":
                        data = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['DataSheetUrl']
                        self.createCellitem(rows,columns, data)

                    case "Link":
                        data = dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['ProductDetailUrl']
                        self.createCellitem(rows,columns, data)

            if self.checkIfPartIsInDatabase(dict_from_json_request["SearchResults"]["Parts"][rows - correction_index]['ManufacturerPartNumber']) == True:
                self.styleRow(rows, "blue")
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
        if "http" in text:
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
            self.Odkaz_obrazek_dodavatel = self.part_data['ImagePath']
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
