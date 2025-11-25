def fill_rect_curry(putc):
    def fill_rect(row,col,height,width,putc=putc):
        for r in range(row,row+height):
            for c in range(col,col+width):
                putc(32,r,c)
    return fill_rect
    
class cursor:
    def __init__(self,putc,scroll,cols=80,rows=24,fill_rect=None):
        self.putc = putc
        self.scroll = scroll
        self.cols = cols
        self.rows = rows
        self.x = 0
        self.y = 0
        self.fill_rect = fill_rect or fill_rect_curry(putc)
        #self.utf8 = 0 nah, not gonna expand utf8
        #self.codepoint = 0
        self.esc = False
    def inc_col(self,by=1):
        self.x += by
        by,self.x = divmod(self.x,self.cols)
        if by != 0:
            self.inc_row(by)
    def move_cursor(self,dx=0,dy=0):
        self.x = min(self.cols,max(0,self.x+dx))
        self.y = min(self.rows,max(0,self.x+dx))
    def inc_row(self,by=1):
        self.y += by
        if self.y >= self.rows:
            self.scroll(1+self.y-self.rows)
            self.y = self.rows-1
    def writebyte(self,b):
        if self.esc:
            if len(self.esc)==1:
                self.esc.append(chr(b))
            elif self.esc[1] == '[':
                if 0x30 <= b <= 0x3f:
                    if b < 0x3a:
                        if type(self.esc[-1]) == int:
                            self.esc[-1] = 10*self.esc[-1] + b-0x30
                        else:
                            self.esc.append(b-0x30)
                    else:
                        self.esc.append(chr(b))
                elif 0x20 <= b <= 0x2f:
                    self.esc.append(chr(b))
                elif 0x40 <= b <= 0x7e:
                    self.esc.append(chr(b))
                    self.esc = self.escape(self.esc)
            else:
                self.esc.append(chr(b))
                self.esc = self.escape(self.esc)
        elif b < 32:
            if b == 8:
                self.inc_col(-1)
            elif b == 10:
                self.inc_row()
            elif b == 13:
                self.x = 0
            elif b == 27:
                self.esc = [chr(b)]
        else:
            self.putc(b,self.x,self.y)
            self.inc_col()
    def write(self,data):
        for b in data:
            self.writebyte(b)
    def escape(self,seq):
        if seq[1] == "[":
            if seq[-1] == {'A','B','C','D'}:
                a = seq[-2] if type(seq[-2]) == int else 1
                if seq[-1] == 'A':
                    self.move_cursor(0,-a)
                elif seq[-1] == 'B':
                    self.move_cursor(0,a)
                elif seq[-1] == 'C':
                    self.move_cursor(a,0)
                else:
                    self.move_cursor(-a,0)
            elif seq[-1] == 'K':
                if seq[-2] == 1:
                    self.fill_rect(0,self.y,self.x,1)
                elif seq[-2] == 2:
                    self.fill_rect(0,self.y,self.cols,1)
                else:
                    self.fill_rect(self.x,self.y,self.cols-self.x,1)
    def readinto(self,*a):
        return None
    
#  123456
#1  ###   
#2 #   #
#4 # # # 
#8 # # #
#1 # ###
#2 #   
#4  #### 
#8 @ABCDEFGHIJKLMNOPQRSTUVWXYZ

    
font6x8 = b"\0\0\0\0\0\0\0\0\x5f\0\0\0\0\x03\0\x03\0\0\x14\x7f\x14\x7f\x14\0\x24\x2a\x7f\x2a\x10\0\x62\x15\x2a\x54\x23\0\x36\x49\x56\x20\x50\0\0\0\x03\0\0\0"\
    b"\x1c\x22\x22\x41\x41\0\x41\x41\x22\x22\x1c\0\x04\x15\x0e\x15\x04\0\x08\x08\x3e\x08\x08\0\0\0\x50\x30\0\0\x08\x08\x08\x08\x08\0\0\0\x60\x60\0\0\x40\x30\x08\x06\x01\0"\
    b"\x3e\x51\x49\x45\x3e\0\x40\x42\x7f\x40\x40\0\x42\x61\x51\x49\x46\0\x22\x41\x49\x49\x36\0\x18\x14\x12\x7f\x10\0\x27\x45\x45\x45\x39\0\x3c\x4a\x49\x49\x30\0\x01\x61\x19\x05\x03\0"\
    b"\x36\x49\x49\x49\x36\0\x06\x49\x49\x49\x3e\0\0\x36\x36\0\0\0\0\x56\x36\0\0\0\x08\x14\x14\x22\x22\0\x14\x14\x14\x14\x14\0\x22\x22\x14\x14\x08\0\x02\x01\x59\x05\x02\0"\
    b"\x3e\x41\x5d\x51\x5e\0"



