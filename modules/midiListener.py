import rtmidi
from collections import deque

class MidiListener:
	__slots__ = ("active_notes", "updated", "_midi_in", "_events","midiDeviceName")

	def __init__(self, input_name: str):
		self.active_notes = {}   # pitch -> velocity
		self.updated = False
		self._events = deque()
		self.midiDeviceName = input_name
		self._midi_in = rtmidi.MidiIn()

		ports = self._midi_in.get_ports()

		try:
			idx = next(i for i, p in enumerate(ports) if input_name in p)
		except StopIteration:
			raise ValueError(f"Port '{input_name}' not found. Available: {ports}")

		self._midi_in.open_port(idx)
		self._midi_in.set_callback(self._callback)
		self._midi_in.ignore_types(sysex=True, timing=True, active_sense=True)

	def _callback(self, event, data=None):
		self._events.append(event[0])

	def tick(self) -> dict:
		self.updated = False
		notes  = self.active_notes
		events = self._events

		while events:
			msg = events.popleft()
			if len(msg) < 3:
				continue

			status = msg[0] & 0xF0
			if status == 0x90 or status == 0x80:
				p, v = msg[1], msg[2]

				if status == 0x90 and v > 0:
					if notes.get(p) != v:
						notes[p] = v
						self.updated = True
				else:
					if p in notes:
						del notes[p]
						self.updated = True

		return notes
	def close(self):
		self._midi_in.close_port()
		del self._midi_in

	def __enter__(self):
		return self

	def __exit__(self, *_):
		self.close()
