
from array import array

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
def shade_rect(buf,x0,y0,width,height,shader,ystride=255,xstride=1,dim=77,bright=190,u0=0,v0=0,u1=1,v1=1,shader_args=()):
    #todo: bounds checking
    if isinstance(shader,type(a_shade_rect)):
        #i.e. if asm function
        shader = stm.mem32[id(shader)+8] #grab pointer to code
    elif isinstance(shader,float) or isinstance(shader,int):
        shader = float(shader)
        #movwt(r7,shader)
        #vmov(s0,r7)     "vmovr": (("1110 1110 000O nnnn, tttt 1010 N001 0000","tttt","nnnnN","O"),"[Sn=Rt,Rt=Sn][O]"),
        #bx(lr)
        shader = array("H",tuple(movwt(7,stm.mem32[id(shader)+4]))+(0xee00,0x7a10,0x4770))
    else:
        assert isinstance(shader,array) or isinstance(shader,bytes) or isinstance(shader,bytearray) or isinstance(shader,memoryview), "unknown shader type"
    bufinfo = array("i",(width,height,xstride,ystride,dim,bright))
    uvinfo = array("f",(u0,v0,u1,v1)+tuple(shader_args))
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
    vsub(s1,s2,s1) # x
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
    vsub(s2,s3,s2) # y
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




#fast pow2 and log2:
@micropython.asm_thumb
def vpow2_approx7(r0,r1):
    mov(r2,r0)
    vldr(s0,[r1,4])
    
    #uses r0,s0,s1,s2
    # 2**x ~= (2+(x+1)**2)/3 between 1 and 2
    # good to almost 8 bits
    # (can think of it as the integral of the linear approximated exponential)
    #  (can integrate furter to get a cubic fit, or can filter with a fir filter to get a twice as frequent fit)
    #  (both suck, only giving a few more bits)
    #  (cubic from firsts: x^3 -> 3x^2 want two points where d2 = 2*d1, 1 and root 2,
    #    then want to scale such that p2-p1 = 1, divide by 2√2-1, then shift
    #   overall, y = ((x*(√2-1)+1)^3-1)/(2√2-1) + 1
    #     meh, minor improvement (1 bit), underconstrained, need to get the x^2 term
    #     get by y * 2 - (2+(x+1)**2)/3 ?
    #     almost, not alligned in the middle though...)
    #
    #2**s0
    #nan and -inf check
    vmov(r0,s0)
    data(2,0xea5f,0b0_101_0000_11_11_0000)#ror(r0,r0,23)
    mvn(r0,r0)
    data(2,0xf010,0x0fff) #tst(r0,0xff)
    bne(ok)
    #s0 is +-inf or nan
    #return s0 unchanged if +inf or nan
    #return 0 if -inf
    #-inf would look like 0xfffffe00 in r0
    data(2,0xf200,0x10ff)#add(r0,r0,0x1ff)
    add(r0,1)
    it(eq)
    vmov(s0,r0)
    
    b(cont)#bx(lr)

    label(ok)
    #domain reduce
    vcvt_s32_f32(s1,s0) #saturates btw
    vmov(r0,s1)#int part
    vmov(r1,s0)#convert round towards 0 to round towards -inf
    cmp(r1,0)
    itt(mi)#minus
    sub(r0,1)
    vmov(s1,r0)
    #parabola
    vcvt_f32_s32(s1,s1)
    vsub(s0,s0,s1)#frac part
    data(2,0xeef7,0x0a00)#vmov_imm(s1,1.0)
    vadd(s0,s0,s1)
    vadd(s2,s1,s1)
    vmul(s0,s0,s0)
    vadd(s0,s0,s2)
    vadd(s1,s1,s2)
    vdiv(s0,s0,s1)

    #create exponent from int part
    cmp(r0,127)
    it(gt)#overflow, load something that'll become +inf
    mov(r0,128)
    add(r0,127)#exp bias
    itte(le)#underflow
    add(r0,64)#do it as two mults
    data(2,0b00000_10111_000_000)#lsl(r0,23) shift up to exp field location
    data(2,0b00000_10111_000_000)#lsl(r0,23) on both branches, don't affect flags
    
    vmov(s1,r0)
    vmul(s0,s0,s1)
    itttt(le)
    mov(r0,0x3f)#2^-64
    data(2,0b00000_10111_000_000)#lsl(r0,23)
    vmov(s1,r0)
    vmul(s0,s0,s1)
    #bx(lr)
    label(cont)
    vstr(s0,[r2,4])

