from apiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import os.path
from datetime import datetime, timezone
import time
import pytz
import pygame

# ---------CONSTS---------
scopes = ['https://www.googleapis.com/auth/calendar']
NUMBER_OF_CALENDARS = 12
WAIT_N_MINUTES_FOR_NEXT_CHECK = 1
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
    
    for i in range(NUMBER_OF_CALENDARS):
        if calendars['items'][i]['summary'] == 'waking-up':
            return i
    return -1
    

def findEventNameIndex(eventList, name):
    for i, event in enumerate(eventList['items']):
        # print("Zdarzenie",i,": ",event,'\n')
        if event.get('summary') == name:
            return i
    return -1
    

def isIndexWrong(index):
    if index == -1:
        return True
    return False


def findClosestIndexBeforeAlarm(eventList, now, lastIndex):
    before = datetime.fromisoformat("9999-12-12 23:59:59")
    
    for i, event in enumerate(eventList['items']):
        if i < lastIndex:
            i = lastIndex
        
        print("i:",i)
        
        event_data_start = datetime.fromisoformat(eventList['items'][i]['start']['dateTime'])
        event_data_end =  datetime.fromisoformat(eventList['items'][i]['end']['dateTime'])
        
        print("start: ",event_data_start)
        print("end: ",event_data_end)
        print("now:", now, '\n')
        
        if event_data_start >= now:
            # print("event_data >= now")
            if i > 0:
                if before >= now:
                    # print("return i-1")
                    return i-1
            # print("return i")
            return i
        elif event_data_start < now:
            if event_data_end >= now:
                # print("return i")
                return i
            #print("event_data < now")
            before = event_data_start
        #print('\n')
                
    return -1


# ---------CODE---------
lastEventIndex = 0

while True:
    service = connectToGoogleCalendar()

    # wszystkie kalendarze w liscie
    allCalendars = service.calendarList().list().execute()

    wakingUpIndex = where_is_waking_up_index(allCalendars)

    if isIndexWrong(wakingUpIndex):
        raise ValueError("Calendar 'waking-up' not found.")

    # weź zdarzenia danego kalendarza
    wakingCalendar = allCalendars['items'][wakingUpIndex]

    eventsWakingUpList = service.events().list(calendarId=wakingCalendar['id'], orderBy="startTime", singleEvents=True).execute()

    # events = eventsWakingUpList.get("items", [])

    # for event in sortedWakingUpList:
    #    start_time = event['start'].get('dateTime', event['start'].get('date'))
    #    print(start_time)

    # print('\n')
    # print(eventsWakingUpList)
    # print('\n')

    event1Index = findEventNameIndex(eventsWakingUpList, 'POBUDKA')
    
    if isIndexWrong(event1Index):
        raise ValueError("Event not found.")

    # 2.
    event0 = eventsWakingUpList['items'][0]

    utc_timezone = pytz.timezone(event0['start']['timeZone'])
    date_now = datetime.now(utc_timezone).replace(microsecond=0)

    closest_events_index = findClosestIndexBeforeAlarm(eventsWakingUpList, date_now, lastEventIndex)
    lastEventIndex = closest_events_index
    
    event1 = eventsWakingUpList['items'][closest_events_index] # [event1Index]
    event1_start_time = event1['start']['dateTime']
    event1_end_time = event1['end']['dateTime']

    print("EVENT NAME:", event1['summary'])
    print("START TIME:", event1_start_time)
    print("END TIME:", event1_end_time)

    # zamienienie formatu daty z kalendarza aby można było porównać go z datą aktualną

    event1_start_time = datetime.fromisoformat(event1_start_time)
    event1_end_time = datetime.fromisoformat(event1_end_time)

    print("TIME NOW:", date_now)

    if event1_start_time <= date_now <= event1_end_time:
        print("ALARM!")
        pygame.init()
        pygame.mixer.init()
        
        screen = pygame.display.set_mode((600, 200))
        pygame.display.set_caption("ALARM CLOCK")
        font = pygame.font.Font(None, 36)
        txt_to_alarm_application = "Now playing: " + audioName
        text0 = font.render(date_now.strftime("%H:%M:%S %Y-%m-%d"), True, (0, 255, 0))
        text1 = font.render(txt_to_alarm_application, True, (255, 255, 255))
        text2 =  font.render("To turn off the alarm press ESC or ENTER", True, (255, 255, 255))
        screen.blit(text0, (200, 30))
        screen.blit(text1, (130, 80))
        screen.blit(text2, (60, 130))
        pygame.display.flip()
        
        pygame.mixer.music.load(audioSource+audioName)
        pygame.mixer.music.play()
        
        isRunning = pygame.mixer.music.get_busy()
        while isRunning:
            for event in pygame.event.get():
                # if event.type == pygame.QUIT:
                #     isRunning = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                        pygame.mixer.music.stop()
                        isRunning = False
                        print("ALARM CLOCK TURN OFF MANUALLY")
                    
            pygame.time.Clock().tick(10)
            
        pygame.quit()
    else:
        time_difference = event1_start_time - date_now
        print("DIFFERENCE:", time_difference)  
    
    print("WAITING", WAIT_N_MINUTES_FOR_NEXT_CHECK, "MINUTES")
    time.sleep(WAIT_N_MINUTES_FOR_NEXT_CHECK * 60)
    print("NEXT CHECK")
    
