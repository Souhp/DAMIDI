import fluidsynth

class MidiPlayer:
    def __init__(self, soundfont, instrument=0):
        self.fs = fluidsynth.Synth(samplerate=24000.0)
        self.fs.start()  # uses default audio driver

        self.sfid = self.fs.sfload(soundfont)
        self.fs.program_select(0, self.sfid, 0, instrument)

    def note_on(self, pitch, velocity=127):
        self.fs.noteon(0, pitch, velocity)

    def note_off(self, pitch):
        self.fs.noteoff(0, pitch)

    def close(self):
        self.fs.delete()


