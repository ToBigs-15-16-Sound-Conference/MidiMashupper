import pypianoroll
import glob
import os

from .const import *

def midi_to_array(filename):
    if filename.endswith(".mid"):
        multitrack = pypianoroll.read(filename)
    elif filename.endswith(".npz"):
        multitrack = pypianoroll.load(filename)
    else:
        raise Exception("Midi file must be .npz or .mid")

    multitrack.binarize()
    multitrack.set_resolution(beat_resolution)
    pianoroll = (multitrack.stack() > 0)
    pianoroll = pianoroll[:, :, lowest_pitch:lowest_pitch + n_pitches]
    sample = np.zeros((n_tracks, pianoroll.shape[1], pianoroll.shape[2]))
    for i, track in enumerate(multitrack):
        try:
            track_idx = track_names_lower.index(track.name.strip().lower())
        except:
            continue
        sample[track_idx] = pianoroll[i, :]
    return sample

def array_to_midi(array):
    array = array.squeeze()
    tracks = []
    for idx, (program, is_drum, track_name) in enumerate(
            zip(programs, is_drums, track_names)
    ):
        pianoroll = np.pad(
            array[idx] > 0.5,
            ((0, 0), (lowest_pitch, 128 - lowest_pitch - n_pitches))
        )
        tracks.append(
            pypianoroll.BinaryTrack(
                name=track_name,
                program=program,
                is_drum=is_drum,
                pianoroll=pianoroll
            )
        )
    tempo_array = np.full((array.shape[-2], 1), tempo)
    m = pypianoroll.Multitrack(
        tracks=tracks,
        tempo=tempo_array,
        resolution=beat_resolution
    )
    return m

def save_midi(filename, array):
    m = array_to_midi(array)
    pypianoroll.write(filename, m)


def get_latest_ckpoint(ckpoint):
    pt_list = list(glob.glob(os.path.join(ckpoint, "*.pt")))
    if len(pt_list) == 0:
        return None
    return sorted(pt_list)[-1]

