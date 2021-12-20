import numpy as np
import music21
from music21 import *
from sklearn.metrics.pairwise import cosine_similarity

"""
미디를 불러오고 매시업 하기 위한 다양한 함수들이 내장되어 있습니다.
"""

def convert_numpy_midi(mf: music21.midi.MidiFile) -> np.ndarray:
    """
    music21 midiFile을 입력받아서 이를 numpy 형태로 변환해서 반환합니다.
    <입력>
    mf: music21.midi.MidiFile. 모든 트랙 정보가 담겨 있는 미디 객체

    <출력>
    np.ndarray. shape: (len, pitch, velocity)
    len은 틱 단위로 되어 있습니다.
    pitch는 1~128 까지이며, 0인 경우 연주하지 않는 음입니다.
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


def open_midi(file_path: str, stream: bool = False) -> music21.midi.MidiFile:
    """
    music21 midiFile을 입력받아서 이를 numpy 형태로 변환한 뒤, 한 마디 단위로 분할하여 유사도를 비교할 수 있게 합니다.
    <입력>
    file_path: str ".midi"로 끝나는 확장자
    stream: boolean. stream 형태로 불러오는지 설정합니다. 

    <출력>
    music21 midiFile
    """

    try:
        mf = midi.MidiFile()
        mf.open(file_path) # 파싱 준비
        mf.read() # 파싱과 스트림
        mf.close() # 파일 메모리 분리

        if stream:
            return midi.translate.midiFileToStream(mf)
        else:
            return mf
    except Exception as e:
        print(f"Error on Loading Midi file! : {e}")
        
        return None


def split_per_bars(mf: music21.midi.MidiFile) -> np.ndarray:
    """
    music21 midiFile을 입력받아서 이를 numpy 형태로 변환해서 반환합니다.
    <입력>
    mf: music21.midi.MidiFile. 모든 트랙 정보가 담겨 있는 미디 객체

    <출력>
    np.ndarray. shape: (bars, len, pitch, velocity)
    bars는 전체 틱 수 / 한 마디당 틱 수의 올림 변환으로 구분됩니다.
    len은 틱 단위로 되어 있습니다.
    pitch는 1~128 까지이며, 0인 경우 연주하지 않는 음입니다.
    """

    npSong = convert_numpy_midi(mf) # 넘파이 형태로 분할합니다.
    barTicks = (mf.ticksPerQuarterNote * 4) # 4/4 박자로 가정합니다.

    splited_song = []
    for i in range(int(len(npSong)/barTicks)):
        splited_song.append(npSong[i*barTicks:(i+1)*barTicks]) 

    return np.array(splited_song)

def midi_cosine_similarity(split1, split2):
    """
    마디 단위로 나눠진 파일을 입력 받아 유사도를 계산합니다.
    <입력>
    split1, split2 : np.ndarray. shape: (len, pitch, velocity), split_per_bars의 결과값

    <출력>
    np.ndarray. shape: (len(split1), len(split2))
    각 마디 별 코사인 유사도를 구합니다.

    """

    similarity = np.empty((len(split1),len(split2)), dtype=np.float32)
    for i, barX in enumerate(split1):
        for j, barY in enumerate(split2):
            similarity[i][j] = cosine_similarity(barX.reshape(1,-1), barY.reshape(1,-1))[0][0] # 속도가 느림.. 개선 필요

    return similarity

def convert
def key_transform_12(mf):
    """
    마디 단위로 나눠진 파일을 입력 받아 12개 키로 변조된 파일을 반환합니다.
    """

    pass

def get_chords(df):
    """
    마디 단위로 나눠진 파일을 입력 받아 각 마디에서 추정된 코드를 반환합니다.
    """

    pass