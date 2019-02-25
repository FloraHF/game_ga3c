from threading import Thread

import numpy as np

from Config import Config

class ThreadTrajectoryRecorder(Thread):
    def __init__(self, player):
        super(ThreadTrajectoryRecorder, self).__init__()
        self.setDaemon(True)

        self.player = player
        self.exit_flag = False

    def run(self):

        with open(Config.TRAJECTORY_FILENAME+self.player.type+str(self.player.id)+'.txt', 'a') as trj_logger:
            trj_logger.write('location:x, location:y, action, reward\n')
            while not (self.exit_flag and self.player.trajectory_log_q.empty()):
                x, y, action, reward = self.player.trajectory_log_q.get()
                trj_logger.write('%.3f, %.3f, %.3f, %.3f\n' % (x, y, action, reward))
                trj_logger.flush()
