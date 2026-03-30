import rtmidi
from collections import deque

class MidiListener:
	__slots__ = ("active_notes", "updated", "_midi_in", "_events","midiDeviceName")

	def __init__(self, input_name: str):
		self.active_notes = bytearray(128)
		self.updated	  = False
		self._events	  = deque()			   # thread-safe append/popleft
		self.midiDeviceName=input_name
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
		# Runs on a C++ thread — only append, never read here
		self._events.append(event[0])		   # event = ([bytes], delta_time)

	def tick(self) -> bytearray:
		self.updated = False
		notes  = self.active_notes
		events = self._events

		while events:
			msg = events.popleft()			   # [status, note, velocity]
			if len(msg) < 3:
				continue
			status = msg[0] & 0xF0			   # strip channel
			if status == 0x90 or status == 0x80:
				p, v = msg[1], msg[2]
				# note_on with vel=0 is a note_off
				v = v if (status == 0x90 and v > 0) else 0
				if notes[p] != v:
					notes[p]	 = v
					self.updated = True

		return notes

	def close(self):
		self._midi_in.close_port()
		del self._midi_in

	def __enter__(self):
		return self

	def __exit__(self, *_):
		self.close()
