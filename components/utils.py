import numpy as np
import music21
from music21 import *


def convert_numpy_midi(mf: music21.midi.MidiFile) -> np.ndarray:
    """
    music21 midiFile을 입력받아서 이를 numpy 형태로 변환해서 반환합니다.
    <입력>
    """
    trackEvents = [] # 전체 playLists의 조합
    for track in mf.tracks:
        #노트의 시간, 음, 강도를 만들기
        playLists = [] # 트랙별 모든 시간
        dTime = 0 # 현재 시간단위
        for e in track.events:
            if type(e) == music21.midi.MidiEvent:
                playLists.append([dTime, e.pitch if e.pitch is not None else -1, e.velocity if e.velocity is not None else -1])
            elif type(e) == music21.midi.DeltaTime:
                dTime += e.time # 빈 시간 단위가 나오면.. 커서 이동
        trackEvents.append(playLists)

    musicLen = max(x[-1][0] for x in trackEvents) + 1 # 전체 트랙 중에 가장 긴 timelength 를 가지는 시간을 찾기
    npLists = np.zeros((musicLen, 128, 1), dtype=np.int8) # 음악 길이, 피치 범위, velocity

    for track in trackEvents: # 트랙별로 값을 입력합니다.
        for notes in track:
            npLists[notes[0], notes[1] + 1] = notes[2] + 1

    return npLists