#font editor
import sys
import uselect
spoll = uselect.poll()
spoll.register(sys.stdin, uselect.POLLIN)
def read_stdin_nonblocking():
    for a,b in spoll.ipoll(0):
        return a.read(1)

font6x8 = bytearray(6*96)
def edit_font(font,w=6,offs=32):
    pallette = framebuf.FrameBuffer(bytearray((77,170)),2,1,framebuf.GS8)
    mv = memoryview(font)
    def charfb(c):
        return framebuf.FrameBuffer(mv[(c-offs)*6:],6,8,framebuf.MONO_VLSB)
    def putc(c,x,y):
        t.fb.blit(charfb(c),x,y,-1,pallette)
    cx = 0
    cy = 0
    def draw(c):
        t.fb.fill(77)
        t.fb.text(chr(c),100,90,170)
        putc(c,94,108)
        putc(c,100,108)
        putc(c,106,108)
        b = charfb(c)
        for x in range(6):
            for y in range(8):
                t.fb.rect(120+x*12,50+y*12,12,12,[100,124][cx==x and cy==y])
                t.fb.rect(121+x*12,51+y*12,10,10,[77,170][b.pixel(x,y)],1)
    def toggle(c):
        b = charfb(c)
        b.pixel(cx,cy,1-b.pixel(cx,cy))
        draw(c)
    c = 32
    while 1:
        r = read_stdin_nonblocking()
        if r is not None:
            if r == '\x1b':
                e = sys.stdin.read(2)
                if e == '[D':
                    cx = (cx-1)%6
                    draw(c)
                elif e == '[C':
                    cx = (cx+1)%6
                    draw(c)
                if e == '[A':
                    cy = (cy-1)%8
                    draw(c)
                elif e == '[B':
                    cy = (cy+1)%8
                    draw(c)
            elif r == ' ':
                toggle(c)
            elif r == "n":
                c += 1
                draw(c)
            elif r == "p":
                c -= 1
                draw(c)
            elif r == "d":
                return

#really uneven weight
font6x8 = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00O\x00\x00\x00\x00\x07\x00\x07\x00\x00\x14\x7f\x14\x7f\x14\x00$*\x7f*\x10\x00b\x15*T#\x006IV P\x00\x00\x00\x07\x00\x00\x00\x00\x1c"A\x00\x00\x00A"\x1c\x00\x00\x04\x15\x0e\x15\x04\x00\x00\x08>\x08\x00\x00\x00@0\x00\x00\x00\x00\x08\x08\x08\x00\x00\x00\x00@\x00\x00\x00@0\x08\x06\x01\x00>sIg>\x00DB\x7f\x7f@\x00fsYOF\x00"cI\x7f6\x00\x0c\x0e{\x7f\x08\x00\'gE}9\x00<~Ky0\x00\x01q}\x0f\x03\x006\x7fI\x7f6\x00\x06OI\x7f>\x00\x0033\x00\x00\x00@s3\x00\x00\x00\x08\x1c\x146"\x00\x14\x14\x14\x14\x00\x00"6\x14\x1c\x08\x00\x06\x03Y_\x06\x00>A]Q^\x00~\x7f\t\x7f~\x00\x7f\x7fI\x7f6\x00>\x7fAc"\x00\x7f\x7fA\x7f>\x00\x7f\x7fIIA\x00\x7f\x7f\t\t\x01\x00>wI{:\x00\x7f\x7f\x08\x7f\x7f\x00A\x7f\x7fA\x00\x000qA\x7f?\x00\x7f\x7f\x1cwc\x00\x7f\x7f@@\x00\x00\x7f\x02\x0c\x02\x7f\x00\x7f\x02\x1c \x7f\x00>\x7fA\x7f>\x00\x7f\x7f\t\x0f\x06\x00>AQ!^\x00\x7f\x7f\x19\x7ff\x00&oI{2\x00\x01\x7f\x7f\x01\x00\x00?\x7f@\x7f?\x00\x03\x1c`\x1c\x03\x00\x1f`\x18`\x1f\x00A6\x086A\x00\x01\x06x\x06\x01\x00ay]OC\x00\x00\x7f\x7fAA\x00\x01\x06\x080@\x00AA\x7f\x7f\x00\x00\x04\x02\x01\x02\x04\x00@@@@\x00\x00\x00\x00\x01\x02\x00\x000zJ~|\x00\x7f\x7fD|8\x008|DD\x00\x008|D\x7f\x7f\x008|T\\X\x00\x08~\x7f\t\x01\x00l^R~>\x00\x7f\x7f\x08xp\x00\x00\x00z\x00\x00\x00 @:\x00\x00\x00\x7f\x7f8lD\x00\x00\x00?@\x00\x00x\x08p\x08p\x00xx\x08xp\x008|D|8\x00||\x14\x1c\x08\x00\x08\x1c\x14||\x00|x\x0c\x18\x10\x00H\\Tt \x00\x04?\x7fD\x00\x008x@xx\x00\x080@0\x08\x00\x18`\x18`\x18\x00D(\x10(D\x00\x0c\\P|<\x00dtT\\L\x00\x00\x086A\x00\x00\x00\x00\x7f\x00\x00\x00\x00A6\x08\x00\x00\x08\x04\x08\x10\x08\x00\xaaU\xaaU\xaaU')
def type6x8(msg,x,y,fg,bg=-1,font=font6x8,fontwidth=6,fontoffs=32):
    pallette = framebuf.FrameBuffer(bytearray((bg if bg >= 0 else 0,fg if fg >= 0 else 0)),2,1,framebuf.GS8)
    mv = memoryview(font)
    for c in msg:
        if ord(c) >= fontoffs:
            t.fb.blit(framebuf.FrameBuffer(mv[(ord(c)-fontoffs)*fontwidth:],fontwidth,8,framebuf.MONO_VLSB),x,y,0 if bg < 0 else 1 if fg < 0 else -1,pallette)
        x += fontwidth
            


