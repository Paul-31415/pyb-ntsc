def mand(t,x0=0,y0=0,w=211,h=237,z0=0,zoom=10,iters=64):
    for x in range(x0,x0+w):
        for y in range(y0,y0+h):
            t.fb.pixel(x,y,77+int(93*(a_mandelbrot(0j,(3*((x-x0)/w-.5)+2j*((y-y0)/w-.5))*zoom+z0,iters)+1)/iters))







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
                    

