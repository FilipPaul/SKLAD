
from AutomateSuperPackage.AutomateSuperModule import SuperClass
import yaml

class LoTGenerator():
    def __init__(self,config_file_path = "config.yaml") -> None:
        
        with open(config_file_path, 'r') as f:
            self.YAML = yaml.safe_load(f)

        self.ACCES = SuperClass().database.AccesDatabase
        self.ACCES.multipleCursors([self.YAML["DATABASE"]])
        self.ACCES.WriteQuery("SELECT Zakazka from Zakazky ORDER BY ID ASC")
        result = self.ACCES.ResultFromQuery()

        list_of_lots = []
        for rows in result:
            list_of_lots.append(rows[0])

        print(list_of_lots)

        for lot in list_of_lots:
            if self.tableAlreadyExists(self.ACCES,lot,0):
                ...
            else:
                self.coppyQueryIntoNewTable("SELECT * FROM LOT_SABLONA","LOT_SABLONA",0,f"[{lot}]",0,"ID")
                self.ACCES.WriteQuery(f"ALTER TABLE [{lot}] ADD FOREIGN KEY (refSkladID) REFERENCES Sklad(ID)")
            
        self.ACCES.UpdateDatabase()




    def tableAlreadyExists(self,ACDB,table,cursor_index):
        for rows in ACDB.cursors[cursor_index].tables():
            if rows[2] == table:
                return 1 #table already exists
        return 0 #Table doesnt exists



    def WriteAndReadQUery(self,query,cursor_index = 0):
        self.ACCES.MultipleWriteQuery(query, cursor_index)
        result = self.ACCES.MultipleResultFromQuery(cursor_index)
        return result


    def getQueryContent(self,query, cursor_index):
            dict_of_columns = {}
            self.ACCES.MultipleWriteQuery(query,[cursor_index])
            description = self.ACCES.cursors[cursor_index].description
            result = self.ACCES.MultipleResultFromQuery([cursor_index])
            for rows in description:
                dict_of_columns[rows[0]] = []

            for rows in result:
                i = 0
                for columns in rows:
                    if str(description[i][1]) == "<class 'int'>" and columns != None:
                        dict_of_columns[description[i][0]].append(str(columns))
                    
                    elif str(description[i][1]) == "<class 'datetime.datetime'>" and columns != None:
                        dict_of_columns[description[i][0]].append( "#"  + str(columns) + "#")

                    elif str(description[i][1]) == "<class 'str'>" and columns != None:
                        columns = str(columns).replace("'","''")
                        dict_of_columns[description[i][0]].append( "'"  + str(columns) + "'")

                    elif str(description[i][1]) == "<class 'decimal.Decimal'>" and columns != None:
                        dict_of_columns[description[i][0]].append( str(columns))
                    
                    elif str(description[i][1]) == "<class 'float'>" and columns != None:
                        dict_of_columns[description[i][0]].append( str(columns))
                    
                    elif str(description[i][1]) == "<class 'int'>" and columns != None:
                        dict_of_columns[description[i][0]].append(str(columns))

                    elif str(description[i][1]) == "<class 'bool'>" and columns != None:
                        if columns == True:
                            dict_of_columns[description[i][0]].append("True")
                        else:
                            dict_of_columns[description[i][0]].append("False")

                    elif columns == None:
                        dict_of_columns[description[i][0]].append( "NULL")
                    
                    else:
                        dict_of_columns[description[i][0]].append( "'"  + str(columns) + "'")

                    i += 1
            return dict_of_columns

    def getTableContent(self,table,cursor_index):
            """retunr dictionary, where key corresponds to the name of column and value coresponds to the datatype"""
            #GET INFO ABOUT TABLE
            column_name_types_dict= {}
            for row in self.ACCES.cursors[cursor_index].columns(table = table):
                if row.type_name == "VARCHAR":
                    column_name_types_dict[row.column_name] =  str(row.type_name) + "(" +str( row.column_size) + ")"
                else:
                    column_name_types_dict[row.column_name] =  row.type_name
            return column_name_types_dict

    def coppyQueryIntoNewTable(self,query,from_table,from_table_index,to_table,to_table_index,key):
            print(f"query is {query}")
            dict_of_columns = self.getTableContent(from_table,from_table_index)
            #Create Query string for table creation:
            SQL_string = f"CREATE TABLE {to_table} ("
            for keys in dict_of_columns:
                SQL_string += str(keys) + " "  + str(dict_of_columns[keys]) + ","
            SQL_string = SQL_string[:-1] + ")" #remove last Comma and add bracket (

            #First check if table exists:
            if self.tableAlreadyExists(self.ACCES,to_table, to_table_index) == True:
                self.ACCES.MultipleWriteQuery("DROP TABLE " + to_table ,[to_table_index])    #delete table first

            self.ACCES.MultipleWriteQuery(SQL_string,[to_table_index]) #create new table from SQL string

            #NOW change autonumbering of ID (must be unique in original table) -> from ooriginal table !
            #if from_table == "FA":
            #    MAX_ID_FROM_FA = WriteAndReadQUery("SELECT TOP 1 RelAgID FROM pUD ORDER BY RelAgID DESC",[from_table_index])

            #else:
            MAX_ID_FROM_FA = self.WriteAndReadQUery("SELECT TOP 1 "+ str(key) +" FROM " + from_table+ " ORDER BY "+ str(key) +" DESC",[from_table_index])

            self.ACCES.MultipleWriteQuery("ALTER TABLE " + to_table + " ALTER COLUMN "+ str(key) +" AUTOINCREMENT("+ str(int(1) + 1) + ",1)",[to_table_index])

            #Now take a coppy of FA original table and place it into the FAcopy:
            result_dict = self.getQueryContent(query,from_table_index)
            list_of_old_keys = result_dict[key]

            #Create SQL_query from result_dict-> for each rows the headers (columns) will remain same, therefore first create only columns and than loop through rows
            SQL_string_for_columns = f"INSERT INTO {to_table} ("
            for keys in result_dict:  #keys are columns and each column has a list of data which represents data from rows
                if keys == key: #in order to have autonumbering ignore ID and let ms self.ACCES to auto number
                    ...
                else:
                    SQL_string_for_columns +=  keys + ","

            SQL_string_for_columns = SQL_string_for_columns[:-1] + ") VALUES ("


            #FOR number of rows from query create second (data) part of SQL string
            for i in range(0,len(result_dict[str(key)])):
                SQL_string = SQL_string_for_columns
                for keys in result_dict:  #keys are columns and each column has a list of data which represents data from rows
                    if keys == "ID": #in order to have autonumbering ignore ID and let ms self.ACCES to auto number
                        ...
                    else:
                        SQL_string +=  result_dict[keys][i] + ","
                self.ACCES.MultipleUpdateDatabase([to_table_index])  #update table
                SQL_string = SQL_string[:-1] + ")"
                self.ACCES.MultipleWriteQuery(SQL_string,[to_table_index]) #create new table from SQL string

            list_of_new_keys = []
            result = self.WriteAndReadQUery("SELECT "+ key +" FROM " + to_table, [to_table_index])
            for rows in result:
                list_of_new_keys.append(rows[0])

            self.ACCES.MultipleUpdateDatabase([to_table_index])  #update table
            return 1,list_of_old_keys,list_of_new_keys

