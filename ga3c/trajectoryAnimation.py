import matplotlib as mpl
mpl.use('TkAgg')

import matplotlib.pyplot as plt
from matplotlib import animation
from numpy import random
import numpy as np
import re
from Config import Config

colors = ['red', 'red', 'blue']

def read_trj():
    x, y = [], []
    for _ in range(Config.DEFENDER_COUNT + Config.INTRUDER_COUNT):
        x.append([])
        y.append([])
    for d in range(Config.DEFENDER_COUNT):
        trj_file = open('trj_defender' + str(d) + '.txt', 'r')
        for line in trj_file:
            x[d].append(float(re.split(',', line)[0]))
            y[d].append(float(re.split(',', line)[1]))
        trj_file.close()
    for i in range(Config.INTRUDER_COUNT):
        trj_file = open('trj_intruder' + str(i) + '.txt', 'r')
        for line in trj_file:
            x[i+Config.DEFENDER_COUNT].append(float(re.split(',', line)[0]))
            y[i+Config.DEFENDER_COUNT].append(float(re.split(',', line)[1]))
        trj_file.close()
    x, nb_frames = _match_data_length(x)
    y, nb_frames = _match_data_length(y)
    return x, y, nb_frames

def _match_data_length(data):
    max_len = len(data[0])
    for i in range(1, len(data)):
        new_len = len(data[i])
        if new_len > max_len:
            max_len = new_len
    for i in range(len(data)):
        data[i].extend(data[i][-1] for _ in range(max_len-len(data[i])))
    nb_frames = max_len
    return data, nb_frames


figure = plt.figure()
axis = plt.axes(xlim=(-Config.WORLD_X_BOUND, Config.WORLD_X_BOUND), ylim=(-Config.WORLD_Y_BOUND, Config.WORLD_Y_BOUND))
plt.xlabel('x')
plt.ylabel('y')
trajectorys = []
x, y, nb_frames = read_trj()
for d in range(Config.DEFENDER_COUNT):
    trajectorys.append(axis.plot([],[],lw=2, color=colors[d])[0])
for i in range(Config.INTRUDER_COUNT):
    trajectorys.append(axis.plot([],[],lw=2, color=colors[i+Config.DEFENDER_COUNT])[0])

def init_trajectory():
    for trj in trajectorys:
        trj.set_data([],[])
    return trajectorys

def update(frame):
    for tid, trj in enumerate(trajectorys):
        trj.set_data(x[tid][frame], y[tid][frame])
    return trajectorys

trj_animation = animation.FuncAnimation(figure, update, init_func=init_trajectory,
                               frames=nb_frames, interval=100, blit=True)
plt.show()
