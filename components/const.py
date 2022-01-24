import numpy as np
import random

random.seed(42)
np.random.seed(42)

n_tracks = 5  # number of tracks
n_pitches = 72  # number of pitches
lowest_pitch = 24  # MIDI note number of the lowest pitch
n_samples_per_song = 10  # number of samples to extract from each song in the datset
n_measures = 4  # number of measures per sample
beat_resolution = 4  # temporal resolution of a beat (in timestep)

programs = [0, 0, 25, 33, 48]  # program number for each track
is_drums = [True, False, False, False, False]  # drum indicator for each track
track_names = ['Drums', 'Piano', 'Guitar', 'Bass', 'Strings']  # name of each track
track_names_lower = [track.lower() for track in track_names]

measure_resolution = 4 * beat_resolution 
tempo = 100
tempo_array = np.full((4 * 4 * measure_resolution, 1), tempo)
