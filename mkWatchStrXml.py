#!/usr/bin/python3

import sys,re,os,math,base64
from decimal import Decimal

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

#---------------------------------------------------------
# Load all data and get relevant data

import xml.etree.ElementTree as ET

def xmlFirst(node,key):
    return [x for x in node if x.tag.endswith(key)][0]

def xmlAll(node,key):
    return [x for x in node if x.tag.endswith(key)]

def typeIx(s):
    if s == "Start":
        return 0;
    if s == "Finish":
        return 2;
    return 1;


tree      = ET.parse(legFile)
root      = tree.getroot()
rcData    = xmlFirst(root, "RaceCourseData")
rcCtrls   = xmlAll(rcData, "Control")
rcCourses = xmlAll(rcData, "Course")
rcCourseAssignments = xmlAll(rcData, "ClassCourseAssignment")


#---------------------------------------------------------
# Controls

cCtrlsAll = {}

for c in rcCtrls:
    name = xmlFirst(c, "Id").text.strip()
    pos =  xmlFirst(c, "Position")
    cCtrlsAll[name] = {
        'lat' : Decimal(pos.get('lat').strip()),
        'lon' : Decimal(pos.get('lng').strip()) }

#---------------------------------------------------------
# Courses

cAssign = {}

for cassign in rcCourseAssignments:
    className = xmlFirst(cassign, "ClassName").text.strip()
    courseName = xmlFirst(cassign, "CourseName").text.strip()
    cl = cAssign[courseName] = cAssign.get(courseName,[]);
    cl.append(className);

#---------------------------------------------------------
# Courses

cList = []

for course in rcCourses:

    cName = xmlFirst(course, "Name").text.strip()
    cCtrls = {}
    cOrder = []
    nextIx = 0
    cIx = []

    for cntrl in xmlAll(course, "CourseControl"):
        cntrlType = typeIx(cntrl.get("type"))
        cntrlName = xmlFirst(cntrl, "Control").text.strip()

        if cntrlName not in cCtrls:
            cCtrls[cntrlName] = cCtrlsAll[cntrlName].copy();
            cCtrls[cntrlName]['ix'] = nextIx
            nextIx += 1;
            cIx.append(cntrlName)

        cOrder.append({
            'i':cntrlName,
            'type':cntrlType})

    cList.append(
        { 'name' : cName,
          'id' : len(cList),
          'ord' : cOrder,
          'ix' : cIx,
          'ctrls' : cCtrls })

#---------------------------------------------------------
# Export

def packStr(out,s):
    if (len(s) > 255):
        sys.exit("Too long string")
    out[0].append(len(s))
    for c in s:
        cc = ord(c)
        if cc <	32 or cc > 127:
            cc = 95 # '_' sym
        out[0].append(cc)

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
    a /= Decimal(360.0)
    a *= Decimal(math.pow(2,32))
    a += Decimal(0.5)
    a = int(math.floor(a))
    if a >= math.pow(2,32):
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
        packStr(out, i[:4])  # Name, max 4 chars
        packAngle(out, c['ctrls'][i]['lat'])
        packAngle(out, c['ctrls'][i]['lon'])

    # End marker
    pack8(out,0xEE)
    outstr = str(base64.b64encode(out[0]))

    # Print out
    print("Track: " + c['name'])
    print("Classes: " + ", ".join(cAssign.get(c['name'],[])))
    print("NumCheck: " + str(len(c['ord'])))
    print("CodeLen: " + str(len(outstr)))
    print("Code: " + outstr)
    print("")
