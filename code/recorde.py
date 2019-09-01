from pynq.overlays.base import BaseOverlay
base = BaseOverlay("base.bit")
#录音
pAudio = base.audio
pAudio.select_microphone()
#BIN0-3 base.buttons[0-3] read
#SW0 SW1 base.switches[0-1] read 
#base.leds[0-3] on off
#base.rgbleds[0-2]
#base.buttons[num] 
while base.buttons[0].read() != 1:
    pass

base.leds[0].on()
pAudio.record(5)
base.leds[0].off()


#pAudio.load("ch.wav")
#pAudio.play()