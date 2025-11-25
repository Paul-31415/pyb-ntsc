from pyb import Pin, Timer, DAC
import framebuf
import micropython
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

class tv240p:
    def __init__(self,buf,hres=64,total_lines=262,sync_level=30,porch_level=70,black_level=77):
        self.buf = buf
        self.mv = memoryview(buf)
        self.sync_level = sync_level
        self.porch_level = porch_level
        self.black_level = black_level
        self.hsync_syncpulse_µs = 4.7
        self.hsync_backporch_µs = 4.7
        self.hsync_video_µs = 52.6
        self.hsync_frontporch_µs = 1.5
        self.vsync_frontporch_lines = 3
        self.vsync_syncpulse_lines = 3
        self.vsync_backporch_lines = 3
        self.vsync_hporch_µs = 4.7
        self.vsync_blank_lines = 11
        self.vsync_video_lines = total_lines-20
        self.line_length = hres
    def init(self):
        h = self.line_length
        b = self.mv
        #vertical syncpulse
        horiz = [self.hsync_syncpulse_µs,self.hsync_backporch_µs,self.hsync_video_µs,self.hsync_frontporch_µs]
        for i in range(3):
            horiz[i+1] += horiz[i]
        vh = int((horiz[-1]-self.vsync_hporch_µs)/horiz[-1] * h)
        horiz = tuple(int(v/horiz[-1] * h) for v in horiz)
        vert = [self.vsync_syncpulse_lines,self.vsync_backporch_lines,self.vsync_blank_lines,self.vsync_video_lines,self.vsync_frontporch_lines]
        for i in range(4):
            vert[i+1] += vert[i]
        self.fullfb = f = framebuf.FrameBuffer(b,h,vert[-1],framebuf.GS8)
        #horizontal sync
        f.rect(0,0,horiz[0],vert[-1],self.sync_level,True)
        f.rect(horiz[0],0,horiz[1]-horiz[0],vert[-1],self.porch_level,True)
        f.rect(horiz[2],0,h-horiz[2],vert[-1],self.porch_level,True)
        #vertical sync
        f.rect(0,0,vh,vert[0],self.sync_level,True)
        f.rect(vh,0,h-vh,vert[0],self.porch_level,True)
        f.rect(horiz[0],vert[0],h-horiz[0],vert[1]-vert[0],self.porch_level,True)
        f.rect(horiz[1],vert[1],horiz[2]-horiz[1],vert[2]-vert[1],self.black_level,True)
        f.rect(horiz[0],vert[3],h-horiz[0],vert[4]-vert[3],self.porch_level,True)
        #screen dimensions
        self.w = horiz[2]-horiz[1]
        self.h = vert[3]-vert[2]
        self.smv = b[vert[2]*h+horiz[1]:]
        self.fb = framebuf.FrameBuffer(self.smv,self.w,self.h,framebuf.GS8,h)
        self.total_length = h*vert[4]
    def pinit(self,ctim=9,cch=2,cpin="X4",dacpin='X5',dacbuf=True,ftim=2):
        self.carrier = Timer(ctim, prescaler=1,period=2)
        self.ch = self.carrier.channel(cch,Timer.PWM,pin=Pin(cpin),pulse_width=1)
        self.dac = DAC(Pin(dacpin),buffering=dacbuf)
        line_time = self.hsync_syncpulse_µs+self.hsync_backporch_µs+self.hsync_video_µs+self.hsync_frontporch_µs
        self.dac_tim = Timer(6, freq=int(self.line_length/line_time*1e6))
        ps = self.dac_tim.prescaler()
        pe = self.dac_tim.period()
        fpe = (pe+1)*self.total_length - 1
        self.frametim = Timer(ftim,prescaler=ps,period=fpe)
        self.dac_tim.prescaler(0xffff)
        self.frametim.prescaler(0xffff)
        self.dac_tim.counter(0)
        self.dac.write_timed(self.mv[:self.total_length],self.dac_tim,mode=DAC.CIRCULAR)
        self.frametim.counter(0)
        self.dac_tim.prescaler(ps)
        self.frametim.prescaler(ps)
        #frametim should fire approx at the start of vertical sync
    def onframe(self,callback,scheduled=True):
        if callback is None or not scheduled:
            self.frametim.callback(callback)
            return
        def do(s):
            s[3](self)
            s[0] = 1
        self.cbargs = [1,0,do,callback]
        def cb(tim,s = self.cbargs):
            if s[0]:
                s[0] = 0
                micropython.schedule(s[2],s)
            else:
                s[1]+=1
        self.frcb = cb
        self.frametim.callback(cb)
    def ainit(self,apin="Y3",atim=10,ach=1):
        self.atim = Timer(atim,freq=4500000)
        self.ach=self.atim.channel(ach,Timer.PWM,pin=Pin(apin),pulse_width=18)
        #modulation is done via parasitic loading
        #do a dma transfer to atim's period to play audio
        #nominal center period is 37+1/3, deviation is 25kHz, is from 37.127 to 37.542
        #ugh, that means it's all in dither unless we use an undertone
        #or we take 512 bytes = bytes([38-1]*256+[37-1]*256) and set up a looping dma transfer 256 bytes wide (timer source is atim)
        # and dma to that dma's start address
