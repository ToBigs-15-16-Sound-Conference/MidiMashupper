import numpy as np
import pypianoroll

"""
pypianoroll 을 사용해서 파일을 불러오는 유틸리티 파일입니다.
"""

def load_as_np(path:str, beat_resolution:int=4, lowest_pitch:int=24, n_pitches:int=72)->np.ndarray:
    """
    pypianoroll 형식으로 npz 또는 midi 파일을 불러와서 마디별로 분할된 넘파이 형식으로 반환합니다.

    입력
    ----------
    path:str 파일 주소를 나타내는 패스 .npz 또는 .mid로 끝나야 함
    beat_resolution: 한 마디당 타임 틱을 나타냅니다. 논문 기본값은 4입니다.
    lowest_pitch: 가장 낮은 음은 24번째 음입니다.
    n_pitches: 총 몇개의 음을 사용할지 결정합니다.

    출력
    ----------
    마디 별로 분할된 넘파이 배열
    shape : (마디, 트랙, 마디당 틱, 피치)
    """

    if path[:-3] == 'npz':
        score = pypianoroll.load(path)
    else:
        score = pypianoroll.read(path)

    # 키 변환 후 저장
    totalScore = []
    for key in range(-5, 7): # 아래로 5개, 위로 6개 키 변환 실시

        tmp = score.copy() # 원본 손상 방지를 위해 복사 후 저장
        trans = tmp.transpose(key) # 해당 키로 전환 실시
        
        # score.binarize() # 이진화 실시(어떤 이점이 있는지 모르겠습니다.)
        trans.set_resolution(beat_resolution) # 비트당 틱을 재설정합니다.

        # 넘파이 배열로 변경합니다.
        pianoroll = (trans.stack() > 0) # .stack() -> (track, time, pitch)

        # 주어진 피치범위로 잘라냅니다.
        pianoroll = pianoroll[:, :, lowest_pitch:lowest_pitch+n_pitches] # (track, time, 피치 수)

        # 전체 마디 수를 계산합니다.
        measure_resolution = 4 * beat_resolution # 한 마디는 4박이기 때문에 마디당 틱 수를 계산할 수 있습니다.
        n_measures = trans.get_max_length() // measure_resolution

        # 마디별로 배열을 잘라서 저장합니다.
        split = []
        for i in range(0, n_measures, measure_resolution):
            split.append(pianoroll[:, i:i+measure_resolution, :])


        totalScore.append(np.stack(split)) # shape: (마디, 트랙, 틱, 피치)


    return np.concatenate(totalScore) # shape: (마디 * 12, 트랙, 틱, 피치)


def concat_midi(score1:pypianoroll.Multitrack, pos1: int, score2:pypianoroll.Multitrack, pos2:int, pad:int=2)->pypianoroll.Multitrack:
    """
    pypianoroll 형식 파일 두 개를 받아서 두 지점을 이어 새로운 미디 파일로 만듭니다.
    score1은 먼저 나온 뒤 pos1 지점에서 끊기고, score2의 pos2지점에서 이어서 나옵니다.

    입력
    ----------
    score1: 첫 번째 멀티트랙 파일입니다. 먼저 재생될 미디 파일입니다.
    pos1: score1의 매시업 포인트입니다.
    score2: 두 번째 멀티트랙 파일입니다. 나중에 재생됩니다.
    pos2: score2의 매시업 포인트입니다.
    pad: pos1, pos2 이전/이후 몇 마디씩을 남기고 자를 것인지를 결정합니다.

    출력
    ----------
    pypianoroll.Multitrack. 
    """

    # 원본 손상을 방지하기 위해 복사해서 사용합니다
    score1_tmp = score1.copy()
    score2_tmp = score2.copy()

    # 최대 길이를 찾아서 이에 맞게 패딩합니다.
    score1_max = score1.get_max_length()
    score2_max = score2.get_max_length()
    score1_tmp.pad_to_same(score1_max)
    score2_tmp.pad_to_same(score2_max)

    # 트림 가능한 최대 거리를 구합니다.
    leftStart = min(0, pos1-pad)
    rightFinish = max(score2_max, pos2+pad)

    # 길이만큼 자르기
    score1_tmp.trim(leftStart, pos1)
    score2_tmp.trim(pos2, rightFinish)

    return score1_tmp, score2_tmp # 이 두개를 연결할 수 있는 방법이 없을지 살펴볼 필요성이 있다.







