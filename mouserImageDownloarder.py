
import urllib.request
from PIL import Image
  
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




url = "https://www.mouser.com/images/stmicroelectronics/images/NUCLEO-U575ZI-Q_SPL.jpg"

request = urllib.request.urlopen(url, timeout=5)
with open("filename.jpg", 'wb') as f:
    try:
        f.write(request.read())
    except:
        print("error")

img = Image.open("filename.jpg")
img.show()