def edit_font(font,w=6,offs=32):
    pal = bytearray((77,100,130,170))
    pallette = framebuf.FrameBuffer(pal,4,1,framebuf.GS8)
    mv = memoryview(font)
    def charfb(c):
        return framebuf.FrameBuffer(mv[(c-offs)*16:],6,8,framebuf.GS2_HMSB)
    def putc(c,x,y):
        t.fb.blit(charfb(c),x,y,-1,pallette)
    cx = 0
    cy = 0
    def draw(c):
        t.fb.fill(77)
        t.fb.text(chr(c),100,90,170)
        putc(c,94,108)
        putc(c,100,108)
        putc(c,106,108)
        b = charfb(c)
        for x in range(6):
            for y in range(8):
                t.fb.rect(120+x*12,50+y*12,12,12,[100,124][cx==x and cy==y])
                t.fb.rect(121+x*12,51+y*12,10,10,pal[b.pixel(x,y)],1)
        for i in range(offs,127):
            putc(i,50+((i-offs)%16)*6,((i-offs)//16)*8+150)
    def toggle(c):
        b = charfb(c)
        b.pixel(cx,cy,(b.pixel(cx,cy)+1)&3)
        draw(c)
    c = 32
    while 1:
        r = read_stdin_nonblocking()
        if r is not None:
            if r == '\x1b':
                e = sys.stdin.read(2)
                if e == '[D':
                    cx = (cx-1)%6
                    draw(c)
                elif e == '[C':
                    cx = (cx+1)%6
                    draw(c)
                if e == '[A':
                    cy = (cy-1)%8
                    draw(c)
                elif e == '[B':
                    cy = (cy+1)%8
                    draw(c)
            elif r == ' ':
                toggle(c)
            elif r == "n":
                c += 1
                draw(c)
            elif r == "p":
                c -= 1
                draw(c)
            elif r == "d":
                return






font6x8_2b = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x000\x000\x000\x000\x00\x00\x00\x00\x000\x00\x00\x00\xcc\x00\xcc\x00\xcc\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xcc\x00\xcc\x00\xaa\x02\xcc\x00\xaa\x02\xcc\x00\xcc\x00\x00\x000\x00\xa9\x013\x00\xa9\x010\x03\xa9\x010\x00\x00\x00)\x03s\x02\xd9\x01t\x00\x9d\x016\x03\x93\x02\x00\x00,\x003\x003\x00\x1d\x007\x02\xd3\x00)\x03\x00\x000\x000\x000\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xa4\x00\x19\x00\x07\x00\x03\x00\x07\x00\x19\x00\xa4\x00\x00\x00h\x00\x90\x01@\x03@\x03@\x03\xd0\x01h\x00\x00\x00\xdc\x00\xb4\x00\xaa\x02\xb4\x00\xdc\x00\x00\x00\x00\x00\x00\x00\x10\x000\x000\x00\xaa\x020\x000\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x000\x00$\x00\x00\x00\x00\x00\x00\x00\x00\x00\xaa\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x004\x004\x00\x00\x00@\x02\x80\x01\x90\x00d\x00\x18\x00\t\x00\x06\x00\x00\x00\xa9\x02G\x03\xa7\x03w\x03k\x03G\x03\xa9\x02\x00\x004\x009\x007\x000\x000\x000\x00\xaa\x02\x00\x00\xa9\x01\x8a\x02\x03\x03\x90\x02\xa9\x01\x1a\x00\xaa\x02\x00\x00\xa9\x02\x1a\x03A\x03\xa0\x02A\x03\x1a\x03\xa9\x02\x00\x00\xa0\x01\xe4\x00\xc9\x00\xc3\x00\xaa\x02\xc0\x00\xc0\x00\x00\x00\xaa\x02\x03\x00\xaa\x01@\x03\x00\x03G\x03\xa9\x01\x00\x00\xa8\x01\n\x02\x03\x00\xab\x01\x07\x03\n\x03\xa9\x01\x00\x00\xaa\x02@\x03\x80\x02\xd0\x01\xa0\x00p\x000\x00\x00\x00\xa9\x02G\x03\x03\x03\xa9\x02\x03\x03G\x03\xa9\x02\x00\x00\xa9\x02\x03\x03\x03\x03\xa9\x02\x00\x03\x80\x02\xa8\x00\x00\x00\x00\x004\x004\x00\x00\x004\x004\x00\x00\x00\x00\x00\x00\x004\x004\x00\x00\x004\x004\x00(\x00\x00\x00\x00\x00\x90\x02i\x00\x07\x00i\x00\x90\x02\x00\x00\x00\x00\x00\x00\x00\x00\xaa\x00\x00\x00\xaa\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1a\x00\xa4\x01\x00\x03\xa4\x01\x1a\x00\x00\x00\x00\x00\xa8\x01\x07\x03B\x02\x90\x004\x00\x00\x004\x00\x00\x00\xa9\x01G\x03s\x037\x03\xa3\x02G\x00\xa9\x02\x00\x00p\x00\xa4\x00\x8c\x01\x89\x01\xa9\x02F\x02\x03\x03\x00\x00\xaa\x01C\x02C\x02\xaa\x01C\x02C\x02\xaa\x01\x00\x00\xa9\x01J\x02\x07\x00\x03\x00\x07\x00J\x02\xa9\x01\x00\x00\xaa\x01C\x02\x03\x03\x03\x03\x03\x03C\x02\xaa\x01\x00\x00\xaa\x02\x03\x00\x03\x00\xaa\x01\x03\x00\x03\x00\xaa\x02\x00\x00\xaa\x02\x03\x00\x03\x00\xaa\x01\x03\x00\x03\x00\x03\x00\x00\x00\xa9\x01J\x02\x07\x00\xa3\x02g\x02J\x02\xa9\x01\x00\x00\x03\x03\x03\x03\x03\x03\xaa\x03\x03\x03\x03\x03\x03\x03\x00\x00\xaa\x020\x000\x000\x000\x000\x00\xaa\x02\x00\x00\xa4\x02\xc0\x00\xc0\x00\xc0\x00\xc2\x00\x96\x00i\x00\x00\x00C\x03\xd3\x007\x00*\x007\x00\xd3\x00C\x03\x00\x00\x03\x00\x03\x00\x03\x00\x03\x00\x03\x00\x03\x00\xaa\x02\x00\x00G\x03\x9a\x03\xaa\x033\x03\x03\x03\x03\x03\x03\x03\x00\x00\x07\x03\x1b\x03+\x033\x03\xa3\x03\x93\x03C\x03\x00\x00\xa8\x01J\x02\x03\x03\x03\x03\x03\x03J\x02\xa8\x01\x00\x00\xaa\x01C\x02C\x02\xaa\x01\x03\x00\x03\x00\x03\x00\x00\x00\xa8\x01\x8a\x02G\x03\x03\x037\x03\xca\x00x\x03\x00\x00\xaa\x01C\x03C\x03\xaa\x02\xa3\x00\x83\x02C\x03\x00\x00\xa9\x01G\x02\x03\x00\xa9\x01@\x02F\x02\xa9\x01\x00\x00\xaa\x020\x000\x000\x000\x000\x000\x00\x00\x00\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03F\x02\xa9\x01\x00\x00\x03\x03J\x02\x89\x02\xcc\x00\xa8\x000\x000\x00\x00\x00\x03\x03\x13\x033\x03w\x03\xaa\x02\xdd\x01\xcc\x00\x00\x00\x03\x03\xcd\x02\xa8\x01t\x00\xa8\x01\xcd\x02\x03\x03\x00\x00\x03\x03J\x02\x99\x01\xa8\x00t\x000\x000\x00\x00\x00\xaa\x02\x00\x03\xc0\x000\x00\x0c\x00\x03\x00\xaa\x02\x00\x00\xa0\x020\x000\x000\x000\x000\x00\xa0\x02\x00\x00\x03\x00\t\x00\x18\x004\x00\x90\x00\x80\x02\x00\x03\x00\x00j\x000\x000\x000\x000\x000\x00j\x00\x00\x00t\x00\xdd\x01G\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xaa\x02\x00\x00p\x00\xd0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xa9\x01@\x03\xa9\x03\x07\x03\xa9\x02\x00\x00\x03\x00\x03\x00\xa7\x01k\x02\x03\x03K\x02\xaa\x01\x00\x00\x00\x00\x00\x00\xa9\x01F\x02\x03\x00F\x02\xa9\x01\x00\x00\x00\x03\x00\x03i\x03\x96\x03\x03\x03F\x03\xa9\x03\x00\x00\x00\x00\x00\x00\xa9\x01\x87\x02\xab\x02G\x00\xa9\x01\x00\x00\xa4\x02L\x03\x0c\x00\xaa\x00\x0c\x00\x0c\x00\x0c\x00\x00\x00\x00\x00\x00\x00\xa9\x02\x06\x03\xa9\x02@\x03\xa9\x01\x00\x00\x03\x00\x03\x00\xa7\x01k\x02\x07\x03\x03\x03\x03\x03\x00\x00\x00\x004\x00\x00\x00\xa4\x000\x000\x00\xa8\x01\x00\x00\x00\x00\xc0\x00\x00\x00\xe0\x02\xc0\x00\xc8\x00\xa4\x00\x00\x00\x03\x00\x03\x00C\x03\xa7\x01*\x00\xa7\x01C\x03\x00\x00h\x000\x000\x000\x000\x000\x00\xa8\x01\x00\x00\x00\x00\x00\x00\xab\x02w\x033\x033\x033\x03\x00\x00\x00\x00\x00\x00\xa7\x01Z\x02\x03\x03\x03\x03\x03\x03\x00\x00\x00\x00\x00\x00\xa8\x01J\x02\x07\x03J\x02\xa8\x01\x00\x00\x00\x00\x00\x00\xaa\x01C\x02C\x02\xaa\x01\x03\x00\x00\x00\x00\x00\x00\x00\xa9\x03\x06\x03\x96\x03i\x03\x00\x03\x00\x00\x00\x00\x00\x00\xa7\x02\x1a\x03\x03\x00\x03\x00\x03\x00\x00\x00\x00\x00\x00\x00\xa9\x01\x07\x01\xa9\x01E\x03\xaa\x01\x00\x000\x000\x00\xa8\x020\x000\x00p\x03\xd0\x01\x00\x00\x00\x00\x00\x00\x03\x03\x03\x03C\x03\xa6\x03h\x03\x00\x00\x00\x00\x00\x00\x03\x03\x8a\x02\xcc\x00\xa8\x000\x00\x00\x00\x00\x00\x00\x00\x03\x033\x03v\x03\xaa\x02\xcc\x00\x00\x00\x00\x00\x00\x00\x03\x03\xcc\x000\x00\xcc\x00\x03\x03\x00\x00\x00\x00\x00\x00\x03\x03J\x02\xa9\x02@\x02\xa8\x01\x00\x00\x00\x00\x00\x00\xaa\x02\xc0\x000\x00\x0c\x00\xaa\x02\x00\x00\x90\x02\xb0\x000\x00\x1c\x000\x00\xb0\x00\x90\x02\x00\x000\x000\x000\x000\x000\x000\x000\x00\x00\x00*\x00$\x000\x00\xd0\x000\x00$\x00*\x00\x00\x00\x00\x00\x00\x00-\x003\x03\xd0\x02\x00\x00\x00\x00\x00\x00U\x01U\x01U\x01U\x01U\x01U\x01U\x01\x00\x00')



def type6x8_2b(msg,x,y,a=170,b=130,c=100,d=77,font=font6x8_2b,fontwidth=6,fontoffs=32):
    pal = bytearray((d&255,c,b,a))
    pallette = framebuf.FrameBuffer(pal,4,1,framebuf.GS8)
    mv = memoryview(font)
    for c in msg:
        if ord(c) >= fontoffs:
            t.fb.blit(framebuf.FrameBuffer(mv[(ord(c)-fontoffs)*16:],fontwidth,8,framebuf.GS2_HMSB),x,y,0 if d < 0 else -1,pallette)
        x += fontwidth

#tv bounds:         far bound;               ok bound
# t.fb.fill(77);t.fb.rect(16,15,190,208,170);t.fb.rect(18,19,185,200,170);
#


c = cursor(lambda c,x,y: type6x8_2b(chr(c),20+x*6,20+y*8),lambda dy: (t.fb.scroll(0,-8*dy),t.fb.rect(0,220-8*dy,300,300,77,1)),30,25)

import uio
class pystream(uio.IOBase):
    def __init__(self,write_cb = len,readinto_cb=lambda b:None):
        self.wcb = write_cb
        self.ricb = readinto_cb
    def write(self,b):
        return self.wcb(b)
    def readinto(self,b):
        return self.ricb(b)


def utf8_to_codepoints():
    b = yield
    while 1:
        while not b&128:
            b = yield b
        if not b&0x40:
            b = yield -b #err
        else:
            c = b&0x1f
            m = -0x20
            while b & 0x40:
                n = yield
                c = (c<<6) | (n&0x3f)
                m <<= 5
                if n & 0xc0 != 0x80:
                    b = yield -n
                    break
                b <<= 1
            b = yield c&~m


def nop(*a,**ka):
    pass
            
def ansi_mux(normal_chars=nop,control_chars=nop,csi=nop,dcs=nop,sos=nop,osc=nop,pm=nop,apc=nop):
    while 1:
        c = yield
        if c >= 32:
            if 0x80 <= c <= 0x9f:
                control_chars(c)
            normal_chars(c)
        elif c == 27:
            t = yield
            if 0x40 <= t <= 0x5f:
                if t == 0x5b:
                    c2 = yield
                    while 0x30 <= c2 <= 0x3f:
                        csi(c2)
                        c2 = yield
                    while 0x20 <= c2 <= 0x2f:
                        csi(c2)
                        c2 = yield
                    csi(c2)
                    continue
                elif t in {0x50,0x58,0x5d,0x5e,0x5f}:
                    sink = {0x50:dcs,0x58:sos,0x5d:osc,0x5e:pm,0x5f:apc}[t]
                    while 1:
                        c2 = yield
                        if c2 == 27:
                            t2 = yield
                            if t2 == 0x5c:
                                sink()
                                break
                            sink(c2)
                            sink(t2)
                        else:
                            sink(c2)
                else:
                    control_chars(t^0xc0)
        else:
            control_chars(c)


#observed codes used by the pyboard:
# \r\n
# \x08      for short movement
# \x1b[#D   for ^A and up/down arrows
# \x1b[K    for editing the middle of the buffer

def csi_curry(self):
    def csi_iter(c):
        while 1:
            args = [0]
            intermediate = ""
            c = yield
            while 0x30 <= c <= 0x3f:
                if c <= 0x39:
                    args[-1] *= 10
                    args[-1] += c-0x30
                else:
                    args.append(chr(c))
                    args.append(0)
                c = yield
            while 0x20 <= c <= 0x2f:
                intermediate += chr(c)
                c = yield
            if c == 0x41: self.move_cursor_by(-(args[-1] or 1),0)
            elif c == 0x42: self.move_cursor_by(args[-1] or 1,0)
            elif c == 0x43: self.move_cursor_by(0,args[-1] or 1)
            elif c == 0x44: self.move_cursor_by(0,-(args[-1] or 1))
            elif c == 0x48: self.move_cursor_to(((len(args)>=3 and args[-3]) or 1)-1,(args[-1] or 1)-1)
            elif c == 0x4a: self.erase_in_display(args[-1])
            elif c == 0x4b: self.erase_in_line(args[-1])
            elif c == 0x6d: self.select_graphic_rendition(args)
            else: self.csi(c,args,intermediate)
    ci = csi_iter()
    ci.send(None)
    def csi(c,s=[ci]):
        s[0].send(c)
    return csi

class TermCursor(uio.IOBase):
    def __init__(self,putc,vscroll,cols=80,rows=24,fill_rect=None):
        self.row = 0
        self.col = 0
        self.cols = cols
        self.rows = rows
        self.line_starts = 0
        self.readinto_cb = lambda b:None
        self.utf8 = utf8_to_codepoints()
        self.utf8.send(None)
        self.csi = csi_curry(self)
        self.amux = ansi_mux(self.normal_char,self.control_char,self.csi)
        self.amux.send(None)
        self.style = set()
        self.font = 10
        self.fg_color_default = self.fg_color = 15
        self.bg_color_default = self.bg_color = 0
        self.putc = putc
        self.vscroll = vscroll
        if fill_rect is None:
            def fill_rect(char,rowl,coll,rowh,colh,putc=putc):
                for r in range(row,rowh):
                    for c in range(col,colh):
                        putc(char,r,c)
        self.fill_rect = fill_rect
    def readinto(self,b):
        return self.readinto_cb(b)
    def write(self,b):
        for c in b:
            self.writebyte(c)
    def writebyte(self,b):
        v = self.utf8.send(b&255)
        if v is not None and v >= 0:
            self.writechar(v)
    def writechar(self,c):
        self.amux.send(c|0)
    def move_cursor_to(self,row=None,col=None):
        if row is not None: self.row = min(self.rows-1,max(0,row))
        if col is not None: self.col = min(self.cols-1,max(0,col))
    def move_cursor_by(self,row=0,col=0):
        self.move_cursor_to(row+self.row,col+self.col)
    def move_cursor_wrap(self,cols=0):        
        d,self.col = divmod(self.col+cols,self.cols)
        d += self.row
        self.move_cursor_to(d)
        if d != self.row:
            self.vscroll(d-self.row)
    def normal_char(self,c):
        self.putc(c,self.row,self.col,self.style)
        self.move_cursor_wrap(1)
    def control_char(self,c):
        if c == 7:
            if hasattr(self,bell): self.bell()
        elif c == 8:
            self.move_cursor_wrap(-1)
        elif c == 9:
            self.move_cursor_wrap(1+((self.col&7)^7))
        elif c == 10:
            self.move_cursor_wrap(self.cols)
            self.line_starts |= 1<<self.row
        elif c == 11:
            self.move_cursor_wrap(self.cols*(1+((self.row&3)^3)))
        elif c == 12:
            self.scroll(self.rows)
            self.move_cursor_to(0,self.col)
        elif c == 13:
            self.move_cursor_to(self.row,0)
        elif c == 133:
            self.move_cursor_wrap(self.cols-self.col)
            self.line_starts |= 1<<self.row
    def erase_in_display(self,mode):
        if mode == 0: self.fill_rect(32,self.row,self.col,self.row+1,self.cols)
        elif mode == 1: self.fill_rect(32,self.row,0,self.row+1,self.col+1)
        elif mode == 2: self.fill_rect(32,0,0,self.rows,self.cols)
    def erase_in_line(self,mode):
        if mode == 0: self.fill_rect(32,self.row,self.col,self.row+1,self.cols)
        elif mode == 1: self.fill_rect(32,self.row,0,self.row+1,self.col+1)
        if mode == 0 or mode == 2:
            e = self.row+1
            while not (self.line_starts>>e)&1 and e < self.rows:
                e += 1
            if mode == 0 and e > self.row+1: self.fill_rect(32,self.row+1,0,e,self.cols)
        if mode == 1 or mode == 2:
            s = self.row
            while not (self.line_starts>>s)&1 and s >= 0:
                s -= 1
            if mode == 1 and s < self.row: self.fill_rect(32,s,0,self.row,self.cols)
        if mode == 2: self.fill_rect(32,s,0,e,self.cols)
    def select_graphic_rendition(self,args):
        while ';' in args:
            i = args.index(';')
            self.select_graphic_rendition_1(args[:i])
            args = args[i+1:]
        self.select_graphic_rendition_1(args)
    def select_graphic_rendition_1(self,args):
        if args[0] == 0:
            self.style.clear()
            self.font = 10
            self.fg_color = self.fg_color_default
            self.bg_color = self.bg_color_default
        elif args[0] < 10:
            self.style.add(args[0])
        elif args[0] <= 20:
            self.font = args[0]
        elif args[0] < 30:
            self.style.discard(args[0]-20)            
        elif args[0] < 38:
            self.fg_color = args[0]-30
        elif args[0] == 49:
            self.fg_color = args
        elif args[0] == 39:
            self.fg_color = 15
        elif args[0] < 48:
            self.bg_color = args[0]-40
        elif args[0] == 48:
            self.bg_color = args
        elif args[0] == 49:
            self.bg_color = 0
        elif args[0] < 90:
            pass
        elif args[0] < 98:
            self.fg_color = args[0]-82
        elif args[0] < 100:
            pass
        elif args[0] < 108:
            self.bg_color = args[0]-92
    def csi(self,cmd,args,intermediate):
        pass








import array
class term(uio.IOBase):
    def __init__(self,cols=80,rows=24):
        self.row = 0
        self.col = 0
        self.cols = cols
        self.rows = rows
        self.chars = array.array("i",bytearray(rows*cols*4))
        self.cmv = memoryview(self.chars)
        self.cfb = framebuf.FrameBuffer(self.chars,cols*2,rows,framebuf.RGB565)
        self.line_starts = 0
        self.readinto_cb = lambda b:None
        self.utf8 = utf8_to_codepoints()
        self.utf8.send(None)
        self.amux = ansi_mux(self.normal_char,self.control_char,self.csi)
        self.amux.send(None)
        self.style = 0
    def readinto(self,b):
        return self.readinto_cb(b)
    def write(self,b):
        for c in b:
            self.writebyte(c)
    def writebyte(self,b):
        v = self.utf8.send(b&255)
        if v is not None and v >= 0:
            self.writechar(v)
    def writechar(self,c):
        self.amux.send(c|0)
    def __getitem__(self,k):
        if isinstance(k,tuple):
            k = k[0]*self.cols + k[1]
        return self.chars[k]
    def __setitem__(self,k,v):
        if isinstance(k,tuple):
            k = k[0]*self.cols + k[1]
        self.chars[k] = v
    def move_cursor_to(self,row=None,col=None):
        if row is not None: self.row = min(self.rows-1,max(0,row))
        if col is not None: self.col = min(self.cols-1,max(0,col))
    def move_cursor_by(self,row=0,col=0):
        self.move_cursor_to(row+self.row,col+self.col)
    def scroll(self,rows=0):
        if rows > 0: #scroll text up
            self.cmv[:-rows*self.cols] = self.cmv[rows*self.cols:]
            self.line_starts >>= rows 
            self.cfb.rect(0,self.rows-rows,self.cols*2,rows,0,1)
        if rows < 0: #scroll text down
            self.cmv[-rows*self.cols:] = self.cmv[:rows*self.cols]
            self.line_starts <<= min(self.rows,-rows)
            self.line_starts &= (1<<self.rows-1)
            self.cfb.rect(0,0,self.cols*2,-rows,0,1)
    def move_cursor_wrap(self,cols=0):
        d,self.col = divmod(self.col+cols,self.cols)
        d += self.row
        self.move_cursor_to(d)
        if d != self.row:
            self.scroll(d-self.row)
    def normal_char(self,c):
        self.chars[self.row,self.col] = c|(self.style<<21)
        self.move_cursor_wrap(1)
    def control_char(self,c):
        if c == 7:
            if hasattr(self,bell): self.bell()
        elif c == 8:
            self.move_cursor_wrap(-1)
        elif c == 9:
            self.move_cursor_wrap(1+((self.col&7)^7))
        elif c == 10:
            self.move_cursor_wrap(self.cols)
            self.line_starts |= 1<<self.row
        elif c == 11:
            self.move_cursor_wrap(self.cols*(1+((self.row&3)^3)))
        elif c == 12:
            self.scroll(self.rows)
            self.move_cursor_to(0,self.col)
        elif c == 13:
            self.move_cursor_to(self.row,0)
        elif c == 133:
            self.move_cursor_wrap(self.cols-self.col)
            self.line_starts |= 1<<self.row
    def erase_in_display(self,mode):
        if mode == 0: self.cfb.hline(self.col*2,self.row,(self.cols-self.col)*2,0)
        elif mode == 1: self.cfb.hline(0,self.row,self.col*2,0)
        elif mode == 2: self.cfb.fill(0)
    def erase_in_line(self,mode):
        if mode == 0: self.cfb.hline(self.col*2,self.row,(self.cols-self.col)*2,0)
        elif mode == 1: self.cfb.hline(0,self.row,self.col*2,0)
        elif mode == 2: self.cfb.hline(0,self.row,self.cols*2,0)
        if mode == 0 or mode == 2:
            r = self.row+1
            while not (self.line_starts>>r)&1 and r < self.rows:
                self.cfb.hline(0,r,self.cols*2,0)
                r += 1
        if mode == 1 or mode == 2:
            r = self.row
            while not (self.line_starts>>r)&1 and r >= 0:
                r -= 1
                self.cfb.hline(0,r,self.cols*2,0)
    def select_graphic_rendition(self,args):
        if args[0] == 0:
            self.style = 0
        #11 bits free for style
        #styles 1-9 (bold, underline, invert, underline, blink, -, swap fg/bg, -, -) incompatability matrix:
        #
    def csi(self,cmd,args,intermediate):
        pass
    
