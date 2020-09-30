#!/usr/bin/python3

import sys,re,os,math,base64

#---------------------------------------------------------
#Config
nameSep = 2.0
nameMinYDist = 1.2
nameXMarg = 0.2

#---------------------------------------------------------
# Arg parce
if len(sys.argv) != 2:
    sys.exit("Missing argument")

legFile = sys.argv[1]

if not os.path.isfile(legFile):
    sys.exit("Could not fetch file")

import json

#---------------------------------------------------------
# Load all data and get relevant data

with open(legFile) as f:
    data=json.load(f)

#---------------------------------------------------------
# Controls

cList = []


for course in data['courses']:

    cName = course['name'];
    cId = course['id'];
    cCtrls = {}
    cOrder = []
    nextIx = 0
    cIx = []

    for control in course['controls']:
        i=control['control']['courseSettingId'];
        cCtrls[i] = {
              'lat' : control['control']['position']['latitude'],
              'lon' : control['control']['position']['longitude'] };

        cOrder.append({
            'i':i,
            'type':control['control']['type']})

        if 'ix' not in cCtrls[i]:
            cCtrls[i]['ix'] = nextIx
            nextIx += 1
            cIx.append(i)

    cList.append(
        { 'name' : cName,
          'id' : cId,
          'ord' : cOrder,
          'ix' : cIx,
          'ctrls' : cCtrls })

#print(cList)

#---------------------------------------------------------
# Export

def packStr(out,s):
    if (len(s) > 255):
        sys.exit("Too long string")
    out[0].append(len(s))
    for c in s:
        out[0].append(ord(c))

def pack8(out,b):
    if (b < 0) or (b > 255):
        sys.exit("Byte out of range")
    out[0].append(b)
    #print(b);

def pack16(out, dw):
    for i in range(2):
      pack8(out, dw % 256)
      dw //= 256
    if (dw > 0):
        sys.exit("16Bit word out of range")

def pack32(out, dw):
    for i in range(4):
      pack8(out, dw % 256)
      dw //= 256
    if (dw > 0):
        sys.exit("32Bit word out of range")

def packAngle(out, a):
    while a < 0:
        a += 360.0
    while a >= 360.0:
        a -= 360.0
    a /= 360.0
    a *= math.pow(2,32)
    a += 0.5
    a = math.floor(a)
    if a == math.pow(2,32):
        a = 0
    pack32(out, a)

#-----------------------

for c in cList:
    out = [bytearray()]

    # Export track name
    packStr(out, c['name'])

    # Export number of checkpoints
    pack8(out,len(c['ord']))

    if len(c['ord']) > 255:
        sys.exit("Too many conrols for format")
    if len(c['ix']) > 63:
        sys.exit("Too many conrols for format")

    # Export checkpoint type and index in order
    for i in c['ord']:
        pack8(out,
              (i['type'] % 4)
              + 4 * ( c['ctrls'][i['i']]['ix'] ))

    # Export number of checkpoints
    pack8(out,len(c['ix']))

    # Export control points
    for i in c['ix']:
        packStr(out, i[:4])  # Name max 4 chars
        packAngle(out, c['ctrls'][i]['lat'])
        packAngle(out, c['ctrls'][i]['lon'])

    # End marker
    pack8(out,0xEE)
    outstr = str(base64.b64encode(out[0]),'ascii')

    # Print out
    print("Track: " + c['name'])
    print("NumCheck: " + str(len(c['ord'])))
    print("CodeLen: " + str(len(outstr)))
    print("Code: " + outstr)
    print("")
