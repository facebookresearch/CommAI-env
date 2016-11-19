--[[
 Copyright (c) 2016-present, Facebook, Inc.
 All rights reserved.

 This source code is licensed under the BSD-style license found in the
 LICENSE file in the root directory of this source tree. An additional grant
 of patent rights can be found in the PATENTS file in the same directory.
]]--
require 'torch'
local zmq = require 'lzmq'

-- A simple example of a learner class in Torch
local TorchLearner = torch.class('TorchLearner')

function TorchLearner:__init(port, rf, f)
   self.port, self.t = port or 5556, 0

   -- closures to execute upon reward and received bit
   self.rf, self.f = rf, f

   self.ctx = zmq.context()
   self.skt = self.ctx:socket{zmq.PAIR,connect = 'tcp://localhost:'..self.port}

   return self
end

function TorchLearner:run()
   self.skt:send('hello')

   while not self._stop do
      local reward, err = self.skt:recv()
      if err then error(err) end

      self:rf(reward)

      local m_in, err = self.skt:recv()
      if err then error(err) end

      self.skt:send(self:f(m_in))

      self.t = self.t + 1
   end
end

function TorchLearner:close()
   self.skt:close()
   self.ctx:term()
end

-- Test Learner
local message = '00101110'
local tl = TorchLearner.new(
   tonumber(arg[1]),
   function(self, r) end,
   function(self, i)
      local msg_out = self.t % 7 == 0 and math.random(0, 1) or 1
      msg_out = self.t % 2 == 0 and message[self.t % 8] or msg_out
      return msg_out
   end
)

-- Go!
pcall(tl.run, tl)
tl:close()
