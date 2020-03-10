# ----------------------------------------------------------------------
# User Checkin/Checkout System, using Arduino and Python
# 
# Pedro Duquesne
# 10/22/2019
# ----------------------------------------------------------------------
# PLEASE remember to write something to the Serial after a CaptureCard command.
# Or else the Arduino will get stuck in an infinite loop.
# This only applies if the DOOR flag is True.
# ----------------------------------------------------------------------
# TODO:
# * Arduino waits for Serial information in an infinite loop after reading a card.
#   This is intended at first but kind of annoying to have to write something
#   to the Serial after every single CaptureCard command. Need to change this.
#
# * Implement the Sheets.py code so that it works with this system.
# * Make the code Prettier.
# * Implement a second CardReader.
# ----------------------------------------------------------------------
import serial, re, platform
import firb
from datetime import datetime
import hashlib, getpass, sys, time, os

import colorama
from colorama import Fore, Style
#-----------------------------------------------------------------------
# GLOBAL CONFIG, PLEASE DO NOT EDIT THIS |
#-----------------------------------------------------------------------
VER = 'alpha 0.1.7'
BANNER_TITLE = ''
BANNER_MESSAGE = ''
DOOR = False # Are we going to implement door open mechanic?

SERIAL_COM = ''
BAUD = ''
TOUT = 0
USER = {}
USER_PW = False
ADMIN = {}
BLUE_CARD_UID = ''
IN_USERS = []
#----------------------------------------------------------------------
# Admin Related 
#----------------------------------------------------------------------
def NewUser(args):
    global ser
    
    if(ser != None):
        print('Present new user Card...\n')
        uid = CaptureCard()

        if(DOOR):
            ser.write(b'OK')
    else:
        print('Using 00000000 as UID since no Arduino board is present.')
        uid = '00000000'

    AddNewUser(uid)

def ListUsers(args):
    print('\nListing all Users...\n')
    users = firb.get_all_users()

    for user in users:
        u = user.to_dict()
        print('{:<15} {:<15} {:<15} {:<15}'.format(u['uid'], u['name'], u['lastname'], u['snum']))
    
    print()

def ListChecks(args):
    if len(args) > 2:
        users = args[2].split(',')
        field = args[1][1:]

        if '-q' in args:
            ind = args.index('-q')
            try:
                qty = int(args[ind+1])
            except:
                print('\nERROR: Invalid argument for -q (Expected a positive Integer).\n')
                return
        else:
            print('No argument "-q" specified, using default -q 6')
            qty = 6
        
        for u in users:
            usr = firb.find_user(field, u)
            if(usr == {}):
                print('User Not Found\n')
                return

            print()
            print('-'*60)
            print('Listing checks for:', usr['name'], usr['lastname'])
            print('-'*60)

            docs = firb.find_checks(usr['uid'], qty)

            # List all Checks for one user
            for doc in docs:
                d = doc.to_dict()

                t = ''
                if(d['in']):
                    t = 'IN'
                else:
                    t = 'OUT'

                print(Date12(d['time']), t)

    else:
        print('DESCRIPTION: Shows a list of Checks')
        print('\nUSAGE: checks -[param] [args] -q [num]')
        print('\nExample: checks -name Bob')
        print('Example: checks -name Bob,Alice,Matt -q 4')
        print('Example: checks -uid FA4BB4FC -q 4')
        print('Example: checks -uid 1234ABCD,5678BFDC -q 4')

    print('\nDONE')

def ListChecksIn(args=''):
    global IN_USERS

    print('Listing ALL checked IN users...')
    print('-'*30)
    users = firb.get_all_users()
    for user in users:
        u = user.to_dict()
        docs = firb.find_checks(u['uid'], 1)

        for doc in docs:
            d = doc.to_dict()
            if(d['in'] == True):
                print('{:<15} {:<15} {:<15}'.format(u['name'], u['lastname'], u['snum']))
        
def DisplayHelp(args):
    global COMMANDS
    print('\nCommands Available:\n')

    for c in COMMANDS:
        print(c)
    
    print()

def AdminMenu():
    print('ADMIN Console. Type "help" for a list of commands.')
    print('-'*60)
    GetCommand('Command : ')   

def GetCommand(msg):
    valid = False
    while(not valid):
        comm = input(msg)
        args = comm.split(' ')
        comm = args[0]
        
        if(comm in COMMANDS):
            COMMANDS[comm](args)

