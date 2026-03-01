
default_chromatic=["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]



major_scales = {
    "C":  ["C", "D", "E", "F", "G", "A", "B"],

    "G":  ["G", "A", "B", "C", "D", "E", "F#"],
    "D":  ["D", "E", "F#", "G", "A", "B", "C#"],
    "A":  ["A", "B", "C#", "D", "E", "F#", "G#"],
    "E":  ["E", "F#", "G#", "A", "B", "C#", "D#"],
    "B":  ["B", "C#", "D#", "E", "F#", "G#", "A#"],
    "F#": ["F#", "G#", "A#", "B", "C#", "D#", "E#"],
    "Gb": ["F#", "G#", "A#", "B", "C#", "D#", "E#"],  # Same as F#

    "Db": ["Db", "Eb", "F", "Gb", "Ab", "Bb", "C"],
    "C#": ["Db", "Eb", "F", "Gb", "Ab", "Bb", "C"],   # Same as Db

    "Ab": ["Ab", "Bb", "C", "Db", "Eb", "F", "G"],
    "Eb": ["Eb", "F", "G", "Ab", "Bb", "C", "D"],
    "Bb": ["Bb", "C", "D", "Eb", "F", "G", "A"],
    "F":  ["F", "G", "A", "Bb", "C", "D", "E"],
}
minor_scales = {
    "A":  ["A", "B", "C", "D", "E", "F", "G"],

    "E":  ["E", "F#", "G", "A", "B", "C", "D"],
    "B":  ["B", "C#", "D", "E", "F#", "G", "A"],
    "F#": ["F#", "G#", "A#", "B", "C#", "D#", "E#"],
    "C#": ["C#", "D#", "E", "F#", "G#", "A", "B"],
    "G#": ["G#", "A#", "B", "C#", "D#", "E", "F#"],
    "D#": ["D#", "E#", "F#", "G#", "A#", "B", "C#"],
    "Eb": ["D#", "E#", "F#", "G#", "A#", "B", "C#"],  # same as D# minor

    "Bb": ["Bb", "C", "Db", "Eb", "F", "Gb", "Ab"],
    "A#": ["Bb", "C", "Db", "Eb", "F", "Gb", "Ab"],   # same as Bb minor

    "F":  ["F", "G", "Ab", "Bb", "C", "Db", "Eb"],
    "C":  ["C", "D", "Eb", "F", "G", "Ab", "Bb"],
    "G":  ["G", "A", "Bb", "C", "D", "Eb", "F"],
    "D":  ["D", "E", "F", "G", "A", "Bb", "C"],
}

chromatic_major_scales = {
    "C":  ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B"],

    "G":  ["C", "C#", "D", "D#", "E", "F", "F#", "F##", "G#", "A", "A#", "B"],
    "D":  default_chromatic,
    "A":  default_chromatic,
    "E":  default_chromatic,
    "B":  ["E#", "C#", "D", "D#", "E", "E#", "F#", "F##", "G#", "A", "A#", "B"],
    "F#": ["B#", "C#", "C##", "D#", "E", "E#", "F#", "G", "G#", "A", "A#", "B"],##technically the e# is f in th chromatic from what ive seen but i use this scale for staff and there i need connections
    "Gb": ["B#", "C#", "C##", "D#", "E", "E#", "F#", "G", "G#", "A", "A#", "B"],

    #"Db": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
    "C#": ["C", "Db", "D", "Eb", "Fb", "F", "Gb", "G", "Ab", "A", "Bb", "Cb"],

    "Ab": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "Cb"],
    "Eb": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
    "Bb": ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"],
    "F":  ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"],
}

chromatic_minor_scales = {
    "A":  default_chromatic,

    "E":  default_chromatic,
    "B":  default_chromatic,
    "F#": default_chromatic,
    "C#": default_chromatic,
    "G#": default_chromatic,
    "D#": default_chromatic,
    "Eb": default_chromatic,

    "Bb": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
    "A#": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],

    "F":  ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "Bb", "B"],
    "C":  default_chromatic,
    "G":  default_chromatic,
    "D":  default_chromatic,
}





