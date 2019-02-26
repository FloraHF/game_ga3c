# Copyright (c) 2016, NVIDIA CORPORATION. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#  * Neither the name of NVIDIA CORPORATION nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
if sys.version_info >= (3,0):
    from queue import Queue
else:
    from Queue import Queue

import numpy as np
import scipy.misc as misc

from Config import Config
import GuardingTerritoryGame as GTG


class Environment:
    def __init__(self):
        self.game = GTG.GuardingTerritoryGame()
        self.nb_frames = Config.STACKED_FRAMES
        self.frame_q = Queue(maxsize=self.nb_frames)
        self.previous_state = None
        self.current_state = None
        self.total_reward = 0
        self.update_q = []
        for d in range(self.game.dcount):
            self.update_q.append('defender_'+str(d))
        for i in range(self.game.icount):
            self.update_q.append('intruder_'+str(i))
        print(self.update_q)

    def _get_current_state(self):
        if not self.frame_q.full():
            return None  # frame queue is not full yet.
        x_ = np.array(self.frame_q.queue)
        x_ = np.transpose(x_, [1, 2, 0])  # move channels
        return x_

    def _update_frame_q(self, new_state):
        if self.frame_q.full():
            self.frame_q.get()
        self.frame_q.put(new_state)

    def get_num_actions(self, id=0, player='intruder'):
        if player == 'intruder':
            return self.game.intruders[id].get_num_actions()
        elif player == 'defender':
            return self.game.defenders[id].get_num_actions()

    def defender_step(self, id, action):
        reward, done = self.game.defender_step(id, action)
        observation = self.game.get_state()

        self.total_reward += reward
        self._update_frame_q(observation)

        self.previous_state = self.current_state
        self.current_state = self._get_current_state()
        return self.previous_state, self.current_state, reward, done

    def intruder_step(self, id, action):
        reward, done = self.game.intruder_step(id, action)
        observation = self.game.get_state()
        # print('intruder', id, observation)

        self.total_reward += reward
        self._update_frame_q(observation)

        self.previous_state = self.current_state
        self.current_state = self._get_current_state()

        # print(self.current_state)
        return self.previous_state, self.current_state, reward, done

    def step(self, who, id, action):
        step_func = getattr(self, who + '_step')
        previous_state, current_state, reward, _ = step_func(id, action)
        done  = self.game.is_game_done()
        return previous_state, current_state, reward, done

    def reset(self):
        self.game.reset()
        self.total_reward = 0
        self.frame_q.queue.clear()
        self.update_occupied = False
        # while not self.frame_q.full():
        #     self.frame_q.put(self.game.get_state())
        self.previous_state = None
        self.current_state = None
        self.update_q = []
        for d in range(self.game.dcount):
            self.update_q.append('defender_'+str(d))
        for i in range(self.game.icount):
            self.update_q.append('intruder_'+str(i))
        print(self.update_q)
