from NTSC import tv
#t = tv() #should work
t = tv(250,True) #high res progressive scan, might work
t.set_carrier(0,2,1) #~ VHF low channel 2
t.demo()
