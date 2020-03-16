# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import torch
import torch.optim as optim
import torch.nn as nn
import model
from collections import deque
import numpy as np
from model import repackage_hidden
import train_weights
from .base_mixture_learner import BaseMixtureOfRNNsLearner
from observer import Observable

class CloneLearner(BaseMixtureOfRNNsLearner):
    def __init__(self, rnn_type, consolidate_moment, consolidate_threshold, nin, nout, ninp, nhid, nlayers,
            max_memory_size, max_ltm_size, init_stm_size, lr, batch_size, clip, optimizer, ltm_reinstatement, stm_consolidation,
            train_weights_before_predict, weights_trainer, residual_weights_trainer=None, 
            tie_weights=False, w_window=20, recent_window_size=5, dropout=0.2, is_cuda = True):
        self.optimizers = []
        self.consolidate_moment = consolidate_moment
        self.consolidation_threshold = consolidate_threshold
        self.reinstatement_threshold = consolidate_threshold
        self.consolidate_moment_ticks = 1
        self.residual_weights_trainer = None
        self.ltm_size = 0
        self.memory_size = 0
        self.max_ltm_size = max_ltm_size
        self.init_stm_size = init_stm_size
        self.max_memory_size = max_memory_size
        self.stm_consolidation = stm_consolidation
        self.ltm_reinstatement = ltm_reinstatement
        self.recent_window_size = recent_window_size
        self.weight_history = []
        self.weights_copied = Observable()
        self.weights_moved = Observable()
        self.ltm_size_updated = Observable()
        super(CloneLearner, self).__init__(rnn_type, nin, nout, ninp, nhid, nlayers,
            max_memory_size, lr, batch_size, clip, optimizer, 
            train_weights_before_predict, weights_trainer, tie_weights, w_window, dropout, is_cuda)
        self.weights_updated.register(self.save_weights_history)

    def cuda(self):
        super(CloneLearner, self).cuda()
        if self.residual_weights_trainer:
            self.residual_weights_trainer = self.residual_weights_trainer.cuda()

    def _initialize_model(self):
        memory_size = self.init_stm_size or self.max_memory_size
        for i in range(memory_size):
            self._create_new_rnn()

    def learn(self, data, targets):
        loss, prediction, outputs = self.predict_and_compute_loss(data, targets)
        self.train_modules(data, outputs, targets)
        self.train_weights(data, self.get_outputs().detach(), targets)
        self.consolidate_if_needed(data)
        return loss

    def train_modules(self, data, outputs, targets):
        if self.residual_weights_trainer:
            get_loss = self.get_loss_closure()
            n_modules = self.get_n_modules()
            self.residual_weights_trainer.optimize(
                    data, get_loss, until_convergence=True)
            weights = self.residual_weights_trainer.get_weights(data)
        else:
            weights = self.get_weights(data)
        prediction = self.get_prediction(weights.detach(), outputs)
        loss = self.get_loss(prediction, targets)
        self.backpropagate_and_train_modules(loss)

    def backpropagate_and_train_modules(self, loss):
        n_modules = self.get_n_modules()
        stm_start, stm_end = self._get_stm_interval()
        for opt in self.optimizers[stm_start:stm_end]:
            opt.zero_grad()
        loss.backward()
        for i,rnn in enumerate(self.rnns[stm_start:stm_end]):
            assert next(rnn.parameters()).requires_grad
            torch.nn.utils.clip_grad_norm_(rnn.parameters(), self.clip)
        for opt in self.optimizers[stm_start:stm_end]:
            opt.step()

    def consolidate_if_needed(self, data):
        if self.consolidate_moment_ticks > 20:
            #weight_diff = self.get_weight_diff(weights)
            #if (self.consolidate_moment and self.consolidate_moment_ticks % self.consolidate_moment == 0) or (self.consolidate_threshold and weight_diff > self.consolidate_threshold):
            self.consolidate_and_reinstate(data)
        self.consolidate_moment_ticks += 1

    def get_weight_diff(self, weights):
        current_weights= weights.detach().cpu().numpy() 
        current_weights /= np.linalg.norm(current_weights)
        recent_weights = self.get_recent_weights_mean()
        recent_weights  /= np.linalg.norm(recent_weights)
        #cosine =  np.dot(current_weights, recent_weights) / np.linalg.norm(current_weights) / np.linalg.norm(recent_weights)
        #weight_diff = 1 - cosine
        weight_diff = np.linalg.norm(current_weights - recent_weights)
        return weight_diff

    def consolidate_and_reinstate(self, data):
        ids_at_start = list(self.ids)
        consolidated = self.consolidate(data)
        if consolidated:
            print("Consolidated", self.get_memory_str())
        reinstated = self.reinstate(data)
        if reinstated:
            print("Reinstatated", self.get_memory_str())
            if self.ids == ids_at_start:
                print('Warning: CYCLING')

    def get_memory_str(self):
        return " ".join(self.ids[:self.ltm_size]) + "|" \
                + " ".join(self.ids[self.ltm_size:])

    def consolidate(self, data):
        consolidated = 0
        if self.stm_consolidation == 'fifo':
            raise NotImplementedError()
            #stm_start, stm_end = self._get_stm_interval()
            #self._consolidate_stm2ltm(stm_start)
            #stm_start, stm_end = self._get_stm_interval()
            #self._move_rnn(stm_start, stm_end)
        elif self.stm_consolidation == 'relevance':
            weights = self.get_weights(data).detach().cpu().numpy()
            while self._has_consolidation_candidates(weights):
                stm_idx = self._get_consolidation_candidate(weights)
                self._consolidate_stm2ltm(stm_idx)
                weights = self.get_weights(data).detach().cpu().numpy()
                consolidated += 1
        else:
            raise NotImplementedError(self.stm_consolidation)
        return consolidated

    def _has_consolidation_candidates(self, weights):
        if self._get_stm_size() == 1:
            return False
        consolidation_scores = self._get_consolidation_scores(weights)
        return (consolidation_scores > self.consolidation_threshold).any()

    def _get_consolidation_candidate(self, weights):
        stm_start, stm_end = self._get_stm_interval()
        consolidation_scores = self._get_consolidation_scores(weights)
        return stm_start+consolidation_scores.argmax()

    def _get_consolidation_scores(self, weights):
        stm_start, stm_end = self._get_stm_interval()
        scores = self.get_usage_scores(weights, stm_start, stm_end)
        return -scores

    def _consolidate_stm2ltm(self, stm_idx):
        ltm_start, ltm_end = self._get_ltm_interval()
        self._move_rnn(stm_idx, ltm_end)
        self._freeze_rnn(ltm_end)
        self.ltm_size += 1
        self.ltm_size_updated(self.ltm_size)
        print(f"Moving stm@{stm_idx} to ltm@{ltm_end} (ltm: {self.ltm_size})")
        if self.max_ltm_size is not None and self.ltm_size > self.max_ltm_size:
            self._delete_rnn(ltm_start)
            self.ltm_size -= 1
            self.ltm_size_updated(self.ltm_size)
            print("Reduced LTM size")


    def reinstate(self, data):
        reinstated = False
        if self.ltm_reinstatement == 'fifo':
            raise NotImplementedError()
        elif self.ltm_reinstatement == 'relevance':
            weights = self.get_weights(data).detach().cpu().numpy()
            while self._has_reinstatement_candidates(weights):
                self._reinstate_by_relevance(weights)
                weights = self.get_weights(data).detach().cpu().numpy()
                reinstated += 1
        elif self.ltm_reinstatement == 'none':
            raise NotImplementedError()
        else:
            raise NotImplementedError()
        return reinstated

    def _reinstate_by_relevance(self, weights):
        ltm_idx = self._get_reinstatement_candidate(weights)
        self._reinstate_ltm2stm(ltm_idx)

    def _has_reinstatement_candidates(self, weights):
        if self.ltm_size == 0:
            return False
        reinstatement_scores = self._get_reinstatement_scores(weights)
        return (reinstatement_scores > self.reinstatement_threshold).any()

    def _get_reinstatement_candidate(self, weights):
        ltm_start, ltm_end = self._get_ltm_interval()
        reinstatement_scores = self._get_reinstatement_scores(weights)
        return ltm_start + reinstatement_scores.argmax()

    def _get_reinstatement_scores(self, weights):
        ltm_start, ltm_end = self._get_ltm_interval()
        scores = self.get_usage_scores(weights, ltm_start, ltm_end)
        return scores

    def _reinstate_by_none(self, weights, network_full):
        if network_full:
            ltm_start, ltm_end = self._get_ltm_interval()
            self._delete_rnn(ltm_start)
            self._create_new_rnn()
        else:
            pass  #with this policy we don't reinstate until we are full

    def _reinstate_ltm2stm(self, ltm_idx):
        assert self._is_in_ltm(ltm_idx), ltm_module_idx
        _, stm_end = self._get_stm_interval()
        #self._copy_rnn(ltm_idx, stm_end)
        #ltm_start, _ = self._get_ltm_interval()
        #self.weights_trainer.set_weight_parameters(ltm_idx, 0)
        #self.reset_weight_history(ltm_idx)
        #self._move_rnn(ltm_idx, ltm_start)  # prepare to die, if you need to
        self._move_rnn(ltm_idx, stm_end)
        self._unfreeze_rnn(stm_end-1)
        if self.memory_size > self.max_memory_size:
            #ltm_start, _  = self._get_ltm_interval()
            stm_start, _ = self._get_stm_interval()
            self._delete_rnn(stm_start)
            print("Reduced STM size")
        print(f"Copied ltm@{ltm_idx} to stm@{stm_end} (ltm: {self.ltm_size})")

    def _is_in_ltm(self, idx):
        ltm_start, ltm_end = self._get_ltm_interval()
        return ltm_start <= idx < ltm_end

    def _get_ltm_interval(self):
        return (0, self.ltm_size)

    def _get_stm_interval(self):
        return (self.ltm_size, self.memory_size)
    
    def _get_stm_size(self):
        stm_start, stm_end = self._get_stm_interval()
        return stm_end - stm_start

    def _freeze_rnn(self, idx):
        for i, param in enumerate(self.rnns[idx].parameters()):
            param.requires_grad = False

    def _unfreeze_rnn(self, idx):
        for i, param in enumerate(self.rnns[idx].parameters()):
            param.requires_grad = True

    def _create_new_rnn(self):
        new_rnn_idx = super(CloneLearner, self)._create_new_rnn()
        self.weight_history.append(deque(maxlen=self.window_size))
        self.reset_weight_history(new_rnn_idx)
        self._create_new_optimizer()
        if self.residual_weights_trainer:
            self.residual_weights_trainer.append_weight()
        self.memory_size += 1
        return new_rnn_idx

    def _create_new_optimizer(self):
        opt_class = getattr(torch.optim, self.optimizer_algorithm)
        opt = opt_class(self.rnns[-1].parameters(), lr=self.lr)
        self.optimizers.append(opt)

    def _delete_rnn(self, rnn_idx):
        super(CloneLearner, self)._delete_rnn(rnn_idx)
        del self.optimizers[rnn_idx]
        if self.residual_weights_trainer:
            self.residual_weights_trainer.delete_weight(rnn_idx)
        self.memory_size -= 1

    def _copy_rnn(self, from_idx, to_idx):
        module_idx = self._create_new_rnn()
        self._copy_parameters(from_idx, module_idx)
        self._move_rnn(module_idx, to_idx)

    def _copy_parameters(self, source, dest):
        self.ids[dest] = self.ids[source] + "b"
        self.rnns[dest].load_state_dict(self.rnns[source].state_dict())
        self.optimizers[dest].load_state_dict(self.optimizers[source].state_dict())
        with torch.no_grad():
            for h_source, h_dest in zip(self.hidden[source], self.hidden[dest]):
                h_dest.copy_(h_source)
        self.weight_history[dest] = self.weight_history[source].copy()
        self.weights_trainer.set_weight_parameters(dest, self.weights_trainer.get_weight_parameters(source))
        self.weights_copied(source, dest)

    def _multiply_weights(self, idx, m):
        self.weights_trainer.set_weight_parameters(idx, self.weights_trainer.get_weight_parameters(idx) * m)

    def _move_rnn(self, from_idx, to_idx):
        if from_idx == to_idx:
            return
        self._move(self.optimizers, from_idx, to_idx)
        self._move(self.ids, from_idx, to_idx)
        self._move(self.rnns, from_idx, to_idx)
        self._move(self.hidden, from_idx, to_idx)
        self._move(self.weight_history, from_idx, to_idx)
        self.weights_trainer.move_weight(from_idx, to_idx)
        self.weights_moved(from_idx, to_idx)
        if self.residual_weights_trainer:
            self.residual_weights_trainer.move_weight(from_idx, to_idx)

    def _move(self, lst, from_idx, to_idx):
        if from_idx < to_idx:
            to_idx -= 1
        lst.insert(to_idx, lst.pop(from_idx))

    def get_lr(self):
        return self.optimizers[-1].param_groups[0]['lr']

    def reset_lr(self):
        self.optimizers[-1].param_groups[0]['lr'] = lr

    def save_weights_history(self, weights):
        for i in range(self.get_n_modules()):
            self.weight_history[i].append(weights[i].item())

    def get_most_relevant_module_in_recent_history(self, start=None, end=None):
        """returns the most relevant module"""
        mean_weights = self.get_mean_recent_weights(start, end)
        return start + np.argmax(np.abs(mean_weights))

    def get_usage_scores(self, weights, start=None, end=None):
        previous_mean_weights = self.get_recent_weights_mean(start, end, 0, self.window_size - self.recent_window_size)
        std_weights = self.get_recent_weights_std(start, end, 0, self.window_size - self.recent_window_size)
        mean_weights = self.get_recent_weights_mean(start, end, self.window_size - self.recent_window_size, self.window_size)
        min_std_size = 0.1
        std_weights[std_weights<min_std_size] = min_std_size
        return (np.abs(mean_weights) - np.abs(previous_mean_weights))/std_weights
    
    def get_recent_weights_mean(self, start=None, end=None, dt_start=None, dt_end=None):
        if start is None:
            start = 0
        if end is None:
            end = len(self.weight_history)
        if end == start:
            return None
        mean_weights = []
        for i in range(start, end):
            mean_weights.append(np.mean(list(itertools.islice(self.weight_history[i], dt_start, dt_end))))
        return np.array(mean_weights)

    def get_recent_weights_std(self, start=None, end=None, dt_start=None, dt_end=None):
        if start is None:
            start = 0
        if end is None:
            end = len(self.weight_history)
        if end == start:
            return None
        std_weights = []
        for i in range(start, end):
            std_weights.append(np.std(list(itertools.islice(self.weight_history[i], dt_start, dt_end))))
        return np.array(std_weights)

    def reset_weight_history(self, idx):
        self.weight_history[idx].extend([0]*self.window_size)

