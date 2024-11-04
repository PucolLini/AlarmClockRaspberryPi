from apiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import os.path
from datetime import datetime, timezone
import pytz
import pygame

# ---------CONSTS---------
scopes = ['https://www.googleapis.com/auth/calendar']
NUMBER_OF_CALENDARS = 12
audioSource = "/home/pucollini/Projects/Sounds/"
audioName = "Nightcall.mp3"

#---------FUNCTIONS---------
def connectToGoogleCalendar():
    if os.path.exists("token.pkl"):
        creds = pickle.load(open("token.pkl", "rb"))
    else:
        # sprawdzenie użytkownika
        flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", scopes=scopes)
        creds = flow.run_local_server(port=0)
        # wrzucenie credential do pliku token
        pickle.dump(creds, open("token.pkl", "wb"))
    
    service = build("calendar", "v3", credentials=creds)
    
    return service


def where_is_waking_up_index(calendars):
    # Kalendarze:
    # 1   Znajomi
    # 2   Sport
    # 3   woloszyn.kari@gmail.com
    # 4   Odpoczynek
    # 5   Praca
    # 6   Informatyka plan lekcji
    # 7   Informatyka Grupa 6
    # 8   Urodziny
    # 9   SimLE
    # 10   waking-up
    # 11   Studia
    
    for i in range(NUMBER_OF_CALENDARS):
        # print(i, " ", calendars['items'][i]['summary'])
        if calendars['items'][i]['summary'] == 'waking-up':
            return i
    return -1
    

def findTestIndex(eventList):
    for i, event in enumerate(eventList['items']):
        # print("Zdarzenie",i,": ",event,'\n')
        if event.get('summary') == 'test':
            return i
    return -1
    

def isIndexWrong(index):
    if index == -1:
        return True
    return False


# ---------CODE---------
service = connectToGoogleCalendar()

# wszystkie kalendarze w liscie
allCalendars = service.calendarList().list().execute()

wakingUpIndex = where_is_waking_up_index(allCalendars)

if isIndexWrong(wakingUpIndex):
    raise ValueError("Calendar 'waking-up' not found.")

# weź zdarzenia danego kalendarza
wakingCalendar = allCalendars['items'][wakingUpIndex]

eventsWakingUpList = service.events().list(calendarId=wakingCalendar['id']).execute()

# print('\n')
# print(eventsWakingUpList)
# print('\n')

event1Index = findTestIndex(eventsWakingUpList)

if isIndexWrong(event1Index):
    raise ValueError("Event not found.")

# 1. zdarzenia posortować od najstarszego do najnowszego
# 2. szukać dopóki zdarzenie Z(n) > data_now (i wtedy zrobić krok w tył)
# 3. zrealizować budzik dla Z(n-1), jezeli nie ma alarmu to zrelizowac dla Z(n)
# 4. Czekanie (np. 30 min) do kolejnego sprawdzenia alarmów

event1 = eventsWakingUpList['items'][event1Index]
event1_start_time = event1['start']['dateTime']
event1_end_time = event1['end']['dateTime']

print('\n')
print("EVENT NAME:", event1['summary'])
print("START TIME:", event1_start_time)
print("END TIME:", event1_end_time)

# zamienienie formatu daty z kalendarza aby można było porównać go z datą aktualną
utc_timezone = pytz.timezone(event1['start']['timeZone'])

event1_start_time = datetime.fromisoformat(event1_start_time)
event1_end_time = datetime.fromisoformat(event1_end_time)

date_now = datetime.now(utc_timezone).replace(microsecond=0)

print("TIME NOW:", date_now)

if event1_start_time <= date_now <= event1_end_time:
    print("ALARM!")
    pygame.mixer.init()
    pygame.mixer.music.load(audioSource+audioName)
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    
else:
    time_difference = event1_start_time - date_now
    print("RÓŻNICA:", time_difference)    

    
    
    
    
    
    
    
