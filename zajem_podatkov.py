import requests
from bs4 import BeautifulSoup
import pandas as pd

GLAVA = {
  "User-Agent": "Urnik-Bot"
}

SEJA = requests.Session()
SEJA.headers.update(GLAVA)

def obstaja(stvar):
  return stvar.get_text(strip=True) if stvar else None


url = "https://urnik.fmf.uni-lj.si"
stevec = 1

zaporedni_mankajoči = 0
vsi_podatki = []

teden = {
  0 : "ponedeljek",
  1 : "torek",
  2 : "sreda",
  3 : "četrtek",
  4 : "petek",
  5 : "sobota",
  6 : "nedelja"
}

while True:
  if zaporedni_mankajoči == 5:
    break

  stran_z_povezavami = url + "/" + str(stevec)
  stevec += 1
  response = SEJA.get(stran_z_povezavami)
  soup = BeautifulSoup(response.text, "html.parser")
  # print(soup, response)

  if response.status_code == 404:
    # print("Tega urnika ni.")
    zaporedni_mankajoči += 1
    continue
  else:
    zaporedni_mankajoči = 0


  vzorcni_urnik = url + soup.select_one(".padded a")["href"]
  # print(vzorcni_urnik)
  response2 = SEJA.get(vzorcni_urnik)
  soup2 = BeautifulSoup(response2.text, "html.parser")
  obdobje = soup2.select_one("#timetable-logo span").get_text(strip=True)[1:-1]


  if "izpitno obdobje" in  obdobje:
    continue
  print(obdobje)

  vse = set()
  urniki = []
 
  for kvadratek in soup.select(".m6 .collapsible"):
    program = kvadratek.select_one(".collapsible-header").get_text(strip=True)


    for povezava in kvadratek.select("a"):
      link = povezava["href"]
      if "Zimski" in obdobje:
        link = link[:-1] + "8"


      urniki.append({
        "semester" : obdobje,
        "program" : program,
        "letnik" : povezava.get_text(strip=True),
        "url" : link
      })


      # print(povezava["href"][:-1] + "8")

  if not urniki:
    print("Ta stran nima urnikov.")
    continue

  ure = {}

  for urnik in urniki:
    response = SEJA.get(url + urnik["url"])
    soup = BeautifulSoup(response.text, "html.parser")
    prostori_s_predmeti = soup.select(".entry-absolute-box")
    mesta = soup.select(".hour")

    
    if not mesta or not prostori_s_predmeti:
      print(f"Urnik {urnik["program"] + ", " + urnik["letnik"]} je prazen.")
      continue

    for ura in mesta:
      procent = float(ura.get("style").split(":")[1].strip().replace("%", ""))
      cas = ura.get_text(strip=True)

      if cas:
        ure[procent] = int(cas)
    
    for prostor in prostori_s_predmeti:
      # print (prostor.get("style"))
      if "!important" in prostor.select_one(".entry").get("style"):
        continue

      predmet = obstaja(prostor.select_one(".subject"))

      if not predmet:
        continue

      vrsta_ucenja = obstaja(prostor.select_one(".entry-type"))

      if vrsta_ucenja in ["P", "P(A)", "P(/V)", "P(- po dogovoru)"]:
        vrsta_ucenja = "P"
      elif vrsta_ucenja in ["V", "V(1)", "V(1+2)"]:
        vrsta_ucenja = "V"
      elif vrsta_ucenja in ["L", "L(1)"]:
        vrsta_ucenja = "L"
      elif vrsta_ucenja in ["S", "S(1)"]:
        vrsta_ucenja = "S"
      elif vrsta_ucenja in ["O", "O(1)", "O(KVIZ)", "O(V)"]:
        vrsta_ucenja = "O"
      elif vrsta_ucenja in ["T", "T(1)"]:
        vrsta_ucenja = "T"
      else: 
        vrsta_ucenja = "Ostale skupine"

      vse.add(vrsta_ucenja)
      izvajalci = [oseba.get("title") for oseba in prostor.select(".teacher a")]
      profesor = None if (not izvajalci) or izvajalci[0] in ["X", "rezervacija kolokvij", "? ?"] else izvajalci
      if profesor == "rezervacija kolokvij":
        print(profesor)
      ucilnica = prostor.select_one(".classroom")
      predavalnica = obstaja(ucilnica)
      kljuc = round(100 - float(prostor.get("style").split("top:")[1].split("%")[0].strip()), 2)
      ura_zacetka = ure[kljuc]
      trajanje = round(float(prostor.get("style").split("height:")[1].split("%")[0].strip()) / 7.69)
      dan = teden[float(prostor.get("style").split("left:")[1].split("%")[0].strip()) // 20]
      stevilo_programov = len(prostor.select(".layer_one a"))
      # print(stevilo_programov)
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
        "predavatelj" : izvajalci,
        "stevilo programov" : stevilo_programov
      })
      # print(len(vsi_podatki))
  
  print("Končan semester.")

df = pd.DataFrame(vsi_podatki)
df.to_csv("urniki.csv", index=False, encoding="utf8")

print("Konec zajemanja.")
