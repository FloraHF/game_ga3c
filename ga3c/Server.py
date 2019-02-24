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

from multiprocessing import Queue

import time

from Config import Config
from Environment import Environment
from NetworkVP import NetworkVP
from ProcessAgent import ProcessAgent
from ProcessStats import ProcessStats
from ThreadDynamicAdjustment import ThreadDynamicAdjustment
from ThreadPredictor import ThreadPredictor
from ThreadTrainer import ThreadTrainer


class Server:
    def __init__(self):

        self.env = Environment()

        if Config.LOAD_CHECKPOINT:
            self.stats.episode_count.value = self.model.load()

        self.defender_count = Config.DEFENDER_COUNT
        self.intruder_count = Config.INTRUDER_COUNT

        self.defenders = []
        self.intruders = []

        self.stats = ProcessStats(self)

    def enable_players(self, who):
        player = getattr(self, who+'s')
        count = getattr(self, who+'_count')
        cur_len = len(player)
        if cur_len < count:
            for _ in range(cur_len, count):
                player.append(
                    ProcessAgent(len(player), who, self, self.stats.episode_log_q))
                player[-1].start()
                player[-1].predictor.start()
                player[-1].trainer.start()

    def disable_players(self, who):
        player = getattr(self, who+'s')
        count = getattr(self, who+'_count')
        for pid in reversed(range(len(player))):
            player[pid].predictor.exit_flag = True
            player[pid].predictor.join()
            player[pid].trainer.exit_flag = True
            player[pid].trainer.join()
            player[pid].exit_flag = True
            player.pop()


    def save_model(self):
        for i in self.intruders:
            i.model.save(self.stats.episode_count.value)
        for d in self.defenders:
            d.model.save(self.stats.episode_count.value)

    def main(self):
        self.stats.start()
        self.enable_players('intruder')
        self.enable_players('defender')

        if Config.PLAY_MODE:
            for i in self.intruders:
                i.trainer.enabled = False
            for d in self.defenders:
                d.trainer.enabled = False

        while self.stats.episode_count.value < Config.EPISODES:

            for d in range(self.defender_count):
                learning_rate_multiplier = (
                                            Config.LEARNING_RATE_END - Config.LEARNING_RATE_START) / Config.DEFENDER_ANNEALING_EPISODE_COUNT
                beta_multiplier = (Config.BETA_END - Config.BETA_START) / Config.DEFENDER_ANNEALING_EPISODE_COUNT
                step = min(self.stats.episode_count.value, Config.DEFENDER_ANNEALING_EPISODE_COUNT - 1)
                self.defenders[d].model.learning_rate = Config.LEARNING_RATE_START + learning_rate_multiplier * step
                self.defenders[d].model.beta = Config.BETA_START + beta_multiplier * step

            for i in range(self.intruder_count):
                learning_rate_multiplier = (
                                            Config.LEARNING_RATE_END - Config.LEARNING_RATE_START) / Config.INTRUDER_ANNEALING_EPISODE_COUNT
                beta_multiplier = (Config.BETA_END - Config.BETA_START) / Config.INTRUDER_ANNEALING_EPISODE_COUNT

                step = min(self.stats.episode_count.value, Config.INTRUDER_ANNEALING_EPISODE_COUNT - 1)
                self.intruders[i].model.learning_rate = Config.LEARNING_RATE_START + learning_rate_multiplier * step
                self.intruders[i].model.beta = Config.BETA_START + beta_multiplier * step

            # Saving is async - even if we start saving at a given episode, we may save the model at a later episode
            if Config.SAVE_MODELS and self.stats.should_save_model.value > 0:
                self.save_model()
                self.stats.should_save_model.value = 0

            time.sleep(0.01)

        self.disable_players('intruder')
        self.disable_players('defender')

        self.stats.exit_flag = True
