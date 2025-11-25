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
    def csi_iter():
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
    def __init__(self,putc,vscroll,cols=80,rows=24,fill_rect=None,dcs=nop,sos=nop,osc=nop,pm=nop,apc=nop):
        self.row = 0
        self.col = 0
        self.cols = cols
        self.rows = rows
        self.line_starts = 0
        self.readinto_cb = lambda b:None
        self.utf8 = utf8_to_codepoints()
        self.utf8.send(None)
        self.csi = csi_curry(self)
        self.amux = ansi_mux(self.normal_char,self.control_char,self.csi,dcs,sos,osc,pm,apc)
        self.amux.send(None)
        self.style = set()
        self.font = 10
        self.fg_color_default = self.fg_color = 15
        self.bg_color_default = self.bg_color = 0
        self.putc = putc
        self.vscroll = vscroll
        if fill_rect is None:
            def fill_rect(char,rowl,coll,rowh,colh,putc=putc):
                for r in range(rowl,rowh):
                    for c in range(coll,colh):
                        putc(char,r,c)
        self.fill_rect = fill_rect
    def readinto(self,b):
        return self.readinto_cb(b)
    def write(self,b):
        if hasattr(self,"beforewrite"): self.beforewrite(self)        
        for c in b:
            self.writebyte(c)
        if hasattr(self,"afterwrite"): self.afterwrite(self)            
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
        if col < 0 and row == 0:
            self.col += col
            while self.col < 0 and self.row >= 0 and (self.line_starts>>self.row)&1==0:
                self.col += self.cols
                self.row -= 1
        else:
            self.move_cursor_to(row+self.row,col+self.col)
    def move_cursor_wrap(self,cols=0):
        d,self.col = divmod(self.col+cols,self.cols)
        d += self.row
        self.move_cursor_to(d)
        if d != self.row:
            if d > self.row: self.line_starts>>=d-self.row
            else:
                self.line_starts<<=self.row-d
                self.line_starts&=(1<<self.rows)-1
            self.vscroll(d-self.row)
    def normal_char(self,c):
        self.putc(c,self.row,self.col,self.style)
        self.move_cursor_wrap(1)
    def control_char(self,c):
        if c == 7:
            if hasattr(self,"bell"): self.bell(self)
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
            while e < self.rows and not (self.line_starts>>e)&1:
                e += 1
            if mode == 0 and e > self.row+1: self.fill_rect(32,self.row+1,0,e,self.cols)
        if mode == 1 or mode == 2:
            s = self.row
            while s >= 0 and not (self.line_starts>>s)&1:
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

#e.g. term = TermCursor(lambda c,x,y,term=None:type6x8_2b(chr(c),20+y*6,20+x*8),lambda l: (t.fb.scroll(0,-8*l),t.fb.rect(0,20+8*(25-l),300,300,77,1)),30,25)
#def show_starts(intens=100):
#    t.fb.rect(18,20,2,8*25,77)
#    for i in range(term.rows):
#        if (term.line_starts>>i)&1:
#            t.fb.rect(18,20+i*8,2,7,intens)
#            t.fb.rect(19,21+i*8,1,5,77)
    
