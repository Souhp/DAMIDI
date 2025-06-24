from Event_Dispatch_Bus import trigger_event
import re
import asyncio
from mido import open_input








class midi_listener():

	def __init__(self, input_name: str):
		self.active_notes: dict[int, int] = {}
		self.input_name=input_name
		self.updated = False
		self.stop=False






	async def listen(self):

		"""
		Track active notes using a dict {pitch: velocity}.
		pitch | velocity
		"""
		print(f"Listening on MIDI input: {self.input_name}")
		pattern = r'note_on channel=(\d+) note=(\d+) velocity=(\d+) time=(\d+)'
		with open_input(self.input_name) as inport:
			while self.stop != True:
				for msg in inport.iter_pending():
					m = re.search(pattern, str(msg))
					if not m:
						continue

					_, pitch, velocity, _ = map(int, m.groups())

					if velocity > 0:
						self.active_notes[pitch] = velocity
						self.updated = True
						print(f"Note ON  [{pitch}] vel={velocity}")
					else:
						if pitch in self.active_notes:
							self.updated = True
							print(f"Note OFF [{pitch}] (was vel={self.active_notes[pitch]})")
							del self.active_notes[pitch]

				await asyncio.sleep(0.1)

				# Pass the dict directly
				#await trigger_event("pass_midi_info", active_notes)

			#await trigger_event("pass_midi_info", active_notes)
			print("midi")
			await asyncio.sleep(0.01)



def midi_to_note(midi_pitch):
	note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 
				  'F#', 'G', 'G#', 'A', 'A#', 'B']
	
	if 0 <= midi_pitch <= 127:
		note = note_names[midi_pitch % 12]
		octave = (midi_pitch // 12) - 1
		return f"{note}{octave}"
	else:
		raise ValueError("MIDI pitch must be between 0 and 127")


def strip_octave(note):
	return ''.join([char for char in note if not char.isdigit()])


def get_note_verisons(x):

	 
	 #   x = "c#"


	enharmonic_equivalents = {
		"C#": ["Db"],
		"D#": ["Eb"],
		"F#": ["Gb"],
		"G#": ["Ab"],
		"A#": ["Bb"],
	
	# Optionally include natural notes with rare enharmonics
		"B": ["Cb"],
		"E": ["Fb"],
		"C": ["B#"],
		"F": ["E#"]
	}
	return enharmonic_equivalents.get(x, [])


