#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All rights reserved.
import logging

import ml.rl.types as rlt
import torch
from ml.rl.models.base import ModelBase
from ml.rl.training.trainer import Trainer


logger = logging.getLogger(__name__)


class RewardNetTrainer(Trainer):
    def __init__(
        self, reward_net: ModelBase, minibatch_size: int, use_gpu: bool = False
    ) -> None:
        self.reward_net = reward_net
        self.use_gpu = use_gpu
        self.minibatch_size = minibatch_size
        self.minibatch = 0
        self.loss_fn = torch.nn.MSELoss(reduction="mean")
        self.opt = torch.optim.Adam(self.reward_net.parameters(), lr=1e-3)

    def train(self, training_batch: rlt.PreprocessedTrainingBatch):
        training_input = training_batch.training_input
        if isinstance(training_input, rlt.PreprocessedRankingInput):
            target_reward = training_input.slate_reward
        else:
            target_reward = training_input.reward

        predicted_reward = self.reward_net(training_input).predicted_reward.squeeze()
        mse_loss = self.loss_fn(predicted_reward, target_reward)
        self.opt.zero_grad()
        mse_loss.backward()
        self.opt.step()
        mse_loss = mse_loss.detach()

        self.minibatch += 1
        if self.minibatch % 10 == 0:
            logger.info("{}-th batch: mse_loss={}".format(self.minibatch, mse_loss))

        return mse_loss

    def warm_start_components(self):
        return ["reward_net"]