def ExitAdmin(args):
    print('\nExiting Admin console. GOODBYE')
    exit()

def DeleteUser(args):
    if(len(args) > 2):
        users = args[2].split(',')
        field = args[1][1:]

        for u in users:
            firb.delete_user(field, u)
    else:
        print('DESCRIPTION: Deletes users from the database.\n')
        print('USAGE: delete -[param] [args]\n')
        print('\nExample: delete -name Bob')
        print('Example: delete -name Bob,Alice,Matt')
        print('Example: delete -uid FA4BB4FC')
        print('Example: delete -uid 1234ABCD,5678BFDC')

def WipeData(args):
    print('NOTE: This command is not yet implemented.\n')

def Report(args):

    #Helper function to both write to a file and print to the screen at the same time.
    def dump(f, s):
        f.write(s + '\n')
        print(s)

    lim = 60 # Limit number of checks reported
    
    if(len(args) >= 2):
        if '-date' in args:
            ind = args.index('-date')

            #Date From
            date = ValidateDate(args[ind+1])
            if date == None:
                print(Fore.RED + 'ERROR: Invalid Date. Corret format is: MM/DD/YYYY' + Fore.WHITE)
                return
            
            # datefrom = datetime(int(date[2]), int(date[0]), int(date[1]))
            datefrom = ParseDate(date)

            #Date To
            date = ValidateDate(args[ind+2])
            if date == None:
                print(Fore.RED + 'ERROR: Invalid Date. Corret format is: MM/DD/YYYY' + Fore.WHITE)
                return

            # dateto = datetime(int(date[2]), int(date[0]), int(date[1]), hour=23, minute=59, second=59)
            dateto = ParseDate(date, end=True)
            
        elif '-today' in args:
                date = datetime.today()
                datefrom = ParseDate([date.month, date.day, date.year])

                date = datetime.today()
                dateto = ParseDate([date.month, date.day, date.year], end=True)
                lim = 100

        else:
            print(Fore.RED + 'ERROR: A date range is required (For Now). Use -date or -today argument.' + Fore.WHITE)
            return

        if '-lim' in args:
            ind = args.index('-lim')
            lim = int(args[ind+1])

            if(lim <= 0):
                print(Fore.RED + 'ERROR: An error occured in -lim argument. Must be a positive number.' + Fore.WHITE)
                return
        
        # Begin Printing Assistance
        os.system('clear')
        os.system('cls')

        f = open('Report_.txt', 'w')
        dump(f,'-'*100)
        dump(f,f'::Assistance Report:: Generated {Date12(datetime.today())}\n')
        dump(f,f'Date From: {Date12(datefrom)}')
        dump(f,f'Date To: {Date12(dateto)}')
        dump(f,'-'*35)

        docs = firb.find_checks_date(datefrom, dateto, lim)

        for d in docs:
            doc = d.to_dict()
            u = firb.find_user('uid', doc['uid'])

            if(u != {}):
                c = 'Unknown'
                cd = 'Unknown'
                if(doc['in']):
                    c = Fore.GREEN + 'IN' + Fore.WHITE
                    cd = 'IN'
                else:
                    c = Fore.RED + 'OUT' + Fore.WHITE
                    cd = 'OUT'
                
                # Can't use helper function 'dump' here because we cant color text to a regular text file.
                print('{:<16} {:<16} {:<15} {:<24} {:<12}'.format(u['name'], u['lastname'], u['snum'], Date12(doc['time']), c))
                f.write('{:<16} {:<16} {:<15} {:<24} {:<12}\n'.format(u['name'], u['lastname'], u['snum'], Date12(doc['time']), cd))

        dump(f,'-'*100)
        print(f'Assistance report saved to: {f.name}')
        f.close()
        # Finish Assistance Report

    else:
        print('DESCRIPTION: Generates a checks report specified by criteria.')
        print('USAGE: report -date [Date From] [Date To] -lim [days]')
        print()

        print('Dates Format: MM/DD/YYYY | months and days can be single digits.')
        print('If no -lim argument is specified, it will default to 60.')
        print()

        print('EXAMPLE: report -date 2020/1/1 2020/1/7')
        print('EXAMPLE: report -date 2020/3/3 2020/3/4 -lim 10')
        print('EXAMPLE: report -today -lim 15')
        print()

COMMANDS = {
    'new'       : NewUser,
    'users'     : ListUsers,
    'checks'    : ListChecks,
    'checksin'  : ListChecksIn,
    'report'    : Report,
    'quit'      : ExitAdmin,
    'delete'    : DeleteUser,
    'wipe'      : WipeData,
    'help'      : DisplayHelp,
    'exit'      : ExitAdmin,
}

