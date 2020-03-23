print("starting script download_tagesthemen.py")

import requests
from bs4 import BeautifulSoup

def get_tagesthemen_download_link_date():
    # link = "https://www.tagesschau.de/sendung/tagesschau/index.html"
    link = "https://www.tagesschau.de/sendung/tagesthemen/index.html"
    
    r = requests.get(link)
    soup = BeautifulSoup(r.text, "html.parser")
    button = soup.find_all('div', {'class': "button"})[0]
    button_text = str(button)
    begin_link = button_text.find("//download.media.tagesschau.de/video")
    end_link = button_text.find(".mp4") + len(".mp4")

    link = "http:" + button_text[begin_link:end_link]

    begin_date = link.find("TV-20") + len("TV-")
    date = link[begin_date:(begin_date+8)]
        
    return({"link" : link, "date": date})


def download_mp4(link, date):
    r = requests.get(link)

    with open('./videos/' + date + 'tagesthemen.mp4', 'wb') as f:  
        f.write(r.content)    

if __name__ =="__main__":
    info = get_tagesthemen_download_link_date()

    download_mp4(**info)