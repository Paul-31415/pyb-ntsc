Hardware:
pyb 1.0
  uses:
    DAC 1 (X5)  - outputs the video signal
    X1          - outputs the carrier
1 resistor (1kΩ)
1 N channel MOSFET (5LN01SP)

Transmitter was made by modulating X1 with X5 using a signal n-mos ('YB 4F')
 from the sparkfun discrete semiconductor kit.

Diagram:

   (X1)──┐
        ┌┴┐
        │1│ r = 1 k ohm
        │k│
        └┬┘
         └──┐
            ├─────────── to wire antenna
     gate┃┠─┘drain
   (X5)──┨┃
         ┃┠─┐source
            └─────┐
                 ─┴─
                 ╶─╴
                  ─
                 gnd

The magic numbers for blanking_level, black_level, and white_level were found
 experimentally. More greyscale range can be gotten by modifying the schematic
 or using a better suited mosfet mixer.

The pyboard's DAC is rated for 1 MHz operation, which corresponds to the default
 argument of hres=64 for the constructor.
NOTE: hres should be even if progressive == False (else you'll get a jittery picture)

On my pyboard, it worked up to hres=124 but not above.

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