# --------------------------------------------------------------------------------
def DisplayBanner():
    print('\nCheckin Service VER: ' + VER)
    print()
    print('-'*80)
    print(BANNER_TITLE)
    print(BANNER_MESSAGE)
    print('-'*80)

    print('\nInitializing...')
    print('Operating System: ' + platform.system())
    print('-'*80)

def ReadConfig(file):
    global SERIAL_COM
    global BAUD
    global TOUT
    global BLUE_CARD_UID
    global BANNER_MESSAGE
    global BANNER_TITLE

    # Read all contents from config.txt ------------
    print('\nReading config.txt file...')
    try:
        f = open(file, "r")
    except:
        print("ERROR: An error ocurred while opening {} file.".format(file))
        print('EXITING')
        exit()

    contents = f.read()
    f.close()

    print('-'*30)

    # Read COM Port
    pat = 'port=(.+)'
    match = re.search(pat, contents)
    SERIAL_COM = match.group(1)
    print('SERIAL PORT:', SERIAL_COM)

    # Read BAUD RATE
    pat = 'baud=(\d+)'
    match = re.search(pat, contents)
    BAUD = int(match.group(1))
    print('BAUD RATE:', BAUD)

    # Read Timeout
    pat = 'timeout=(\d+)'
    match = re.search(pat, contents)
    TOUT = int(match.group(1))
    print('Arduino conenction Timeout:', TOUT)

    # Read Blue Keycard UID
    pat = 'bluecard=(.+)'
    match = re.search(pat, contents)
    BLUE_CARD_UID = match.group(1)
    print('BLUE KEY UID:', BLUE_CARD_UID)

    # Read Banner Title
    pat = 'title="(.+)"'
    match = re.search(pat, contents)
    BANNER_TITLE = match.group(1)

    # Read Banner Message
    pat = 'message="(.+)"'
    match = re.search(pat, contents)
    BANNER_MESSAGE = match.group(1)

    print ('\nDONE')

# Get time now in 12 hour format with 'PM/AM' Suffix
def Date12(time):

    # Get Date and Time and adjust for 12 hour format
    now = time.strftime("%m/%d/%Y %H:%M:%S")

    pat = ' (\d\d):\d\d:\d\d'
    match = re.search(pat, now)
    hour = int(match.group(1))

    if(hour >= 12):
        tod = ' PM'
    else:
        tod = ' AM'
    now_12 = time.strftime("%m/%d/%Y %I:%M:%S")
    now_12 += tod

    return now_12

def ConnectArduino():
    ser = None
    print('\nSearching for Arduino board on serial port:', SERIAL_COM)
    try:
        ser = serial.Serial(SERIAL_COM, BAUD)
    except:
        print('\nERROR: Cannot open serial port:', SERIAL_COM)

        if(platform.system() == 'Linux'):
            print('Make sure you run this as sudo.\n')

        ser = None

    if(ser != None):
        print('Connected to Arduino on port', ser.name)

    return ser

# Main menu functions
def MainMenu(user):
    print('-'*60)
    print('NOTE: This feature is not fully implemented yet.\n')
    print('-'*60)

    print('\nBlue Keycard detected, entering main menu for ({} {})'.format(user['name'], user['lastname']))
    print('UID:', user['uid'])
    print()
    
    # if(not InputPassword('Please Enter user Password: ', user['pass'])):
    #     print('ERROR: Failed to provide user password. Returning.')
    #     return

    menu_switch = {
        1 : MenuLatestChecks,
        2 : MenuChecksByDate,
    }

    while(True):
        print('Please Enter an Option:\n')
        print('0: Exit')
        print('1: Verify Latest Checks')
        print('2: Verify Assistance by date range.')

        print()

        sel = ValidateInput_Int(msg='Menu #: ', valid_range=range(0,3))
        if(sel == 0):
            break
        
        menu_switch[sel]()   
            
def MenuLatestChecks():
    print()
    num = ValidateInput_Int(msg='How many Checks to review? (1 - 30): ', valid_range=range(1,31))
    docs = firb.find_checks(USER['uid'], num)

    print('\nDisplaying last {} Checks:'.format(num))
    print()
    for doc in docs:
        d = doc.to_dict()
        if(d['in'] == True):
            c = Fore.GREEN + 'IN' + Fore.WHITE
        else:
            c = Fore.RED + 'OUT' + Fore.WHITE
        
        print(Date12(d['time']), c)

