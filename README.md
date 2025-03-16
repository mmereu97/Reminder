# Aplicație Reminder

O aplicație completă pentru evidența evenimentelor, aniversărilor și sărbătorilor, dezvoltată cu Python și PyQt5.

![Screenshot aplicație](Capture.png)

## Prezentare generală

Această aplicație vă ajută să țineți evidența datelor importante, inclusiv evenimente, aniversări și sărbători. Sistemul calculează automat perioadele de notificare și oferă reminder-uri vizuale pentru evenimentele apropiate.

## Caracteristici

- **Multiple tipuri de reminder-uri**: Urmărire evenimente, aniversări și sărbători
- **Evenimente recurente**: Suport pentru diverse cicluri de repetare (lunar, anual, intervale personalizate)
- **Sistem de notificări**: Perioade de notificare configurabile pentru fiecare eveniment
- **Alerte vizuale**: Alerte codate prin culori în funcție de apropierea față de termene limită
- **Integrare program de lucru**: Ia în considerare programul de lucru la calcularea reminder-urilor
- **Integrare în system tray**: Rulează în fundal cu acces din bara de sistem
- **Interfață personalizabilă**: Fonturi, spațiere și preferințe de afișare ajustabile
- **Persistența datelor**: Toate datele sunt stocate în fișiere CSV pentru backup și portabilitate ușoară

## Cerințe

- Python 3.6+
- PyQt5
- pandas
- dateutil

## Instalare

1. Clonați acest repository sau descărcați codul sursă
2. Instalați dependențele necesare:

```bash
pip install PyQt5 pandas python-dateutil
```

3. Rulați aplicația:

```bash
python Reminder.py
```

## Utilizare

### Configurare inițială

Când rulați aplicația pentru prima dată, aceasta va crea trei fișiere CSV dacă nu există:
- `informatii.csv` - Pentru evenimente obișnuite
- `aniversari.csv` - Pentru aniversări
- `sarbatori.csv` - Pentru sărbători și comemorări

### Interfața principală

Fereastra principală afișează:
- O listă cu evenimente, aniversări și sărbători apropiate care necesită atenție
- Butoane pentru accesarea și editarea fiecărui fișier de date
- Opțiuni pentru configurarea vizibilității evenimentelor legate de serviciu
- Acces la setările aplicației

### Gestionarea evenimentelor

Faceți clic pe butoanele respective pentru a deschide editorii pentru:
- **Evenimente**: Termene limită, sarcini recurente și date importante
- **Aniversări**: Zile de naștere și alte sărbători anuale
- **Sărbători**: Evidența sărbătorilor și comemorărilor

### Editori de evenimente

Fiecare editor vă permite să:
- Adăugați intrări noi
- Editați intrările existente
- Ștergeți intrări
- Sortați și organizați datele
- Setați perioade de notificare pentru fiecare intrare

### Setări

Dialogul de setări vă permite să personalizați:
- Dimensiunea fonturilor pentru diferite elemente ale interfeței
- Preferințele de vizibilitate pentru evenimentele finalizate
- Configurația programului de lucru
- Spațierea și aspectul butoanelor
- Preferințele de afișare a sărbătorilor

### Program de lucru

Configurați programul de lucru pentru a:
- Defini zilele și orele de lucru
- Ascunde automat evenimentele legate de serviciu în afara orelor de lucru
- Ține cont de weekenduri și zile nelucrătoare în calcularea termenelor limită

### Integrare în sistem tray

Aplicația poate fi minimizată în system tray:
- Continuă să ruleze în fundal
- Acces rapid prin iconița din system tray
- Notificările rămân active

## Structura datelor

### Evenimente (informatii.csv)
- `eveniment`: Numele/descrierea evenimentului
- `data`: Data evenimentului (ZZ-LL-AAAA)
- `avanszile`: Zilele înainte de a începe notificarea
- `ciclu`: Ciclul de recurență (lunar, anual, etc.)
- `weekend`: Dacă zilele de weekend contează pentru acest eveniment
- `rosu`: Zilele înainte de eveniment pentru a evidenția în roșu
- `stare`: Status (pastreaza/indeplinit)
- `serviciu`: Dacă este legat de serviciu
- `observatii`: Note/observații suplimentare

### Aniversări (aniversari.csv)
- `eveniment`: Numele persoanei sau descrierea evenimentului
- `data`: Data nașterii sau data originală (ZZ-LL-AAAA)
- `avanszile`: Zilele înainte de a începe notificarea
- `ciclu`: Normal anual pentru zile de naștere
- `rosu`: Zilele înainte pentru a evidenția în roșu
- `stare`: Status (pastreaza/indeplinit)
- `observatii`: Note/observații suplimentare

### Sărbători (sarbatori.csv)
- `eveniment`: Numele sărbătorii
- `ziua`: Ziua lunii
- `luna`: Numele lunii în română
- `avanszile`: Zilele înainte de a începe notificarea
- `rosu`: Zilele înainte pentru a evidenția în roșu
- `tip`: Tipul sărbătorii/comemorării
- `sarbatoare_cruce_rosie`: Dacă este o sărbătoare religioasă majoră
- `observatii`: Note/observații suplimentare

## Sfaturi

- Faceți clic pe o notificare de eveniment pentru a o marca rapid ca finalizată
- Utilizați tooltip-urile (trecând cursorul peste elemente) pentru a vedea informații suplimentare
- Configurați programele de lucru pentru o urmărire mai precisă a termenelor de afaceri
- Aplicația calculează automat următoarea apariție pentru evenimentele recurente

## Depanare

Dacă întâmpinați probleme:
- Verificați fișierul `error_log.txt` pentru mesaje de eroare detaliate
- Asigurați-vă că toate fișierele CSV au permisiuni corespunzătoare de citire/scriere
- Dacă un fișier CSV devine corupt, aplicația va încerca să creeze unul nou

## Licență

Această aplicație este furnizată ca atare pentru uz personal și de afaceri.

## Autor

Mereu Mihai
