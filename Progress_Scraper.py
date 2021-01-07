#!/usr/bin/env python3

import socket
import struct
import json
from datetime import datetime
import gspread

HOST1 = 'localhost'
PORT1 = 3338

HOST2 = 'localhost'
PORT2 = 3339

msg = b""

# Account and Spreadsheet detail
serviceaccount = "NONE"
spreadsheet = "NONE"

startDate = datetime.now()
startLevel = 0
oldLines = 0
oldScore = 0
wrapCounter = 0
preTrans = 0
clearString = ''

debug = False
writeStats = False


def parseStat(numString):
    try:
        return int(numString)
    except:
        return (ord(numString[0]) - ord("A") + 10) * (10 ** (len(numString) - 1)) + int(numString[1:])


def doStuff(game):
    global writeStats, oldLines, oldScore, wrapCounter, startDate, startLevel, preTrans, clearString
    if type(game['lines']) == type(None) or type(game['score']) == type(None):
        if writeStats:
            writeStats = False
            endDate = datetime.now()
            if (startLevel>=19 and oldScore>=100000) or oldScore>=400000:
                date = f"{startDate.month:02}/{startDate.day:02}/{startDate.year}"
                time = f"{startDate.hour:02}:{startDate.minute:02}:{startDate.second:02}"
                dur = endDate - startDate
                durMins = dur.seconds // 60
                durSec = dur.seconds % 60
                duration = f"{durMins:02}:{durSec:02}"
                startlv = f"{startLevel}"
                lines = f"{oldLines}"
                pre = f"{preTrans}"
                posttr = oldScore - preTrans
                post = f"{posttr}"
                score = f"{oldScore}"

                gc = gspread.service_account(filename=serviceaccount)
                sh = gc.open_by_url(spreadsheet)
                worksheet = sh.worksheet('January')

                entryno = worksheet.update["L2"]
                no = entryno.value + 2
                strno = str(no)

                if worksheet["I" + str(no - 1)].value != score:
                    worksheet.update("L2", no - 1)

                    worksheet.update(f"A{strno}", no - 1)
                    worksheet.update(f"B{strno}", date)
                    worksheet.update(f"C{strno}", time)
                    worksheet.update(f"D{strno}", duration)
                    worksheet.update(f"E{strno}", startlv)
                    worksheet.update(f"F{strno}", lines)
                    worksheet.update(f"G{strno}", pre)
                    worksheet.update(f"H{strno}", post)
                    worksheet.update(f"I{strno}", score)

                    print("Entry #%d - Score = %s - Lines = %s" % (no - 1, score, lines))

                startLevel = 0
                oldLines = 0
                oldScore = 0
                wrapCounter = 0
                preTrans = 0
                clearString = ''
    else:
        if not writeStats:
            startDate = datetime.now()
            startLevel = parseStat(game['level'])
        
            writeStats = True
        newScore = parseStat(game['score'])
        newScore += wrapCounter * 16000000
        if newScore < oldScore:
            wrapCounter += 1
            newScore += 16000000
            
        newLines = parseStat(game['lines'])
        
        oldScore = newScore

        if newLines > oldLines:
            clearString += str(newLines - oldLines)
        if oldLines < 130:
            preTrans = oldScore
        oldLines = newLines


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST1, PORT1))
    s.listen()
    conn, addr = s.accept()
    with conn:
        dataBuffer = b""
        while True:
            data = conn.recv(1024)
            if not data:
                print("exiting...")
                '''
                f = open("transition.txt", "w")
                f.write(f'000000')
                f.close()
                '''
                break
            dataBuffer += data
            counter = 0
            while len(dataBuffer) > 4:
                size = int(struct.unpack("<i", dataBuffer[0:4])[0])

                target_idx = size + 4
                if len(dataBuffer) < target_idx:
                    break

                msg = dataBuffer[4:target_idx]

                dataBuffer = dataBuffer[target_idx:]

                doStuff(json.loads(msg.decode('utf-8')))
                counter += 1
            if debug:
                print(str(counter) + " packets processed")
