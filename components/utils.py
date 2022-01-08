import numpy as np
import pypianoroll
import sys
from scipy.spatial import distance
from .util import *
from .const import *
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
    마디와 키 별로 분할된 넘파이 배열
    shape : (마디, 트랙, 마디당 틱, 피치)
    """

    if path[-3:] == 'npz' :
        score = pypianoroll.load(path)
    else:
        score = pypianoroll.read(path)



    tmp = score.copy() # 원본 손상 방지를 위해 복사 후 저장
    tmp.binarize()
    tmp.set_resolution(beat_resolution) # 비트당 틱을 재설정합니다.

    # 넘파이 배열로 변경합니다.
    pianoroll = (tmp.stack() > 0)
    # 주어진 피치범위로 잘라냅니다.
    pianoroll = pianoroll[:, :, lowest_pitch:lowest_pitch+n_pitches] # (track, time, 피치 수)

    # 전체 마디 수를 계산합니다.
    measure_resolution = 4 * beat_resolution # 한 마디는 4박이기 때문에 마디당 틱 수를 계산할 수 있습니다.
    n_measures = tmp.get_max_length() // measure_resolution
    sample = np.zeros((n_tracks, pianoroll.shape[1], pianoroll.shape[2]))
    for i, track in enumerate(tmp):
        try:
            track_idx = track_names_lower.index(track.name.strip().lower())
        except:
            continue
        sample[track_idx] = pianoroll[i, :]

    # 마디별로 배열을 잘라서 저장합니다.
    split = []
    for i in range(0, n_measures):
        split.append(sample[:, i*measure_resolution:(i+1)*measure_resolution, :])

    return np.stack(split)



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

def to_midi(target:np.ndarray, original:pypianoroll.Multitrack, dest:str="output.mid", tempo=100)->None:
    """
    넘파이 배열을 입력 받아서 미디 파일로 변환합니다.
    numpy 배열은 기존 Multitrack의 stack() 형태이며, 미디 변환 시 기타 정보(악기이름, 템포 등)을 얻기 위해 원본 멀티트랙도 같이 입력 받습니다.

    입력
    ----------
    target: 미디로 변환하고자 할 넘파이 배열
    original: 미디 파일을 만드는 데 참고하는 멀티트랙 파일
    dest: 생성하고자 하는 파일 주소. 기본값 : output.mid
    tempo: 템포 정보, 기본값 100
    """

    tempo_array = np.full((target.shape[1],1), tempo) # 템포 어레이 생성. 생성하고자 하는 길이만큼 해당 템포로 가득 채웁니다.

    tracks = [] # StandardTrack을 저장하기 위한 배열
    for t, track in enumerate(original.tracks): # 각각의 트랙을 반복하며 StandardTrack으로 변환
        tracks.append(pypianoroll.StandardTrack(is_drum=(track.name == "Drums"), name=track.name, program=track.program, pianoroll=target[t]))

    # 이제 Track이 나왔으니 MultiTrack으로 변환 가능
    new_score = pypianoroll.Multitrack(tracks=tracks, resolution=original.resolution, tempo=tempo_array)

    # 작성한 Multitrack을 미디로 변환해서 저장합니다.
    pypianoroll.write(dest, new_score)




def get_index(midi:np.ndarray) ->np.ndarray :
    """
    pypianoroll 형식으로 불러온 midi 파일의 경우 bool 형태의 구조를 가집니다. (해당 pitch의 값에 대해 true / false)
    마디별 유사도를 구하기 위해 pitch 값을 지정해줍니다. 
    ex. (0번째 마디, 0번째 track, time 0에 대해 4번째 pitch가 true 인 경우)
    [0,0,0,1,···,0] -> [0,0,0,4,···,0]

    입력
    ----------
    midi: .midi, .npz 를 변환한 numpy array

    출력
    ----------
    pitch 값들이 변경된 numpy array
    shape : (마디, 트랙, 마디당 틱, 피치)
    """

    get_midi_idx = np.argwhere(midi==1)   
    
    for idx_ in get_midi_idx :
        b, tr, t, p = idx_
        
        midi[b,tr,t,p] = p+1
        
    return midi


def dtw(midi1:np.ndarray,midi2:np.ndarray , norm_func:object = np.linalg.norm):
    """
    pypianoroll 형식으로 불러온 midi 파일의 유사도를 구하기 위한 함수입니다.
    Dynamic Time warping을 이용하여 두개의 midi 파일의 마디에 대한 유사도를 구합니다. 

    입력
    ----------
    midi1: .midi, .npz 를 변환한 numpy array
    midi2: .midi, .npz 를 변환한 numpy array
    norm_func: 거리를 구하기 위한 함수 default = Euclidean Distance, L2 norm

    출력
    ----------
    float, 마디에 대한 유사도
    """

    matrix = np.zeros((len(midi1) + 1, len(midi2) + 1))
    matrix[0,:] = np.inf
    matrix[:,0] = np.inf
    matrix[0,0] = 0
    for i, vec1 in enumerate(midi1):
        for j, vec2 in enumerate(midi2):
            cost = norm_func(vec1 - vec2)
            matrix[i + 1, j + 1] = cost + min(matrix[i, j + 1], matrix[i + 1, j], matrix[i, j])
    matrix = matrix[1:,1:]

    return matrix[-1,-1]

def js_similarity_matrix(midi1:np.ndarray,midi2:np.ndarray, dist_func:object = distance.jensenshannon):
    """
    pypianoroll 형식으로 불러온 midi 파일의 유사도를 구하기 위한 함수입니다.
    "비슷한 마디는 비슷한 분포를 가지고 있을 것이다." 라는 가정을 하고 
    마디 마다 분포를 구하여 분포 간의 유사도를 구합니다.
    KL-Divergence의 경우 분포가 겹치는 경우 0, 겹치지 않는 경우 무한대로 발산하기 때문에 Jensen–Shannon divergence를 사용함

    입력
    ----------
    midi1: .midi, .npz 를 변환한 numpy array
    midi2: .midi, .npz 를 변환한 numpy array
    dist_func: 거리를 구하기 위한 함수 default = Jensen–Shannon divergence
    출력
    ----------
    distance matrix, 마디들에 대한 유사도
    """
    # Calculate probability
    probability_midi1 = []
    probability_midi2 = []
    for i, values in enumerate(midi1):
        freq = np.histogram(values)
        prob = np.asarray(freq[0]) / sum(freq[0])
        for ix, x in enumerate(prob):
            if x == 0:
                prob[ix] = sys.float_info.epsilon

        probability_midi1.append(prob)
        
    for i, values in enumerate(midi2):
        freq = np.histogram(values)
        prob = np.asarray(freq[0]) / sum(freq[0])
        for ix, x in enumerate(prob):
            if x == 0:
                prob[ix] = sys.float_info.epsilon

        probability_midi2.append(prob)


    # shape
    dist_mx = np.zeros((midi1.shape[0], midi2.shape[0]), dtype=np.float32)

    for idx1,bar1 in enumerate(probability_midi1):
        for idx2,bar2 in enumerate(probability_midi2):
            kl = dist_func(bar1,bar2)  
            rescale_kl = 1 / (1 +kl)
            dist_mx[idx1, idx2] = rescale_kl
    return dist_mx


def get_dtw_similairy(path1:str,path2:str) ->tuple :
    """
    pypianoroll 형식으로 불러온 midi 파일의 유사도를 구하기 위한 함수입니다.
    Dynamic Time warping을 이용하여 두개의 midi 파일의 마디에 대한 유사도를 구하여 후보 index를 출력합니다.

    입력
    ----------
    midi1: .midi, .npz 를 변환한 numpy array
    midi2: .midi, .npz 를 변환한 numpy array
    출력
    ----------
    tuple, 유사도가 높은 마디들의 index
    """
    
    song1, song2 = load_as_np(path=path1), load_as_np(path=path2)

    tr_song1, tr_song2 = get_index(song1), get_index(song2)

    similarity = np.full((len(tr_song1), len(tr_song2), tr_song1.shape[1]),fill_value=np.inf)
    candidate_dict = dict()

    for track in range(tr_song1.shape[1]) : 
        for idx1, bar1 in enumerate(tr_song1) : 
            for idx2, bar2 in enumerate(tr_song2) :
                try : 
                    if bar1[track].mean() == 0. or bar2[track].mean() == 0 :
                        continue
                    else :
                        score = dtw(bar1[track], bar2[track])
                        similarity[idx1,idx2,track] = score
                except :
                    continue

    for track in range(5) :
        for i,j in np.squeeze(np.dstack(np.unravel_index(np.argsort(similarity[:,:,track].ravel()), (len(tr_song1), len(tr_song2)))),axis = 0) :
            if (i,j) not in candidate_dict :
                candidate_dict[(i,j)] = 0    
            if similarity[i,j,track] == np.inf :
                continue
            else :
                candidate_dict[(i,j)] += similarity[i,j,track]/5
    
    candidate_dict = dict([(idx,np.inf) if v == 0 else (idx,v) for idx,v in candidate_dict.items()])
    candidate_dict = sorted([items for items in candidate_dict.items()], key=lambda x: x[1])

    return candidate_dict[:10]

def get_distribution_similairy(path1:str,path2:str) ->tuple :

    """
    pypianoroll 형식으로 불러온 midi 파일의 유사도를 구하기 위한 함수입니다.
    Jensen–Shannon divergence을 이용하여 두개의 midi 파일의 마디에 대한 유사도를 구하여 후보 index를 출력합니다.

    입력
    ----------
    midi1: .midi, .npz 를 변환한 numpy array
    midi2: .midi, .npz 를 변환한 numpy array
    출력
    ----------
    tuple, 유사도가 높은 마디들의 index
    """

    song1, song2 = load_as_np(path=path1), load_as_np(path=path2)

    tr_song1, tr_song2 = get_index(song1), get_index(song2)
    similarity = np.zeros((len(tr_song1), len(tr_song2), len(track_names)), dtype = np.float32)
    candidate_dict = dict()
    for track in range(len(track_names)) :
        track_sim = js_similarity_matrix(tr_song1[:,track,:,:], tr_song2[:,track,:,:])
        track_sim = np.where(track_sim == 1, 0, track_sim)
        similarity[:,:,track] = track_sim

    for track in range(5) :
        for i,j in np.squeeze(np.dstack(np.unravel_index(np.argsort(similarity[:,:,track].ravel()), (len(tr_song1), len(tr_song2)))),axis = 0)[::-1] :
            if (i,j) not in candidate_dict :
                candidate_dict[(i,j)] = 0    
            if similarity[i,j,track] == 0 :
                continue
            else :
                candidate_dict[(i,j)] += similarity[i,j,track]/5
    candidate_dict = sorted([items for items in candidate_dict.items()], key=lambda x: -x[1])
    return candidate_dict[:10]

