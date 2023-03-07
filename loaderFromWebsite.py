import requests
import pickle
from logger import LOGGER
log = LOGGER("ALL")
from pprint import pprint as p

#MOUSER_SEARCH_API_KEY = "234ba5f6-eb12-4020-a50f-ef56390e0e1f" #MOUSER
#partNumber = "STM32F479VGT6"
#request_url = f"https://api.mouser.com/api/v2/search/partnumber?apiKey={MOUSER_SEARCH_API_KEY}"
#
#JSON_REQUEST_TEMPLATE = {
#  "SearchByPartRequest": {
#    "mouserPartNumber": "PARTNUMBER",
#    "partSearchOptions": "string"
#  }
#}
#
#JSON_REQUEST_TEMPLATE["SearchByPartRequest"]["mouserPartNumber"] = partNumber
#
#r = requests.post(request_url, json= JSON_REQUEST_TEMPLATE)
#print(f"Status Code: {r.status_code}, Response:\n\n{r.json()}")
#with open("mouser.pickle", "wb") as f:
#    pickle.dump(r.json(), f)


with open("mouser.pickle", "rb") as f:
    json_response = pickle.load(f)

result:dict
for result in range(json_response["SearchResults"]['NumberOfResult']):
    p(json_response["SearchResults"]["Parts"][result])
    print(type(json_response["SearchResults"]["Parts"][result]))

    part_data = json_response["SearchResults"]["Parts"][result]
    Nazev_dodavatele = "MOUSER"
    Skladem_dodavatel = part_data['AvailabilityInStock']
    datum_naskladneni_str = f'{part_data["AvailabilityOnOrder"][0]["Quantity"]} : {part_data["AvailabilityOnOrder"][0]["Date"]}'  
    Datum_naskladneni_dodavatel = part_data["AvailabilityOnOrder"]
    PartNumber_dodavatel = part_data['ManufacturerPartNumber']
    Vyrobce_dodavatel = part_data['Manufacturer']
    POPISEN_dodavatel = part_data['Description']
    Datasheet_dodavatel = part_data['DataSheetUrl']
    partNumber = part_data['ManufacturerPartNumber']
    Odkaz_obrazek_dodavatel = part_data['ImagePath']
    Odkaz_dodavatel = part_data["ProductDetailUrl"]
    cena_str = ""
    for ceny in part_data["PriceBreaks"]:
        cena_str += f"{ceny['Quantity']}ks: {ceny['Price']}; "
    Cena_dodavatel_multiple = cena_str
    Cena_dodavatel = part_data["PriceBreaks"][0]['Price']

    
    log.log(f"Nazev_dodavatele: {Nazev_dodavatele}","WARNING")
    log.log(f"partNumber: {partNumber}","DEBUG")
    log.log(f"PartNumber_dodavatel: {PartNumber_dodavatel}","INFO")
    log.log(f"POPISEN_dodavatel: {POPISEN_dodavatel}","INFO")
    log.log(f"Skladem_dodavatel: {Skladem_dodavatel}","CRITICAL")
    log.log(f"Datum_naskladneni_dodavatel: {Datum_naskladneni_dodavatel}","INFO")
    log.log(f"Cena_dodavatel:{Cena_dodavatel}","SIGNAL")
    log.log(f"Cena_dodavatel_multiple:{Cena_dodavatel_multiple}","INFO", oneline=False)
    log.log(f"Vyrobce: {Vyrobce_dodavatel}","INFO")
    log.log(f"Odkaz_dodavatel: {Odkaz_dodavatel}","HARDWARE")
    log.log(f"Datasheet_dodavatel: {Datasheet_dodavatel}","HARDWARE")


