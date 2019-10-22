# ----------------------------------------------------------------------
# User Checkin/Checkout System, using Arduino and Python
# 
# Pedro Duquesne
# 10/22/2019
# ----------------------------------------------------------------------
import serial, re, platform
import firb
from datetime import datetime
import hashlib
import getpass
import sys
#-----------------------------------------------------------------------
# GLOBAL CONFIG, PLEASE EDIT THIS |
#-----------------------------------------------------------------------
VER = 'beta 1.0.0'
BANNER_TITLE = 'CORE LAB Check In Service - Ver: ' + VER
BANNER_MESSAGE = 'Pedro Duquesne @ Universidad Interamericana de Bayamón - School of Engineering\n'
#-----------------------------------------------------------------------


#-----------------------------------------------------------------------
# 
#-----------------------------------------------------------------------

# Global Variables
SERIAL_COM = ''
BAUD = ''
TOUT = 0
USER = {}
USER_PW = False
ADMIN = {}
BLUE_CARD_UID = ''

#----------------------------------------------------------------------
# Admin Related 
#----------------------------------------------------------------------
def ListUsers(args):
    print('\nListing all Users...\n')
    users = firb.get_all_users()

    for user in users:
        u = user.to_dict()
        print('{:<15} {:<15} {:<15} {:<15}'.format(u['uid'], u['name'], u['lastname'], u['snum']))
    
    print()

def ListChecks(args):
    if(len(args) > 2 and args[1] == '-uid'):
        uids = args[2].split(',')

        if(args[3] == '-q'):
            try:
                qty = int(args[4])
            except:
                print('\nERROR: Invalid argument for -q (Expected a positive Integer).\n')
                return
        else:
            qty = 6
        
        for uid in uids:
            u = firb.find_user_by_uid(uid)
            print()
            print('-'*60)
            print('Listing checks for:', u['name'], u['lastname'])
            print('-'*60)

            docs = firb.find_checks(uid, qty)

            # List all Checks for one user
            for doc in docs:
                d = doc.to_dict()
                print(Date12(d['time']), d['in'])

    else:
        print('\nUSAGE: checks -uid [uid,uid,...] -q [num]')

    print('\nDONE')

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
    firb.delete_user(args[1])

def WipeData(args):
    pass

COMMANDS = {
    'users' : ListUsers,
    'checks' : ListChecks,
    'help' : DisplayHelp,
    'quit' : ExitAdmin,
    'exit' : ExitAdmin,
    'delete' : DeleteUser,
    'wipe' : WipeData,
}

# --------------------------------------------
def DisplayBanner():
    print(BANNER_TITLE)
    print(BANNER_MESSAGE)

    print('Initializing...')
    print('Operating System: ' + platform.system())

def ReadConfig(file):
    global SERIAL_COM
    global BAUD
    global TOUT
    global BLUE_CARD_UID

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
        ser = serial.Serial(SERIAL_COM, BAUD, timeout=TOUT)
    except:
        print('\nERROR: Cannot open serial port:', SERIAL_COM)

        if(platform.system() == 'Linux'):
            print('Make sure you run this as sudo.\n')

        print('EXITING\n')
        exit()

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
    
    if(not InputPassword('Please Enter user Password: ', user['pass'])):
        print('ERROR: Failed to provide user password. Returning.')
        return

    menu_switch = {
        1 : Menu_FindChecks,
    }

    while(True):
        print('Please Enter an Option:\n')
        print('1: Verify Assistance')
        print('2: Change UID')

        print('0: Exit')

        print()

        sel = ValidateInput_Int(msg='Menu #: ', valid_range=range(0,2))
        if(sel == 0):
            break
        
        menu_switch[sel]()   
            
def Menu_FindChecks():
    print()
    num = ValidateInput_Int(msg='How many Checks to review? (1 - 20): ', valid_range=range(1,21))

    docs = firb.find_checks(USER['uid'], num)
    print('\nDisplaying last {} Checks:'.format(num))
    print()
    for doc in docs:
        d = doc.to_dict()
        if(d['in'] == True):
            c = 'CHECK IN'
        else:
            c = 'CHECK OUT'
        
        print(Date12(d['time']), c)

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

# DB Functions
def AddUnknownUser(uid):
    print('UNKNOWN UID:', uid)
    print('Add new user now?')
    select = input('y/n : ')

    if(select == 'y'):
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
            'pass' : password
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
        password = getpass.getpass(prompt=msg)
        m = hashlib.sha256()
        m.update(password.encode('utf-8'))
        password = m.hexdigest()

        if(password == pswd):
            print('Password Confirmed!\n')
            return True
            break
        else:
            print('Wrong Password, please try again.')
            at += 1
    
    return False


#-----------------------------------------------------------------------------
# MAIN BEGIN
#-----------------------------------------------------------------------------
DisplayBanner()

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

ReadConfig('config.txt')

print('-'*30)

ser = ConnectArduino()

line = ''
uid = ''

print()

while(True):
    print('\nPlease present your card...\n')

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

            # Determine if Blue Keycard
            if(uid == BLUE_CARD_UID):
                ser.close()
                print('-'*30)

                if(len(USER) != 0):
                    # Open main user menu
                    MainMenu(USER)
                    break
                else:
                    print('ERROR: No user has been registered since startup. Cannot enter Menu.\n')
                    break

            print('\nFetching user on Database...')

            try:
                USER = firb.find_user_by_uid(uid)
            except:
                print('\nERROR: There was a problem connecting to the Database.')
                break

            if(len(USER) != 0):
                print('-'*30)
                print('.'*30)
                CheckUser(USER)
                print('.'*30)
                print('-'*30)

                break

            else:
                ser.close()
                AddUnknownUser(uid)

                break

ser.close()
