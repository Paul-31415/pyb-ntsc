#various viper and assembly routines for quick graphical operations
# and correct implementations in python
# for the graphical ops, coordinates are complex numbers since float is accepted anyways
# for the framebuffer, it's (int, int) because that's not the place for interpolation
import framebuf
class fbuf:
    def __init__(self,buf,w,h,stride=None,start=0):
        self.b = memoryview(buf)[start:]
        self.w = w
        self.h = h
        self.s = w if stride is None else stride
    @property
    def f(self):
        return framebuf.FrameBuffer(self.b,self.w,self.h,framebuf.GS8,self.s)
    def inbounds(self,x,y):
        return 0 <= x < self.w and 0 <= y < self.h
    def ind(self,x,y):
        return x+y*self.s
    def getpx(self,x,y,default=None):
        return self[x,y] if self.inbounds(x,y) else default
    def setpx(self,x,y,v,default=None):
        if self.inbounds(x,y):
            i = self.ind(x,y)
            r = self.b[i]
            self.b[i] = v
            return r
        return default
    def __getitem__(self,k):
        if isinstance(k,tuple):
            x,y = k
            if isinstance(x,slice) or isinstance(y,slice):
                if isinstance(x,slice):
                    assert x.step is None or x.step == 1, "only stepsize 1 supported for x axis"
                    a = 0 if x.start is None else x.start
                    b = self.w if x.stop is None else x.stop
                else:
                    a = x
                    b = x+1
                if isinstance(y,slice):
                    assert y.step is None or y.step > 0
                    c = 0 if y.start is None else y.start
                    d = self.h if y.stop is None else y.stop
                    e = 1 if y.step is None else y.step
                else:
                    c = y
                    d = y+1
                    e = 1
                return fbuf(self.b,b-a,(d-c)//e,self.s*e,self.ind(a,c))
            else:
                return self.b[x+y*self.s]
    def __setitem__(self,k,v):
        self.b[k[0]+k[1]*self.s] = v


def trace(p,fn,lvl=None,d=1j,epsilon=.1):
    #trace a level set
    if lvl is None: lvl = fn(p)
    triangle = (1+0j,-.5+.8660254038j,-.5-.8660254038j)
    while True:
        samps = tuple(fn(p+v*epsilon) for v in triangle)
        val = sum(samps)/3
        grad = sum(triangle[i]*(samps[i]-val) for i in range(3))/epsilon
        ungrad = 1/(grad.real-1j*grad.imag)
        p -= (val-lvl)*ungrad
        yield p
        p += d*grad/(abs(grad)+1e-30)
    
def stroke(fb,p,fn,length,c,offset=0,scale=1,lvl=None,d=1j,epsilon=.1,):
    for v in trace(p,fn,lvl,d,epsilon):
        v = v*scale+offset
        x = int(v.real)
        y = int(v.imag)
        a = v.real-x
        b = v.imag-y
        fb.setpx(x,y,round(fb.getpx(x,y,0)+c*(1-a)*(1-b)))
        fb.setpx(x+1,y,round(fb.getpx(x+1,y,0)+c*a*(1-b)))
        fb.setpx(x,y+1,round(fb.getpx(x,y+1,0)+c*(1-a)*b))
        fb.setpx(x+1,y+1,round(fb.getpx(x+1,y+1,0)+c*a*b))
        length -= 1
        if length < 0: return


#sphere with simple lighting
for ix in range(100):
    x = (ix-50)/50
    for iy in range(133):
        y = (iy-66)/66
        z = 1 - x**2 - y**2
        if z >= 0:
            z **= .5
            light = (max(0,(x*1+y*2+z*3)/3.7416573868)+max(0,(x*1+y*-2+z*-3)/3.7416573868))/2
            t.fb.pixel(ix+50,iy+50,77+round(64*light))


def movwt(Rd,imm32):
    #movw encoding t3: 1111 0i10 0100 imm4  0im3 dddd [ imm8  ]
    #     Rd = signed(imm4:i:im3:imm8)
    yield 0xf240|((imm32>>12)&15)|(((imm32>>11)&1)<<10)
    yield (imm32&255)|((Rd&15)<<8)|(((imm32>>8)&7)<<12)
    #movt encoding t1: 1111 0i10 1100 imm4  0im3 dddd [ imm8  ]
    imm32>>=16
    yield 0xf2c0|((imm32>>12)&15)|(((imm32>>11)&1)<<10)
    yield (imm32&255)|((Rd&15)<<8)|(((imm32>>8)&7)<<12)

    
import stm
def shade_rect(buf,x0,y0,width,height,shader,ystride=255,xstride=1,dim=77,bright=190,u0=0,v0=0,u1=1,v1=1):
    #todo: bounds checking
    if isinstance(shader,type(a_shade_rect)):
        #i.e. if asm function
        shader = stm.mem32[id(a_shade_rect)+8] #grab pointer to code
    elif isinstance(shader,float) or isinstance(shader,int):
        shader = float(shader)
        #movwt(r7,shader)
        #vmov(s0,r7)     "vmovr": (("1110 1110 000O nnnn, tttt 1010 N001 0000","tttt","nnnnN","O"),"[Sn=Rt,Rt=Sn][O]"),
        #bx(lr)
        shader = array("H",tuple(movwt(7,stm.mem32[id(shader)+4]))+(0xee00,0x7a10,0x4770))
    else:
        assert isinstance(shader,array) or isinstance(shader,bytes) or isinstance(shader,bytearray) or isinstance(shader,memoryview), "unknown shader type"
    bufinfo = array("i",[width,height,xstride,ystride,dim,bright])
    uvinfo = array("f",[u0,v0,u1,v1])
    a_shade_rect(memoryview(buf)[x0*xstride+y0*ystride:],bufinfo,uvinfo,shader)
        


            
            
@micropython.asm_thumb
def a_shade_rect(r0,r1,r2,r3):
    #r0 - buffer bytearray/memoryview
    #r1 - buffer info array("i",[width,height,stride_x,stride_y,min_brightness,max_brightness])
    #r2 - rectangle array("f",[u0,v0,u1,v1])
    #r3 - shader function: s0=pixel val,s1=u,s2=v -> return s0=new pixel val (return with 70 47 : bx(lr)  # (0x4770 in array))
    mov(r4,1)    #make sure bit 0 of shader address is set so jump is to thumb format
    orr(r3,r4)
    
    ldr(r5,[r1,4])
    label(heightloop)
    
    mov(r6,r0)
    ldr(r4,[r1,0])
    label(widthloop)
    ldrb(r7,[r0,0])
    vmov(s0,r7)
    vcvt_f32_s32(s0,s0)
    vldr(s1,[r1,16])
    vcvt_f32_s32(s1,s1)
    vldr(s2,[r1,20])
    vcvt_f32_s32(s2,s2)
    vsub(s0,s0,s1)
    vsub(s2,s2,s1)
    vdiv(s0,s0,s2) #normalize pixel brightness value
    #calc u,v
    vmov(s1,r4) # width-x
    vcvt_f32_s32(s1,s1)
    vldr(s2,[r1,0]) # width
    vcvt_f32_s32(s2,s2)
    vsub(s1,s1,s2) # x
    vdiv(s1,s1,s2) # u in [0,1)
    vldr(s2,[r2,0]) # u0
    vldr(s3,[r2,8]) # u1
    vsub(s3,s3,s2) #u1-u0
    vmul(s3,s3,s1)
    vadd(s1,s3,s2) #s1 = ((width-(width-x))/width)*(u1-u0)+u0 = u in [u0,u1)
    
    vmov(s2,r5) # height-y
    vcvt_f32_s32(s2,s2)
    vldr(s3,[r1,4]) # height
    vcvt_f32_s32(s3,s3)
    vsub(s2,s2,s3) # y
    vdiv(s2,s2,s3) # v in [0,1)
    vldr(s3,[r2,4]) # v0
    vldr(s4,[r2,12]) # v1
    vsub(s4,s4,s3) #v1-v0
    vmul(s4,s4,s2)
    vadd(s2,s4,s3)
    #call shader at r3
    data(2,0x4798) #blx(r3) : 0100 0111 1rrr r000
    #unnormalize brightness value
    vldr(s1,[r1,16])
    vcvt_f32_s32(s1,s1)
    vldr(s2,[r1,20])
    vcvt_f32_s32(s2,s2)
    vsub(s2,s2,s1)
    vmul(s0,s0,s2)
    vadd(s0,s0,s1)
    vcvt_s32_f32(s0,s0)
    vmov(r7,s0)
    
    strb(r7,[r0,0])#write pixel
    
    
    ldr(r7,[r1,8])
    add(r0,r0,r7)
    sub(r4,1)
    bne(widthloop)
    ldr(r7,[r1,12])
    add(r0,r6,r7)
    sub(r5,1)
    bne(heightloop)








    
    
@micropython.asm_thumb
def a_raster_triangle(r0,r1,r2,r3):
    #r0 - buffer bytearray/memoryview
    #r1 - buffer info array("i",[width,height,stride_x,stride_y,min_brightness,max_brightness])
    #r2 - triangle array("f",[x0,y0,z0,x1,y1,z1,x2,y2,z2]) in screenspace, z is used to calculate perspective correct uv coordinates
    #r3 - shader function: s0=u,s1=v,s2=x,s3=y,s4=z -> return s0=brightness
