import gc
from pyb import Pin, Timer, DAC
gc.collect()
import framebuf
gc.collect()
#big bulky video buffer (8 bits deep)
#fps = 30/1.001
#33367 bytes needed for buffer at 1MHz
#525 scan lines (interlaced) 486 on screen

#-40, +100
#-40 = sync
#0 = porch
#7.5 = black
#100 = white

#http://www.sxlist.com/techref/io/video/ntsc.htm

# vsync: 3 lines porch, 3 lines sync, 3 lines porch, 11 lines black, 242.5 lines video
# hsync: 1.5µs porch, 4.7µs sync, 4.7µs porch (colorburst 40 IRE ptp ≥ 2.5µs), 52.6µs video
# dma is good to about period 9 or so = 8.4MHz, but memory is insufficient
# diode modulator is inverted and linear on about 70% of the domain (from approx 26 to 205, 179ish codepoints)
# progressive scan 262 lines memory cost: 16637 bytes/MHz
#                                         6MHz uses 99822 bytes
# 3:4 aspect ratio




class tv:
    def __init__(self,hres=64,progressive=False,lines=None,linetime=64,buf=None,audio_subcarrier=True,broadcast=True):
        if lines is None:
            lines = 262 if progressive else 525
        self.lines = lines
        if buf is None:
            self.buf = bytearray(lines*hres)
        else:
            self.buf = buf
        self.hres = hres
        self.line_time = linetime
        self.progressive = progressive
        
        self.sync_level = 0
        self.blanking_level = 56 if broadcast else 22
        self.black_level = 58 if broadcast else 26
        self.white_level = 73 if broadcast else 78
        
        self.audio_sc = audio_subcarrier
        
        self.phase = 0
        self.buffer_dac = True
        self.reinit()
    def redac(self):
        self.dac = DAC(Pin('X5'),buffering=self.buffer_dac)
        self.dac = DAC(Pin('X6'),buffering=self.buffer_dac)
        self.bmv = memoryview(self.buf)[:len(self)]
        self.dac_tim = Timer(6, freq=int(self.hres*1000000/self.line_time))
        self.dac.write_timed(self.bmv,self.dac_tim,mode=DAC.CIRCULAR)
        self.frame_tim = Timer(5, prescaler=self.dac_tim.prescaler(),period=self.dac_tim.period()*len(self))
        self.frame_tim.counter(self.phase)
    def reinit(self):
        self.calc_porch_magic_numbers()
        self.init()
    def set_progressive(self,prog=True):
        self.progressive = prog
        self.calc_porch_magic_numbers()
        self.init()
    
    def __len__(self):
        return self.hres*self.lines
    def calc_porch_magic_numbers(self):
        br = self.hres/self.line_time

        w = round(4.7*br)
        t = int(10.9*br+0.9)#round mostly up
        s = round(1.5*br)
        self.h_blank = [s,s+w,t]
        self.v_blank_e = [6,12,18]
        self.v_blank_o = [6,12,19]

        hsl = round(18*br)
        hsh = round(58*br)
        
        self.h_safe = [hsl-t,hsh-t]
        self.v_safe = [32*(2-self.progressive),208*(2-self.progressive)]
        
    def init(self):
        self.carrier = Pin('X1') 
        self.tim = Timer(2, prescaler=1,period=1)
        self.ch = self.tim.channel(1, Timer.PWM, pin=self.carrier)
        self.ch.pulse_width(1)
        if self.audio_sc:
            self.a_carrier = Pin('X2') 
            self.a_tim = Timer(4, freq=4500000)
            self.a_ch = self.a_tim.channel(1, Timer.PWM, pin=self.a_carrier)
            self.a_ch.pulse_width_percent(50)

        self.redac()
        
        self.be = self.bmv
        if not self.progressive:
            self.bo = self.be[len(self)//2:]
        self.fb = framebuf.FrameBuffer(self.buf,self.hres,self.lines,framebuf.GS8)
        self.fbe_mv = self.be[self.hres*21+self.h_blank[2]:]
        if not self.progressive:
            self.fbo_mv = self.bo[self.hres*43//2+self.h_blank[2]:]
        h = self.y_dim()//(2-self.progressive)
        self.fbe = framebuf.FrameBuffer(self.fbe_mv,self.hres-self.h_blank[2],h,framebuf.GS8,self.hres)
        if not self.progressive:
            self.fbo = framebuf.FrameBuffer(self.fbo_mv,self.hres-self.h_blank[2],h,framebuf.GS8,self.hres)
        self.clear()

    def set_pixel(self,x,y,v):
        if self.progressive:
            self.fbe.pixel(x,y,int(v*(self.white_level-self.black_level)+self.black_level))
        else:
            [self.fbe,self.fbo][y&1].pixel(x,y//2,int(v*(self.white_level-self.black_level)+self.black_level))
    def get_pixel(self,x,y):
        if self.progressive:
            return (self.fbe_mv[x+y*self.hres]-self.black_level)/(self.white_level-self.black_level)
        else:
            return ([self.fbe_mv,self.fbo_mv][y&1][x+(y//2)*self.hres]-self.black_level)/(self.white_level-self.black_level)

    def set_carrier(self,pre=1,per=1,w=1):
        self.tim.init(prescaler=pre,period=per)
        self.ch.pulse_width(w)
    def clear(self):
        self.fb.fill(self.black_level)
        self.syncs()
    def syncs(self):
        self.fb.fill_rect(0,0,self.h_blank[2],self.lines,self.blanking_level)
        self.fb.fill_rect(self.h_blank[0],0,self.h_blank[1]-self.h_blank[0],self.lines,self.sync_level)
        for y in range(self.v_blank_e[2]):
            inv = self.v_blank_e[0] <= y < self.v_blank_e[1]
            for x in range(self.hres//2):
                val = self.blanking_level
                if (self.h_blank[0] <= x < self.h_blank[1]) ^ inv:
                    val = self.sync_level
                self.buf[y*self.hres//2+x] = val
        if not self.progressive:
            for y in range(self.v_blank_o[2]):
                inv = self.v_blank_o[0] <= y < self.v_blank_o[1]
                for x in range(self.hres//2):
                    val = self.blanking_level
                    if (self.h_blank[0] <= x < self.h_blank[1]) ^ inv:
                        val = self.sync_level
                    self.bo[y*self.hres//2+x] = val
    def lines_iter(self):
        for y in range(self.v_blank_e[2],self.lines-21):
            yield self.fbe_mv[y*self.hres:(y+1)*self.hres-self.h_blank[2]]
            if not self.progressive:
                yield self.fbo_mv[y*self.hres:(y+1)*self.hres-self.h_blank[2]]
                       
    def x_dim(self):
        return self.hres-self.h_blank[2]
    def y_dim(self):
        return self.lines-(21 if self.progressive else 43)
    
    def mandelbrot(self,imax=8,p=0,s=2,julia=False,il=0,x0=None,y0=None,x1=None,y1=None,asm=True,julia_seed=0):
        
        x0 = self.h_safe[0] if x0 == None else x0
        x1 = self.h_safe[1] if x1 == None else x1
        y0 = self.v_safe[0] if y0 == None else y0
        y1 = self.v_safe[1] if y1 == None else y1
        
        for x in range(x0,x1):
            for y in range(y0,y1):
                c = (((x-x0)/(x1-x0-1)-.5)*2 + ((y-y0)/(y1-y0-1)-.5)*2j)*s+p
                z = c
                if julia:
                    c = julia_seed
                if asm:
                    i = a_mandelbrot(z,c,imax)
                else:
                    for i in range(imax):
                        if z.real*z.real+z.imag*z.imag > 4:
                            break
                        z = z*z+c
                    else:
                        self.set_pixel(x,y,il)
                        continue
                if i == -1:
                    self.set_pixel(x,y,il)
                else:
                    self.set_pixel(x,y,i/imax)
    def demo(self,x0=None,y0=None,x1=None,y1=None):

        x0 = self.h_safe[0] if x0 == None else x0
        x1 = self.h_safe[1] if x1 == None else x1
        w = x1-x0
        y0 = self.v_safe[0] if y0 == None else y0
        y1 = self.v_safe[1] if y1 == None else y1
        h = y1-y0
        
        mx = x0
        my = y0
        import pyb
        import time
        acc = pyb.Accel()
        btn = pyb.Switch()
        p = self.get_pixel(int(mx),int(my))
        pos = 0
        zoom = 2
        it = 16
        julia = False
        jp = 0
        self.mandelbrot(it,pos,zoom,julia,0,x0,y0,x1,y1,julia_seed=jp)

        def paddles(c):
            x = int(mx-.125*w)
            xw = w//4
            y = int(my-.125*h)
            yw = h//4
            y_0 = y0
            y_1 = y1
            if not self.progressive:
                y //= 2
                yw //= 2
                y_0 //= 2
                y_1 //= 2
            self.fbe.hline(x,y_0,xw,c)
            self.fbe.vline(x0,y,yw,c)
            self.fbe.hline(x,y_1,xw,c)
            self.fbe.vline(x1,y,yw,c)
            if not self.progressive:
                self.fbo.hline(x,y_0,xw,c)
                self.fbo.vline(x0,y,yw,c)
                self.fbo.hline(x,y_1,xw,c)
                self.fbo.vline(x1,y,yw,c)
        
        while 1:
            paddles(self.black_level)
            mx = min(x1-2,max(x0,mx*.98+(-acc.x()/24+.5)*w*.02))
            my = min(y1-2,max(y0,my*.98+(acc.y()/24+.5)*h*.02))
            paddles(self.white_level)
            p = self.get_pixel(int(mx),int(my))
            self.set_pixel(int(mx),int(my),(p+.5)%1)
            pyb.delay(10)
            self.set_pixel(int(mx),int(my),p)
            if btn():
                st = time.ticks_ms()
                nit = it*2
                while btn():
                    if time.ticks_diff(time.ticks_ms(),st) > 1000:
                        if acc.z()>0:
                            nit = it*2
                        else:
                            nit = "Julia"
                        self.fbe.fill_rect(x0,y0,w,10,self.black_level)
                        if not self.progressive:
                            self.fbo.fill_rect(x0,y0,w,10,self.black_level)
                        self.fbe.text(str(nit),x0+1,y0+1,self.white_level)
                        if not self.progressive:
                            self.fbo.text(str(nit),x0+1,y0+1,self.white_level)
                cp = (((mx-x0)/w-.5)*2+2j*((my-y0)/h-.5))*zoom
                if time.ticks_diff(time.ticks_ms(),st) > 1000:
                    if nit == "Julia":
                        julia ^= 1
                        jp = pos + cp
                        pos = 0
                        zoom = 2
                        it = 16
                    else:
                        it = nit
                else:
                    pos += cp
                    zoom *= .25
                self.mandelbrot(it,pos,zoom,julia,0,x0,y0,x1,y1,julia_seed=jp)

    
                
                
@micropython.asm_thumb
def a_mandelbrot(r0,r1,r2):
    vldr(s0,[r0,4])#z.real
    vldr(s1,[r0,8])#z.iamg

    vldr(s2,[r1,4])
    vldr(s3,[r1,8])

    movwt(r1,0x40800000)#float 4
    vmov(s7,r1)
    
    mov(r0,0)
    label(Loop)
    #check abs
    vmul(s4,s0,s0)
    vmul(s5,s1,s1)
    vadd(s6,s4,s5)
    vcmp(s6,s7)
    vmrs(APSR_nzcv, FPSCR)
    bgt(out)
    #z = z^2+c
    vmul(s6,s1,s0)
    vsub(s0,s4,s5)
    vadd(s1,s6,s6)
    vadd(s0,s0,s2)
    vadd(s1,s1,s3)
    #loop
    add(r0,1)
    cmp(r0,r2)
    bls(Loop)
    movwt(r0,-1)
    label(out)
                    
                
        

