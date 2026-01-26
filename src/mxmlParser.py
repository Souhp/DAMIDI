import xml.etree.ElementTree as ET
from collections import defaultdict
from bisect import bisect_right




def pitch_to_midi(note):
	pitch = note.find("pitch")
	if pitch is None:
		return None

	step = pitch.findtext("step")
	octave = int(pitch.findtext("octave"))
	alter = int(pitch.findtext("alter", "0"))

	step_to_semitone = {
		"C": 0, "D": 2, "E": 4,
		"F": 5, "G": 7, "A": 9, "B": 11,
	}

	return (octave + 1) * 12 + step_to_semitone[step] + alter




def event_sort_key(event):
	start_div = event.get("start_div", 0)

	# bars first when time is equal
	event_type = event.get("type")
	type_rank = 0 if event_type == "bar" else 1

	return (start_div, type_rank)




def parse_musicxml_chords(xml_path, default_bpm=120):
	tree = ET.parse(xml_path)
	root = tree.getroot()

	events = []
	current_div = 0

	bpm = default_bpm
	divisions_per_quarter = 1

	sound = root.find(".//sound[@tempo]")
	if sound is not None:
		bpm = float(sound.get("tempo"))

	for part in root.findall("part"):
		for measure in part.findall("measure"):
			measure_number = int(measure.get("number", 0))

			divisions_text = measure.findtext("attributes/divisions")
			if divisions_text:
				divisions_per_quarter = int(divisions_text)

			staff_time = defaultdict(int)
			chords = defaultdict(list)

			# BAR marker
			events.append({
				"type": "bar",
				"measure": measure_number,
				"start_div": current_div
			})

			for note in measure.findall("note"):
				staff = int(note.findtext("staff", "1"))
				duration = int(note.findtext("duration", "0"))

				if note.find("rest") is not None:
					staff_time[staff] += duration
					continue

				is_chord = note.find("chord") is not None
				start_div = current_div + staff_time[staff]

				midi_pitch = pitch_to_midi(note)
				if midi_pitch is not None:
					chords[start_div].append({
						"pitch": midi_pitch,
						"duration_div": duration
					})

				if not is_chord:
					staff_time[staff] += duration

			# Emit chords
			for start_div, notes in chords.items():
				events.append({
					"type": "chord",
					"measure": measure_number,
					"start_div": start_div,
					"notes": notes
				})

			# Advance cursor by longest staff
			current_div += max(staff_time.values(), default=0)
			



	events.sort(key=event_sort_key)
	##NOW TO ADD SECONDS

	seconds_per_quarter = 60.0 / default_bpm
	seconds_per_division = seconds_per_quarter / divisions_per_quarter
	
	for event in events:
		start_div = event.get("start_div", 0)
		event["start_sec"] = start_div * seconds_per_division


	total_time_sec = current_div * seconds_per_division
	# DEBUG OUTPUT
	debug = True
	if debug:
		debug_lines = []

		for i, event in enumerate(events):
			debug_lines.append("=" * 40)
			debug_lines.append(f"EVENT {i}")

			event_type = event.get("type")
			debug_lines.append(f"\ttype: {event_type}")
			debug_lines.append(f"\tmeasure: {event.get('measure')}")
			debug_lines.append(f"\tstart_div: {event.get('start_div')}")
			debug_lines.append(f"\tstart_sec: {event.get('start_sec')}")

			if event_type == "bar":
				debug_lines.append("\t[BAR MARKER]")

			elif event_type == "chord":
				notes = event.get("notes", [])
				debug_lines.append(f"\tchord_notes_count: {len(notes)}")

				for j, note in enumerate(notes):
					debug_lines.append(f"\t\tNOTE {j}")
					debug_lines.append(f"\t\t\tpitch: {note.get('pitch')}")
					debug_lines.append(f"\t\t\tduration_div: {note.get('duration_div')}")

			else:
				debug_lines.append("\t[UNKNOWN EVENT TYPE]")

		with open("debug.log", "w", encoding="utf-8") as f:
			f.write("\n".join(debug_lines))
		
	return events, total_time_sec

