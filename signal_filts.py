@micropython.asm_thumb      
def a_biquads8(r0,r1,r2,r3): #dest/ src, len, args, dc
    #does 4 biquads on a bytearray in place
    data(2,0xec92,0x1a1c) #vldm(s2,r2,28)   
    label(loop)
    ldrb(r4,[r0,0])
    sub(r4,r4,r3)
    vmov(s1,r4)
    vcvt_f32_s32(s1,s1)
    #biquad 1: a = [s2,s3], b = [s4,s5,s6], state = [s7,s8]
    # input = s1, output = s0 
    vmul(s0,s1,s4) #out = inp*b0    
    vadd(s0,s0,s7) #out += state0   
    vmul(s7,s1,s5) #state0 = inp*b1  
    data(2,0xeee1,0x3a40) #vfms(s7,s0,s2) #state0 -= out*a1   
    vadd(s7,s7,s8) #state0 += state1  
    vmul(s8,s1,s6) #state1 = inp*b1  
    data(2,0xeea1,0x4ac0) #vfms(s8,s0,s3) #state1 -= out*a2   
    #end biquad^  
    #biquad 2: a = [s9,s10], b = [s11,s12,s13], state = [s14,s15]
    # input = s0, output = s1 
    vmul(s1,s0,s11) #out = inp*b0    
    vadd(s1,s1,s14) #out += state0   
    vmul(s14,s0,s12) #state0 = inp*b1  
    data(2,0xeea4,0x7ae0) #vfms(s14,s1,s9) #state0 -= out*a1   
    vadd(s14,s14,s15) #state0 += state1  
    vmul(s15,s0,s13) #state1 = inp*b1  
    data(2,0xeee5,0x7a60) #vfms(s15,s1,s10) #state1 -= out*a2   
    #end biquad^  
    #biquad 3: a = [s16,s17], b = [s18,s19,s20], state = [s21,s22]
    # input = s1, output = s0 
    vmul(s0,s1,s18) #out = inp*b0    
    vadd(s0,s0,s21) #out += state0   
    vmul(s21,s1,s19) #state0 = inp*b1  
    data(2,0xeee8,0xaa40) #vfms(s21,s0,s16) #state0 -= out*a1   
    vadd(s21,s21,s22) #state0 += state1  
    vmul(s22,s1,s20) #state1 = inp*b1  
    data(2,0xeea8,0xbac0) #vfms(s22,s0,s17) #state1 -= out*a2   
    #end biquad^  
    #biquad 4: a = [s23,s24], b = [s25,s26,s27], state = [s28,s29]
    # input = s0, output = s1 
    vmul(s1,s0,s25) #out = inp*b0    
    vadd(s1,s1,s28) #out += state0   
    vmul(s28,s0,s26) #state0 = inp*b1  
    data(2,0xeeab,0xeae0) #vfms(s28,s1,s23) #state0 -= out*a1   
    vadd(s28,s28,s29) #state0 += state1  
    vmul(s29,s0,s27) #state1 = inp*b1  
    data(2,0xeeec,0xea60) #vfms(s29,s1,s24) #state1 -= out*a2   
    #end biquad^    

    vcvt_s32_f32(s1,s1)
    vmov(r4,s1)
    add(r4,r4,r3)
    it(lt)
    mov(r4,0)
    cmp(r4,255)
    it(ge)
    mov(r4,255)
    strb(r4,[r0,0])
    
    add(r0,1)   
    sub(r1,1)   
    bgt(loop)   
    #write back 
    data(2,0xec82,0x1a1c) #vstm(s2,r2,28)  
