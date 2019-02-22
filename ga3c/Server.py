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


class Server:
    def __init__(self):

        self.env = Environment()

        self.training_step = 0
        self.frame_counter = 0

        self.defender_count = Config.DEFENDER_COUNT
        self.intruder_count = Config.INTRUDER_COUNT

        self.defenders = []
        self.intruders = []

    def add_defender(self):
        self.defenders.append(
            ProcessAgent(self, 'defender', len(self.defenders)))
        self.defenders[-1].start()

    def add_intruder(self):
        self.intruders.append(
            ProcessAgent(self, 'intruder', len(self.intruders)))
        self.intruders[-1].start()

    def enable_players(self):
        cur_len = len(self.defenders)
        if cur_len < self.defender_count:
            for _ in range(cur_len, self.defender_count):
                self.add_defender()
        cur_len = len(self.intruders)
        if cur_len < self.intruder_count:
            for _ in range(cur_len, self.intruder_count):
                self.add_intruder()

    def main(self):

        self.enable_players()

        if Config.PLAY_MODE:
            for i in range(len(self.intruders)):
                i.trainer.enabled = False
            for d in range(leng(self.defenders)):
                d.trainer.enabled = False
