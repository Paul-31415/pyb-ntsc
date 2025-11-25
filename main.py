buf = bytearray(65535)
import gc
gc.collect();import micropython
micropython.alloc_emergency_exception_buf(256)
gc.collect();from small_ntsc import tv240p
gc.collect();import ansiterm
gc.collect();import simple_font
gc.collect();import framebuf
gc.collect();import uos
gc.collect();import keyboard_filter
gc.collect()
t = tv240p(buf,255,257,0)
t.init()
t.fb.fill(77)
t.pinit()
t.carrier.prescaler(0)
t.carrier.period(1)
kbd = keyboard_filter.bluekbd3601()
kbd.init()


font6x8_2b = simple_font.font6x8_2b
def type6x8_2b(msg,x,y,a=170,b=130,c=100,d=77,font=font6x8_2b,fontwidth=6,fontoffs=32):
    pal = bytearray((d&255,c,b,a))
    pallette = framebuf.FrameBuffer(pal,4,1,framebuf.GS8)
    mv = memoryview(font)
    for c in msg:
        if ord(c) >= fontoffs:
            t.fb.blit(framebuf.FrameBuffer(mv[(ord(c)-fontoffs)*16:],fontwidth,8,framebuf.GS2_HMSB),x,y,0 if d < 0 else -1,pallette)
        x += fontwidth



term = ansiterm.TermCursor(lambda c,x,y,term=None:(type6x8_2b(chr(c),20+y*6,20+x*8),show_starts()),lambda l: (t.fb.scroll(0,-8*l),t.fb.rect(0,20+8*(25-l),300,300,77,1)),30,25,lambda c,rl,cl,rh,ch:t.fb.rect(20+cl*6,20+rl*8,(ch-cl)*6,(rh-rl)*8,77,1))

cursor_buf = bytearray(6*8)
cursor_fb = framebuf.FrameBuffer(cursor_buf,6,8,framebuf.GS8)
cursor_fb.fill(77)
def beforewrite(term):
    x = term.col*6+20
    y = term.row*8+20
    t.fb.blit(cursor_fb,x,y)
def afterwrite(term):
    x = term.col*6+20
    y = term.row*8+20
    fb = framebuf.FrameBuffer(t.smv[t.line_length*y+x:],6,8,framebuf.GS8,t.line_length)
    cursor_fb.blit(fb,0,0)
    draw_cursor(x,y)

def draw_cursor(x,y):
    for ix in range(6):
        for iy in range(8):
            t.fb.pixel(ix+x,iy+y,max(100,t.fb.pixel(ix+x,iy+y)))

term.beforewrite = beforewrite
term.afterwrite = afterwrite

            
def show_starts(intens=100):
    t.fb.rect(18,20,2,8*25,77)             
    for i in range(term.rows):             
        if (term.line_starts>>i)&1:        
            t.fb.rect(18,20+i*8,2,7,intens)
            t.fb.rect(19,21+i*8,1,5,77)

uos.dupterm(term)

keybuf = micropython.RingIO(16)

term.readinto_cb = lambda b: keybuf.readinto(b) if keybuf.any() else None

kbd.modifiers = 0
def keydown(scancode):
    if scancode in keyboard_filter.KEY_IDS:
        if scancode in {118,78,6,38,15,134}:
            kbd.modifiers |= {118:1,78:2,6:4,38:8,15:16,134:32}[scancode]
        else:
            key = keyboard_filter.KEY_IDS[scancode]
            if kbd.modifiers&16:
                k = chr(ord(keyboard_filter.UPPERCASE[key])^0x40)
            elif kbd.modifiers&33:
                k = keyboard_filter.FN[key]
            elif kbd.modifiers&2:
                k = keyboard_filter.UPPERCASE[key]
            else:
                k = keyboard_filter.LOWERCASE[key]
            if k != '\0':
                keybuf.write(k.encode("utf8"))

def keyup(scancode):
    if scancode in {118,78,6,38,15,134}:
        kbd.modifiers &= ~({118:1,78:2,6:4,38:8,15:16,134:32}[scancode])

        
kbd.onkeydown = keydown
kbd.onkeyup = keyup


def clean_slate():
    for v in dir():
        exec("del "+v)
