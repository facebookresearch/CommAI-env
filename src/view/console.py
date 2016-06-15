from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import curses
import curses.textpad
import logging


class ConsoleView:

    def __init__(self, env, session):
        # TODO: Move environment and session outside of the class
        self._env = env
        self._session = session
        env._input_channel.sequence_updated.register(
            self.on_learner_sequence_updated)
        env._input_channel.message_updated.register(
            self.on_learner_message_updated)
        env._output_channel_listener.sequence_updated.register(
            self.on_env_sequence_updated)
        env._output_channel_listener.message_updated.register(
            self.on_env_message_updated)
        env.world_updated.register(
            self.on_world_updated)
        session.total_reward_updated.register(
            self.on_total_reward_updated)
        session.total_time_updated.register(
            self.on_total_time_updated)
        self.logger = logging.getLogger(__name__)
        # we save information for display later
        self.info = {'reward': 0, 'time': 0}

    def on_learner_message_updated(self, message):
        learner_input = self.channel_to_str(self._env._input_channel)
        self._win.addstr(self._learner_seq_y, 0, learner_input)
        self._win.refresh()

    def on_learner_sequence_updated(self, sequence):
        learner_input = self.channel_to_str(self._env._input_channel)
        self._win.addstr(self._learner_seq_y, 0, learner_input)
        self._win.refresh()

    def on_env_message_updated(self, message):
        env_output = self.channel_to_str(self._env._output_channel_listener)
        self._win.addstr(self._teacher_seq_y, 0, env_output)
        self._win.refresh()

    def on_env_sequence_updated(self, sequence):
        env_output = self.channel_to_str(self._env._output_channel_listener)
        self._win.addstr(self._teacher_seq_y, 0, env_output)
        self._win.refresh()

    def on_total_reward_updated(self, reward):
        self.info['reward'] = reward
        self.paint_info_win()

    def on_total_time_updated(self, time):
        self.info['time'] = time
        self.paint_info_win()
        self._stdscr.nodelay(1)
        key = self._stdscr.getch()
        if key == ord('+'):
            self._session.add_sleep(-0.001)
        elif key == ord('-'):
            self._session.add_sleep(0.001)
        if key == ord('0'):
            self._session.reset_sleep()

    def paint_info_win(self):
        self._info_win.addstr(0, 0, 'Total time: {0}'.format(
            self.info['time']))
        self._info_win.clrtobot()
        self._info_win.addstr(1, 0, 'Total reward: {0}'.format(
            self.info['reward']))
        self._info_win.clrtobot()
        self._info_win.refresh()

    def on_world_updated(self, world):
        if world:
            world.state_updated.register(self.on_world_state_updated)
            self._worldwin.addstr(0, 0, str(world))
        else:
            self._worldwin.clear()
        self._worldwin.refresh()

    def on_world_state_updated(self, world):
        self._worldwin.addstr(0, 0, str(world))
        self._worldwin.refresh()

    def initialize(self):
        # initialize curses
        self._stdscr = curses.initscr()
        begin_x = 0
        begin_y = 0
        self._teacher_seq_y = 0
        self._learner_seq_y = 1
        self._world_win_y = 3
        self._world_win_x = 0
        self._info_win_width = 20
        self._info_win_height = 2
        self._user_input_win_y = 2
        self._user_input_win_x = 10
        self.height, self.width = self._stdscr.getmaxyx()
        self._scroll_msg_length = self.width - self._info_win_width - 1
        self._win = self._stdscr.subwin(self.height, self.width, begin_y,
                                        begin_x)
        self._worldwin = self._win.subwin(self.height - self._world_win_y,
                                          self.width - self._world_win_x,
                                          self._world_win_y,
                                          self._world_win_x)
        # create info box with reward and time
        self._info_win = self._win.subwin(self._info_win_height,
                                          self._info_win_width,
                                          0,
                                          self.width - self._info_win_width)
        self._user_input_win = \
            self._win.subwin(1,
                             self.width - self._user_input_win_x,
                             self._user_input_win_y,
                             self._user_input_win_x)
        self._user_input_label_win = \
            self._win.subwin(1,
                             self._user_input_win_x - 1,
                             self._user_input_win_y,
                             0)
        curses.noecho()
        curses.cbreak()

    def finalize(self):
        curses.nocbreak()
        curses.echo()
        curses.endwin()

    def get_input(self):
        self._user_input_label_win.addstr(0, 0, 'input:')
        self._user_input_label_win.refresh()
        tb = curses.textpad.Textbox(self._user_input_win)
        tb.stripspaces = True
        input = tb.edit().strip()
        self._user_input_win.clear()
        return input

    def channel_to_str(self, channel):
        length = self._scroll_msg_length - 10
        if not channel.get_undeserialized():
            return "{0:_>{length}}".format(
                channel.get_text()[-length:], length=length)
        else:
            return "{1:_>{length}}[{0: <8}]".format(
                channel.get_undeserialized(),
                channel.get_text()[-length:], length=length)
