import requests
from bs4 import BeautifulSoup
import pandas as pd

url = "https://urnik.fmf.uni-lj.si"
urniki = []
stevec = 1
zaporedni_mankajoči = 0
vsi_podatki = []

while True:
  if zaporedni_mankajoči == 5:
    break

  stran_z_povezavami = url + "/" + str(stevec)
  stevec += 1
  response = requests.get(stran_z_povezavami)
  soup = BeautifulSoup(response.text, "html.parser")
  # print(stevec)

  if response.status_code == 404:
    # print("Tega urnika ni.")
    zaporedni_mankajoči += 1

  else:
    zaporedni_mankajoči = 0
  
    vzorcni_urnik = url + soup.select_one(".padded a")["href"]
    # print(vzorcni_urnik)
    response2 = requests.get(vzorcni_urnik)
    soup2 = BeautifulSoup(response2.text, "html.parser")

    obdobje = soup2.select_one("#timetable-logo span").get_text(strip=True)[1:-1]
    if "izpitno obdobje" in  obdobje:
      continue
    print(obdobje)

    for kvadratek in soup.select(".m6 .collapsible"):
      program = kvadratek.select_one(".collapsible-header").get_text(strip=True)

      for povezava in kvadratek.select("a"):
        link = povezava["href"]
        if "Poletni" in obdobje:
          link = link[:-1] + "8"
        urniki.append({
          "semester" : obdobje,
          "program" : program,
          "letnik" : povezava.get_text(strip=True),
          "url" : povezava["href"][:-1] + "8"
        })
        # print(povezava["href"][:-1] + "8")

    ure = {}
    teden = {
      0 : "ponedeljek",
      1 : "torek",
      2 : "sreda",
      3 : "četrtek",
      4 : "petek",
      5 : "sobota",
      6 : "nedelja"
    }

    for urnik in urniki:
      response = requests.get(url + urnik["url"])
      soup = BeautifulSoup(response.text, "html.parser")
      prostori_s_predmeti = soup.select(".entry-absolute-box")

      mesta = soup.select(".hour")
      for ura in mesta:
        procent = float(ura.get("style").split(":")[1].strip().replace("%", ""))
        cas = ura.get_text(strip=True)

        if cas:
          ure[procent] = int(cas)

      for prostor in prostori_s_predmeti:
        # print (prostor.get("style"))
        if "!important" in prostor.select_one(".entry").get("style"):
          continue
        predmet = prostor.select_one(".subject").get_text(strip=True)
        vrsta_ucenja = prostor.select_one(".entry-type").get_text(strip=True)

        izvajalci = [oseba.get("title") for oseba in prostor.select(".teacher a")]
        profesor = None if not izvajalci or izvajalci[0] in ["X", "rezervacija kolokvij", "? ?"] else izvajalci

        ucilnica = prostor.select_one(".classroom")
        predavalnica = ucilnica.get_text(strip=True) if ucilnica else None

        kljuc = round(100 - float(prostor.get("style").split("top:")[1].split("%")[0].strip()), 2)
        ura_zacetka = ure[kljuc]
        trajanje = round(float(prostor.get("style").split("height:")[1].split("%")[0].strip()) / 7.69)
        dan = teden[float(prostor.get("style").split("left:")[1].split("%")[0].strip()) // 20]

        # print(predmet, vrsta_ucenja, profesor, predavalnica, ura_zacetka, trajanje, dan)
        vsi_podatki.append({
          "semester" : urnik["semester"],
          "program" : urnik["program"],
          "letnik" : urnik["letnik"],
          "predmet" : predmet,
          "zacetek" : ura_zacetka,
          "trajanje" : trajanje,
          "dan" : dan,
          "vrsta" : vrsta_ucenja,
          "predavalnica" : predavalnica,
          "predavatelj" : izvajalci
        })
      print(len(vsi_podatki))
    
    print("Končan semester.")

df = pd.DataFrame(vsi_podatki)

print(df)
print("konec")
