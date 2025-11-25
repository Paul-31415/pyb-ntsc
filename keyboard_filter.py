#
#[00:00:25.956]row:6,col:16      [SHORT]
#[00:00:26.100]row:6,col:16      [UP]
#
#[00:00:13.162]row:7,col:6       [SHORT]
#[00:00:13.163]row:7,col:8       [SHORT]
#[00:00:13.164]Phantom key...
#
#[00:00:20.305]bv:385, bl:7 , check_vbat:0
#[00:00:20.335]bv:385, bl:7 , check_vbat:0
#              
#regex:
#/\[([0-9]{2}:){2}[0-9]{2}\.[0-9]{3}\]/
#probably just look for newline and position of fixed chars
# i.e.
# line[0]=='[' and line[3]==':' and line[6]==':' and line[9]=='.' and line[13]==']row:'
#
#"\\[[0-9][0-9]:[0-9][0-9]:[0-9][0-9]\\.[0-9][0-9][0-9]\\]row:([0-9]+),col:([0-9]+)[ \t]*\\[(SHORT|UP)\\]"

#translation_table=
# 1234567890
# qwertyuiop
# asdfghjkl␡
# zxcvbnm;'␍
# fn shift alt , [space] . cmd ctrl fn
#
#(4,9),(4,16),(4,6),(4,8),(4,7),(4,5),(4,0),(4,4),(4,2),(4,3)
#(0,9),
#(7,9) ..............                                   (4,1)
#(1,9)                                      (1,3),(1,1),(7,3)
#(6,14),(6,9),(6,0),(1,4),   (6,5)   ,(1,2),(6,4),(7,1),(6,16)
import micropython
import pyb
import re
TIMESTAMP = "\\[[0-9][0-9]:[0-9][0-9]:[0-9][0-9]\\.[0-9][0-9][0-9]\\]"
KEY_RE = re.compile(TIMESTAMP+"row:([0-9]+),col:([0-9]+)\t\\[(SHORT|UP)\\]")
BATV_RE = re.compile(TIMESTAMP+"bv:([0-9]+),")

class bluekbd3601:
    def __init__(self,uart=6,baudrate=115200*9):
        self.uart = pyb.UART(uart)
        self.baudrate = baudrate
        self.rx = pyb.Pin([0,"X10","X4","Y10","X2",0,"Y2"][uart])
        self.high_water_mark=0
        self.bv = None
        self.state = 0
        self.over = b""
        self.irq_args = [0,None,self.update]
        def irq(line,a=self.irq_args):
            a[1].disable()
            if a[0]: return
            a[0] = 1
            micropython.schedule(a[2],a)
        self.irq = irq
        self.onkeydown = None
        self.onkeyup = None
    def init(self,buf_len=256):
        self.irq_args[1] = self.exint = pyb.ExtInt(self.rx,pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_UP, None)
        self.irq_args[1] = self.exint = pyb.ExtInt(self.rx,pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_UP, self.irq)
        self.uart.init(self.baudrate,timeout=1,timeout_char=1,read_buf_len=buf_len)
    def update(self,exint_stuff=None):
        self.high_water_mark = max(self.high_water_mark,self.uart.any())
        while self.uart.any():
            line = self.uart.readline()
            if line[14:18] == b"row:":
                m = KEY_RE.match(line)
                if m:
                    i = int(m.group(1)) + (int(m.group(2))<<3)
                    if m.group(3) == b'SHORT':
                        self.state |= 1<<i
                        if self.onkeydown:
                            self.onkeydown(i)
                    else:
                        self.state &= ~(1<<i)
                        if self.onkeyup:
                            self.onkeyup(i)
            elif line[14:17] == b'bv:':
                m = BATV_RE.match(line)
                if m:
                    self.bv = int(m.group(1))
        if exint_stuff:
            exint_stuff[0] = 0
            exint_stuff[1].enable()

keys = {76:"1",132:"2",52:"3",68:"4",60:"5",44:"6",4:"7",36:"8",20:"9",28:"0",
        72:"q",128:"w",48:"e",64:"r",56:"t",40:"y",0:"u",32:"i",16:"o",24:"p",
        79:"a",135:"s",55:"d",71:"f",63:"g",47:"h",7:"j",39:"k",23:"l",12:"\x7f",
        73:"z",129:"x",49:"c",65:"v",57:"b",41:"n",1:"m",25:";",9:"'",31:"\n",
        118:"l-fn",78:"shift",6:"alt",33:",",46:" ",17:".",38:"cmd",15:"ctrl",134:"r-fn"}

key_ids = [76,132,52,68,60,44,4,36,20,28,72,128,48,64,56,40,0,32,16,24,79,135,55,71,63,47,7,39,23,12,
           73,129,49,65,57,41,1,25,9,31,118,78,6,33,46,17,38,15,134]
KEY_IDS = {key_ids[i]:i for i in range(len(key_ids))}
LOWERCASE = "1234567890qwertyuiopasdfghjkl\x7fzxcvbnm;'\x0d\0\0\0, .\0\0\0"
UPPERCASE = '!@#$%^&*()QWERTYUIOPASDFGHJKL\x7fZXCVBNM:"\x0d\0\0\0< >\0\0\0'
FN = ["\0"]*10+["\x1b","\x1b[A","™","~","_","+","|","?","www.",".com","\x1b[D","\x1b[B","\x1b[C","`","-","=","\\","/","\0","\x08","capslock","Home","End","PgUp","PgDn","{","}","[","]","\0"]+["\0"]*9
