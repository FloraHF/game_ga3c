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

from datetime import datetime
from multiprocessing import Process, Queue, Value
from threading import Thread

import numpy as np
import time

from Config import Config
from Environment import Environment
from Experience import Experience
from ThreadTrainer import ThreadTrainer
from ThreadPredictor import ThreadPredictor
from NetworkVP import NetworkVP


class ProcessAgent(Thread):
    def __init__(self, id, type, server, episode_log_q):
        super(ProcessAgent, self).__init__()

        self.id = id
        self.type = type
        self.server = server
        # self.trj_saver = open('trj'+str(self.id)+'.txt', 'w')

        self.training_step = 0
        self.frame_counter = 0

        self.prediction_q = Queue(maxsize=Config.MAX_QUEUE_SIZE)
        self.training_q = Queue(maxsize=Config.MAX_QUEUE_SIZE)
        self.episode_log_q = episode_log_q
        self.wait_q = Queue(maxsize=1)

        self.predictor = ThreadPredictor(self)
        self.trainer = ThreadTrainer(self)

        self.model = NetworkVP(Config.DEVICE, Config.NETWORK_NAME, Environment().get_num_actions())
        if Config.LOAD_CHECKPOINT:
            self.stats.episode_count.value = self.model.load()

        self.num_actions = self.server.env.get_num_actions()
        self.actions = np.arange(self.num_actions)

        self.discount_factor = Config.DISCOUNT

        self.exit_flag = False

    @staticmethod
    def _accumulate_rewards(experiences, discount_factor, terminal_reward):
        reward_sum = terminal_reward
        for t in reversed(range(0, len(experiences)-1)):
            r = np.clip(experiences[t].reward, Config.REWARD_MIN, Config.REWARD_MAX)
            reward_sum = discount_factor * reward_sum + r
            experiences[t].reward = reward_sum
        return experiences

    def convert_data(self, experiences):
        x_ = np.array([exp.state for exp in experiences])
        a_ = np.eye(self.num_actions)[np.array([exp.action for exp in experiences])].astype(np.float32)
        r_ = np.array([exp.reward for exp in experiences])
        return x_, r_, a_

    def predict(self, state):
        # put the state in the prediction q
        self.prediction_q.put(state)
        # wait for the prediction to come back
        p, v = self.wait_q.get()
        return p, v

    def select_action(self, prediction):
        if Config.PLAY_MODE:
            action = np.argmax(prediction)
        else:
            action = np.random.choice(self.actions, p=prediction)
        return action

    def train_model(self, x_, r_, a_):
        self.model.train(x_, r_, a_)
        self.training_step += 1
        self.frame_counter += x_.shape[0]

        self.server.stats.training_count.value += 1

        if Config.TENSORBOARD and self.stats.training_count.value % Config.TENSORBOARD_UPDATE_FREQUENCY == 0:
            self.model.log(x_, r_, a_)

    def run_episode(self):
        self.server.env.reset()
        done = False
        experiences = []

        time_count = 0
        reward_sum = 0.0

        moves = 0

        while not done:
            # moves += 1
            # print(self.type, self.id, moves, 'th move')
            # very first few frames
            if self.server.env.current_state is None:
                self.server.env.step(self.type, self.id, 0)  # 0 == NOOP
                continue
            prediction, value = self.predict(self.server.env.current_state)
            action = self.select_action(prediction)
            reward, done = self.server.env.step(self.type, self.id, action)
            # print(self.server.env.previous_state)
            # _x = self.server.env.previous_state
            # if self.type == 'defender':
            #     pid = self.id
            #     print(self.type, self.id, 'current location', _x[0][pid][0], _x[1][pid][0])
            # if self.type == 'intruder':
            #     pid = self.id + len(self.server.env.game.defenders)
            #     print(self.type, self.id, 'current location', _x[0][pid][0], _x[1][pid][0])
            reward_sum += reward
            if len(experiences):
                experiences[-1].reward = reward
            exp = Experience(self.server.env.previous_state, action, prediction, reward, done)
            experiences.append(exp)

            if done or time_count == Config.TIME_MAX+1:
                print(self.type, self.id, done)
                terminal_reward = 0 if done else old_value

                updated_exps = ProcessAgent._accumulate_rewards(experiences[:-1], self.discount_factor, terminal_reward)
                x_, r_, a_ = self.convert_data(updated_exps)
                yield x_, r_, a_, reward_sum

                # reset the tmax count
                time_count = 0
                # keep the last experience for the next batch
                experiences = [experiences[-1]]
                reward_sum = 0.0

            old_prediction = prediction
            old_value = value

            time_count += 1

    def run(self):
        # randomly sleep up to 1 second. helps agents boot smoothly.
        time.sleep(np.random.rand())
        np.random.seed(np.int32(time.time() % 1 * 1000 + self.id * 10))

        while not self.exit_flag.value:
            total_reward = 0
            total_length = 0
            for x_, r_, a_, reward_sum in self.run_episode():
                # self.trj_saver.write("%s, %s\n" % (x_[0,0,-1,0], x_[0,1,-1,0]))
                total_reward += reward_sum
                total_length += len(r_) + 1  # +1 for last frame that we drop
                self.training_q.put((x_, r_, a_))
            self.episode_log_q.put((datetime.now(), self.type, self.id, total_reward, total_length))
        # self.trj_saver.close()
