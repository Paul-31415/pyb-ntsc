Update:
diode modulator for much better shade resolution and tx linearity.
a lot of stuff. some incomplete shader compilation (automatic floating point assembler). fast exp and log approximation for gamma (unused).
now main.py launches a dupterm on the tv with text input sniffed from the debug uart of an adafru.it/3601 bluetooth keyboard on Y2
font was made by hand to look good on a portavision


Hardware:
pyb 1.0
  uses:
    DAC 1 (X5)  - outputs the video signal
    X4          - outputs the carrier
1 resistor (1kΩ)
1 signal diode

Transmitter was made by modulating X4 with X5

Diagram:
           (to antenna)
                |
         |\  |  |     1kΩ
 (X4) ___|  \|__^__/\  /\  ____ (X5)
         |  /|       \/  \/
         |/  |

The magic numbers for blanking_level, black_level, and white_level were found
 experimentally.

The pyboard's DAC is rated for 1 MHz operation, which corresponds to the default
 argument of hres=64 for the constructor. However, it can output much higher rates.
 The DMA seems to be limited to 65535 byte max looping transfer though.
 
NOTE: hres should be even if progressive == False (else you'll get a jittery picture)

progressive=False results in ~ 30 fps interlaced with 482 lines vertical resolution.
progressive=True  results in ~ 60 fps with 241 lines vertical resolution.

Demo:
 mandelbrot set zoom
  tilt pyboard to control cursor, press USR button to zoom in.
  Hold USR button for > 1 second then release to double iterations.
  Hold USR button for > 1 second, flip pyboard over, then release to
    toggle julia set mode.

  * It uses single precision floats so don't expect to be able to do deep zooms.


Tested on a pyboard 1.0 running at 168 MHz
