from array import array


class fframebuffer:
    def __init__(self,buf,width,height,stride=None,filt=None):
        self.buf = buf
        self.stride = width if stride is None else stride
        self.width = width
        self.height = height

        #need an invertable filtering scheme that
        # captures dc and nonlinearities
        #how about 3x3 matrix, 1 dim is time, the other is order (1,2,3)
        # with a 0th term which is dc offset
        # (inverse requires unambiguous roots of cubics...)
        #perhaps instead just dc, 3 terms of fir, and gamma?
        #
        self.filter = array('f',[0,0,1,0,0]) if filt is None else filt
    
        