def MenuChecksByDate():
    # Get Starting date
    date = input('Please enter starting date (MM/DD/YYYY): ')
    date = ValidateDate(date)
    if date == None:
        print(Fore.RED + 'ERROR: Invalid date format. Format: (MM/DD/YYYY).' + Fore.WHITE)
        return
    
    datefrom = ParseDate(date)
    #-----------------------------------

    # Get Ending date
    date = input('Please enter ending date (MM/DD/YYYY): ')
    date = ValidateDate(date)
    if date == None:
        print(Fore.RED + 'ERROR: Invalid date format. Format: (MM/DD/YYYY).')
        return
    
    dateto = ParseDate(date)
    #-----------------------------------

    lim = ValidateInput_Int('Please enter number of checks to review (Max 100): ', valid_range=range(1, 101))
    docs = firb.find_checks_date(datefrom, dateto, lim, uid=USER['uid'])

    print('-' * 80)
    for d in docs:
        doc = d.to_dict()
        u = firb.find_user('uid', doc['uid'])

        if(u != {}):
            c = 'Unknown'
            cd = 'Unknown'
            if(doc['in']):
                c = Fore.GREEN + 'IN' + Fore.WHITE
                cd = 'IN'
            else:
                c = Fore.RED + 'OUT' + Fore.WHITE
                cd = 'OUT'
            
            # Can't use helper function 'dump' here because we cant color text to a regular text file.
            print('{:<16} {:<16} {:<15} {:<24} {:<12}'.format(u['name'], u['lastname'], u['snum'], Date12(doc['time']), c))
    
    print('-' * 80)

def ValidateDate(arg):
    date = arg.split('/')
    if len(date) != 3:
        return None

    return date

def ParseDate(date, end=False):
    #Date argument must be [MM/DD/YYYY]
    print(f'About to parse date: {date}\n')
    if end:
        parsed = datetime(int(date[2]), int(date[0]), int(date[1]), hour=23, minute=59, second=59)
    else:
        parsed = datetime(int(date[2]), int(date[0]), int(date[1]), hour=0, minute=0, second=0)

    return parsed

def ValidateInput_Int(msg = '', valid_range = [0]):
    done = False
    while(not done):
        try:
            num = int(input(msg))
        except:
            print('Invalid Input')
            continue

        for i in valid_range:
            if(num == i):
                done = True
                break # Breaks For Loop
    
    return num
    
# End Main menu functions -----------------

# Main Functions
def FetchUser(uid):
    user = {}
    print('\nFetching user on Database...')

    try:
        user = firb.find_user('uid', uid)
    except:
        print('\nERROR: There was a problem connecting to the Database.')
    
    return user

def AddNewUser(uid):
    user = firb.find_user('uid', uid)

    if(len(user) > 0):
        print('User already exists in the Database.\n')
        return

    name = input('\nFirst Name : ')
    last = input('Last Name : ')
    student_num = input('Student Num #: ')
    
    while(True):
        password = getpass.getpass(prompt='Personal Password (Min Length=6): ')
        if(len(password) < 6):
            print('\nPassword does not satisfy length requirement.\n')
            continue

        password_confirm = getpass.getpass(prompt='Confirm Password: ')

        if(password == password_confirm):
            break
        else:
            print('\nPasswords do not match!\n')

    m = hashlib.sha256()
    m.update(password.encode('utf-8'))
    password = m.hexdigest()

    print('\nAdding new user to Database...')

    # Data envelope schema
    data = {
        'name' : name,
        'lastname' : last,
        'uid' : uid,
        'snum' : student_num,
        'pass' : password,
        'admin' : False,
    }

    firb.add_user(data)
    print('Done\n')

def CheckUser(user):
    print('USER PROCESS OK\n')
    print('User:', user['name'], user['lastname'])
    print('Student Num:', user['snum'])

    # This is the object we are going to pass to firb.addCheck.
    date = datetime.now()

    # Get time now in 12 hour format with 'PM/AM' Suffix
    now_12 = Date12(date)
    print('Time:', now_12)
    print()
    firb.add_check(user['uid'], date)

