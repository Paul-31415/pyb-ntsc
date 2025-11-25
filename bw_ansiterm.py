



class cursor:
    def __init__(self,putc,scroll,cols=80,rows=24):
        self.putc = putc
        self.scroll = scroll
        self.cols = cols
        self.rows = rows
        self.x = 0
        self.y = 0
        #self.utf8 = 0
        #self.codepoint = 0
        self.esc = False
    def inc_col(self,by=1):
        self.x += by
        by = self.x // self.cols
        if by != 0:
            self.x %= self.cols
            self.inc_row(by)
    def inc_row(self,by=1):
        self.y += by
        if self.y >= self.rows:
            self.scroll(1+self.y-self.rows)
            self.y = self.rows-1
    def writebyte(self,b):
        if self.esc:
            self.esc.append(b)
            if 0x40 <= b <= 0x7e:
                self.escape(self.esc)
                self.esc = False
        elif b < 0x32:
            if b == 10:
                self.inc_row()
            elif b == 13:
                self.x = 0
            elif b == 27:
                self.esc = [b]
        else:
            self.putc(b,self.x,self.y)
            self.inc_col()
    def write(self,data):
        for b in data:
            self.writebyte(b)
    def readinto(self,*a):
        return None
