import qrcode
from AutomateSuperPackage.AutomateSuperModule import SuperClass
import subprocess
import os
import latex_text_to_generate_QR

import yaml

class QRcodeGenerator():
    def __init__(self,config_file_path = "config.yaml") -> None:
        with open(config_file_path, 'r') as f:
            self.YAML = yaml.safe_load(f)

        path = self.YAML["OUTPUT_DIR"]
        # Check whether the specified path exists or not
        isExist = os.path.exists(path)
        if not isExist:
        # Create a new directory because it does not exist 
            os.makedirs(path)
            print("The new directory is created!")


        query_QR = self.YAML["QUERY_FOR_PRINT_QR"]
        query_LOT = self.YAML["QUERY_FOR_PRINT_LOT"]

        self.ACCES = SuperClass().database.AccesDatabase
        self.ACCES.SimplyConnectByPath(self.YAML["DATABASE"])

        list_of_qr_codes,list_of_names,list_of_descriptions = self.generateSkladCodes(query_QR)
        self.createLatexSkladQR(list_of_descriptions=list_of_descriptions,list_of_names=list_of_names,list_of_qr_codes=list_of_qr_codes,path=path,output_file_name="sklad_qr")

        list_of_qr_codes,list_of_names, list_of_descriptions = self.generateLotCodes(query_LOT)
        self.createLatexLotQR(list_of_descriptions= list_of_descriptions,list_of_names=list_of_names,list_of_qr_codes=list_of_qr_codes,path=path,output_file_name="lot")

    def createLatexSkladQR(self,list_of_qr_codes,list_of_names,list_of_descriptions,path,output_file_name):
        latex_final_str = latex_text_to_generate_QR.latex_text
        latex_sablona = R"\begin{minipage}[c][2.9cm][c]{1.5cm}\includegraphics[height = 1.5cm]{QRPATH}\end{minipage}\begin{minipage}[c][2.9cm][c]{4.7cm}\normalsize\textbf{POPIS}\\\small NÁZEV\end{minipage}\hspace{0.1cm}" + "\n"


        qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
        )

        for index,QRcode in enumerate(list_of_qr_codes):
            qr.clear()
            qr.add_data(QRcode)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
            QRcode = QRcode.replace('\\','_').replace("/","_")
            print(QRcode)
            img.save(f"QR_codes/{QRcode}.png")
            latex_final_str += latex_sablona.replace("QRPATH", f"../QR_codes/{QRcode}.png").replace("NÁZEV", list_of_names[index]).replace("POPIS", list_of_descriptions[index])


        latex_final_str += latex_text_to_generate_QR.latex_end_text

        print(latex_final_str)


        with open(Rf"{path}/{output_file_name}.tex", "w", encoding="utf-8") as f:
            f.write(latex_final_str)
            f.close()

        cmd = ['pdflatex', '-interaction', 'nonstopmode', f'{output_file_name}.tex']
        proc = subprocess.Popen( cmd, cwd= f"{path}")
        proc.communicate()
            
        retcode = proc.returncode
        print(f"RETURNCODE: {retcode}")
        if not retcode == 0:
            os.unlink(f"output_tex/{output_file_name}.tex")
            raise ValueError('Error {} executing command: {}'.format(retcode, ' '.join(cmd))) 

        os.unlink(f"output_tex/{output_file_name}.tex")
        os.unlink(f"output_tex/{output_file_name}.log")
        os.startfile(Rf"{path}\{output_file_name}.pdf")
        #subprocess.Popen(["output_tex/generated_tex_file.pdf"],shell=True)

    def createLatexLotQR(self,list_of_qr_codes,list_of_names,list_of_descriptions,path,output_file_name):
        latex_final_str = latex_text_to_generate_QR.latex_text
        latex_sablona = R"\begin{minipage}[c][2.9cm][c]{1.5cm}\includegraphics[height = 1.5cm]{QRPATH}\end{minipage}\begin{minipage}[c][2.9cm][c]{4.7cm}\normalsize\textbf{NÁZEV}\\\small POPIS\end{minipage}\hspace{0.1cm}" + "\n"
        qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
        )

        print("LIST OF QR CODES:",list_of_qr_codes)
        for index,QRcode in enumerate(list_of_qr_codes):
            qr.clear()
            qr.add_data(QRcode)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
            img.save(f"QR_codes/{QRcode.replace('/','_')}.png")
            latex_final_str += latex_sablona.replace("QRPATH", f"../QR_codes/{QRcode.replace('/','_')}.png").replace("NÁZEV", list_of_names[index].replace("_",R"\_")).replace("POPIS", list_of_descriptions[index])


        latex_final_str += latex_text_to_generate_QR.latex_end_text

        print(latex_final_str)


        with open(Rf"{path}/{output_file_name}.tex", "w", encoding="utf-8") as f:
            f.write(latex_final_str)
            f.close()

        cmd = ['pdflatex', '-interaction', 'nonstopmode', f'{output_file_name}.tex']
        proc = subprocess.Popen( cmd, cwd= f"{path}")
        proc.communicate()
            
        retcode = proc.returncode
        print(f"RETURNCODE: {retcode}")
        if not retcode == 0:
            os.unlink(f"output_tex/{output_file_name}.tex")
            raise ValueError('Error {} executing command: {}'.format(retcode, ' '.join(cmd))) 

        os.unlink(f"output_tex/{output_file_name}.tex")
        os.unlink(f"output_tex/{output_file_name}.log")
        os.startfile(Rf"{path}\{output_file_name}.pdf")
        #subprocess.Popen(["output_tex/generated_tex_file.pdf"],shell=True)

    def generateSkladCodes(self,query):
        ################ SKLAD QR GENERATING ##################

        list_of_qr_codes = []
        list_of_names = []
        list_of_descriptions = []
        self.ACCES.WriteQuery(query)
        result = self.ACCES.ResultFromQuery()
        for rows in result:

            if rows[0] == None:
                rows[0]= "NEZADÁN"
            
            if rows[1] == None:
                rows[1] = "NEZADÁN"

            if rows[2] == None:
                rows[2] = "NEZADÁN"

            list_of_qr_codes.append(rows[0])
            list_of_names.append(rows[1])
            list_of_descriptions.append(rows[2])

        return list_of_qr_codes,list_of_names,list_of_descriptions

    def generateLotCodes(self,query):### SKLAD QR GENERATING ##################

        list_of_qr_codes = []
        list_of_names = []
        list_of_descriptions = []
        self.ACCES.WriteQuery(query)
        result = self.ACCES.ResultFromQuery()
        for rows in result:
            list_of_qr_codes.append(rows[0])
            list_of_names.append(rows[0])
            list_of_descriptions.append(rows[1])

        return list_of_qr_codes,list_of_qr_codes,list_of_descriptions