def exp2_approx(a):
    r = 0.
    vpow2_approx7(id(r),id(float(a)))
    return r
@micropython.asm_thumb
def vlog2_approx7(r0,r1):
    mov(r2,r0)
    vldr(s0,[r1,4])
    #sqrt(3x-2)-1
    #logarithm
    #domain reduce
    vmov(r0,s0)
    #movwt(r1,0xff800000)
    #and_(r0,r1) #exp and sign in r0
    data(2,0b00001_10111_000_000)#lsr(r0,r0,23)
    vmov(s1,r0) #exp into s1
    bne(normal)#subnormal or zero
    #multiply by 2^64 and retry
    mov(r0,0xbf)
    data(2,0b00000_10111_000_000)#lsl(r0,r0,23)
    vmov(s2,r0)
    vmul(s0,s0,s2)
    vmov(r0,s0)
    data(2,0b00001_10111_000_000)#lsr(r0,r0,23)
    
    itt(eq)#ittt(eq)#was 0
    movt(r0,0xff80)#-inf
    vmov(s0,r0)
    beq(cont)#bx(lr)

    sub(r0,64)
    vmov(s1,r0) #exp into s1
    add(r0,64)
    
    label(normal)
    cmp(r0,255) #inf/nan check
    #it(eq)
    beq(cont)#bx(lr)

    data(2,0b00000_10111_000_000)#lsl(r0,r0,23)
    itt(mi)#ittt(mi)#ret nan
    movt(r0,0x7fff)#nan
    vmov(s0,r0)
    bmi(cont)#bx(lr)
    
    vmov(r1,s0)
    eor(r1,r0) #mantissa in r1

    #prep exponent of mantissa
    mov(r0,0x7f)
    data(2,0b00000_10111_000_000)#lsl(r0,r0,23)
    orr(r1,r0)
    vmov(s0,r1) #mant into s0

    #parabola
    data(2,0xeeb0,0x1a08)#vmov_imm(s2,3.0)
    vmul(s0,s0,s2)
    data(2,0xeeb0,0x1a00)#vmov_imm(s2,2.0)
    vsub(s0,s0,s2)
    vsqrt(s0,s0)
    data(2,0xeeb7,0x1a00)#vmov_imm(s2,1.0)
    vsub(s0,s0,s2)
    vmov(r0,s1)
    sub(r0,127)
    vmov(s1,r0)
    vcvt_f32_s32(s1,s1)
    vadd(s0,s0,s1)

    label(cont)
    
    vstr(s0,[r2,4])
    
def log2_approx(a):
    r = 0.
    vlog2_approx7(id(r),id(float(a)))
    return r
def pow_approx(a,b):
    return exp2_approx(log2_approx(a)*b)


def log2_by_squaring(v,bits=24):
    m,e = math.frexp(v)
    e -= 1
    m *= 2
    for b in range(bits):
        e <<= 1
        m *= m
        if m >= 2:
            m /= 2
            e |= 1
    return e

def exp2_by_sqrting(e,bits=24):
    m = 1.
    for b in range(bits):
        if e&1:
           m *= 2.
        m = math.sqrt(m)
        e>>= 1
    return m * (2**e)


def p_shade_rect(buf,x0,y0,width,height,shader,ystride=255,xstride=1,dim=77,bright=190,u0=0,v0=0,u1=1,v1=1,shader_args=(),gamma=1):
    #todo: bounds checking
    if isinstance(shader,float) or isinstance(shader,int):
        #i.e. if asm function
        shader = lambda p,u,v,c=shader: c
    for iy in range(height):
        i = (iy+y0) * ystride + x0*xstride
        v = v0+(v1-v0)*(iy/height)
        for ix in range(width):
            px = ((buf[i]-dim)/(bright-dim))**gamma
            u = u0+(u1-u0)*(ix/width) 
            px = shader(px,u,v,*shader_args)**(1/gamma)
            buf[i] = round(dim+(bright-dim)*px)
            i += xstride