def AdminSetup():
    global ADMIN

    print('ALERT: No admin password detected. Please setup an admin password now.\n')
    while(True):
        password = getpass.getpass(prompt='Admin Password (Min Len=6): ')

        if(len(password) < 6):
            print('Password does not meet minimum length requirement.\n')
            continue
        
        password_confirm = getpass.getpass(prompt='Confirm Password: ')

        if(password != password_confirm):
            print('Password does not match!\n')
            continue

        m = hashlib.sha256()
        m.update(password.encode('utf-8'))
        password = m.hexdigest()

        data = {
            'pass' : password
        }

        try:
            firb.set_admin(data)
            print('Admin password successfully added!\n')
            ADMIN = data
            break
        except:
            print('ERROR: There was an error adding the admin data to the database. QUITTING!')
            exit()

def InputPassword(msg, pswd, attempts=3):
    at = 0
    while(at < attempts):
        # getpass allows the user to input a password in the console without showing the characters.
        password = getpass.getpass(prompt=msg)
        m = hashlib.sha256()
        m.update(password.encode('utf-8'))
        password = m.hexdigest()

        if(password == pswd):
            print('Password Confirmed!\n')
            return True
        else:
            print('Wrong Password, please try again.')
            at += 1
    
    return False

# PLEASE remember to write something to the Serial after a CaptureCard command.
# Or else the Arduino will get stuck in an infinite loop.
def CaptureCard(serclose = False):

    global ser
    uid = ''

    if (ser == None):
        print('ERROR: Arduino serial communication not found.\n')
        return None
    
    # Inner Loop
    while(True):
        if(ser.isOpen() == False):
            ser.open()

        line = ser.readline()

        # The readline command reads Serial data as a sequence of bytes rather than ascii characters.
        # We need to convert this for convenience.
        msg = str(line,'ascii')

        # If there is no message in the Serial, restart the loop.
        if(msg == ''):
            continue

        pat = 'HEX: (.. .. .. ..)' # Pattern to identify the line containing the card's UID in HEX
        match = re.search(pat, msg)

        if match:
            uid = match.group(1).replace(' ', '')
            #print('UID: ' + uid)
            print('Read Successful')
            break
        
    if(serclose):
        ser.close()
    
    return uid

#-----------------------------------------------------------------------------
# MAIN BEGIN
#-----------------------------------------------------------------------------
ReadConfig('config.txt')

time.sleep(1)
os.system('clear')
os.system('cls')
DisplayBanner()

ser = ConnectArduino()

ADMIN = firb.get_admin()

if(ADMIN == None or ADMIN['pass'] == None):
    AdminSetup()

if(len(sys.argv) > 1 and sys.argv[1] == 'admin'):
    print()
    if(InputPassword('Please enter Admin Password: ', ADMIN['pass'])):
        AdminMenu()
    else:
        print('ERROR: Cannot enter Admin menu. Incorrect Password. QUITTING!')
        exit()

if(ser == None):
    print('ERROR: No serial connection established. Cannot continue. Quitting.')
    exit()

line = ''
uid = ''

print()

# Flushes the serial connection before main program begins.
# while True:
#     line = ser.readline()
#     msg = str(line,'ascii')
#     if msg == '':
#         break

# MAIN LOOP ROUTINE
while(True):
    #ListChecksIn()
    print('\nPlease present your card...\n')

    uid = CaptureCard()
    
    # Determine if Blue Keycard
    # This will later be done with a push button
    if(uid == BLUE_CARD_UID):
        print('\nPlease present your card to access user menu...\n')
        uid = CaptureCard()
        ser.write(b'OK')
        # ser.close()

        print('-'*60)

        USER = FetchUser(uid)

        if(len(USER) != 0):
            # Open main user menu
            MainMenu(USER)
            continue
        else:
            print('ERROR: User not found. Cannot enter Menu.\n')
            continue

    USER = FetchUser(uid)

    if(len(USER) != 0):
        print('-'*60)
        print('.'*60)
        CheckUser(USER)
        print('.'*60)
        print('-'*60)
        # Send the Open Door signal
        if(DOOR):
            ser.write(b'OPEN')
            time.sleep(4)

    else:
        # AddUnknownUser(uid)
        print('\nERROR: Unknown UID Detected.\n')

        # Send an "Error" signal. SOMETHING needs to be sent to the Arduino.
        # Becasue the Arduino at this point is expecting data to read in the Serial.
        # If nothing is sent, the Arduino will get stucked in an infinite Loop.
        if(DOOR):
            ser.write(b'E')

    # time.sleep(2)
    # os.system('clear')
    # os.system('cls')

ser.close()

#EOF