import math

def p_phong_sphere(pixel,x,y,light,material,powf=pow):
    z2 = 1-x*x-y*y
    if z2 < 0: return pixel
    z = math.sqrt(z2)
    ambient,diffuse,specular,alpha = material
    N = (x,y,z)
    V = (0,0,1)
    lm = math.sqrt(sum(l*l for l in light))
    L = tuple(l/lm for l in light)
    N_dot_L = x*L[0]+y*L[1]+z*L[2]
    R = tuple(2*N_dot_L*N[i]-L[i] for i in range(3))
    R_dot_V = R[0]*V[0]+R[1]*V[1]+R[2]*V[2]
    return min(1,max(0,ambient + diffuse*max(0,N_dot_L) + specular*(powf(max(0,R_dot_V),alpha))))




@assemble(afloat.arg(0),acomplex(afloat.arg(1),afloat.arg(2)),tuple(afloat.arg(3+i) for i in range(3)),tuple(afloat.arg(6+i) for i in range(4)),listing=1)
def phong_sphere(pixel,uv,light,material):
    ambient,diffuse,specular,alpha = material
    z2 = 1-uv.mag2()
    z = z2.sqrt()

    #todo: fix
    N = (x,y,z)
    V = (0,0,1)
    lm = math.sqrt(sum(l*l for l in light))
    L = tuple(l/lm for l in light)
    N_dot_L = x*L[0]+y*L[1]+z*L[2]
    R = tuple(2*N_dot_L*N[i]-L[i] for i in range(3))
    R_dot_V = R[0]*V[0]+R[1]*V[1]+R[2]*V[2]
    return min(1,max(0,ambient + diffuse*max(0,N_dot_L) + specular*(powf(max(0,R_dot_V),alpha))))
    

    return z2.choose(phong,pixel)
    
    
    
@micropython.asm_thumb
def a_horrible_pow(r0,r1,r2,r3):
    #[r0] = [r1] ** [r2]
    #via ((([r1] intminus [r3]) floattimes [r2]) intplus [r3]) as float
    ldr(r4,[r1,4])
    vldr(s1,[r2,4])
    ldr(r5,[r3,4])
    
    sub(r4,r4,r5)
    vmov(s0,r4)
    vcvt_f32_s32(s0,s0)
    vmul(s0,s0,s1)
    vcvt_s32_f32(s0,s0)
    vmov(r4,s0)
    add(r4,r4,r5)

    str(r4,[r0,4])

def horrible_pow(a,b,c=1.):
    a = float(a)
    b = float(b)
    c = float(c)
    r = 0.
    a_horrible_pow(id(r),id(a),id(b),id(c))
    return r

def px(x,y,c,a):
    if 0 <= x < 65536 and 0 <= y < 65536:
        p = t.fb.pixel(x,y)
        if p is not None: t.fb.pixel(x,y,round(p*(1-a)+c*a))

def pt(x,y,c):
    ix = int(x)
    iy = int(y)
    a = x-ix
    b = y-iy
    px(ix,iy,c,(1-a)*(1-b))
    px(ix+1,iy,c,(a)*(1-b))
    px(ix,iy+1,c,(1-a)*(b))
    px(ix+1,iy+1,c,(a)*(b))

def graph(fn,x0=0,xf=10,y0=0,yf=10,res=256,c=140,ix0=20,ixf=t.h-20,iy0=t.h-20,iyf=20):
    for i in range(res):
        nx = i/res
        x = x0+(xf-x0)*nx
        y = fn(x)
        ny = (y-y0)/(yf-y0)
        pt(ix0+(ixf-ix0)*i/res,iy0+(iyf-iy0)*ny,c)











