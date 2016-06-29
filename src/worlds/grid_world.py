# Copyright (c) 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from core.task import World, on_world_start, on_message, on_sequence,\
    on_state_changed, on_timeout, on_output_message, on_world_init
from collections import namedtuple, Counter
import logging
import re


class Point(namedtuple('Point', ('x', 'y'))):
    def __add__(self, ot):
        return Point(self.x + ot.dx, self.y + ot.dy)

    def __sub__(self, ot):
        return Point(self.x - ot.dx, self.y - ot.dy)

    def __eq__(self, ot):
        return self.x == ot.x and self.y == ot.y

    def __str__(self):
        return 'Point({0},{1})'.format(self.x, self.y)

Span = namedtuple('Span', ('dx', 'dy'))


class GWEntity(namedtuple('GWEntity', ('name', 'pickable', 'traversable'))):
    def __str__(self):
        return self.name


class GridWorld(World):
    '''
    This is an infinite grid world where there can be
    objects layed around (pickable or not, traversable or not).
    '''
    def __init__(self, env, init_pos=(0, 0),
                 init_direction='north'):
        super(GridWorld, self).__init__(env)
        self._init_pos = init_pos
        self._init_direction = init_direction
        self.valid_directions = {
            'north': Span(0, -1),
            'east': Span(1, 0),
            'south': Span(0, 1),
            'west': Span(-1, 0)
        }
        self.clockwise_directions = ['north', 'east', 'south', 'west']
        self.logger = logging.getLogger(__name__)

    def put_entity(self, position, name, pickable, traversable):
        self.state.entities[position] = GWEntity(name, pickable, traversable)
        self.logger.info('Droped an entity {0} at position {1}'.format(
            name, position))

    def remove_entity(self, position):
        if position in self.state.entities:
            entity_name = self.state.entities[position].name
            del(self.state.entities[position])
            self.logger.info('Removed an entity {0} at position {1}'.format(
                entity_name, position))
        else:
            self.logger.warn("Asked to remove a non-existent entity "
                             "at position {0}".format(position))

    def get_entity(self, position):
        try:
            return self.state.entities[position]
        except KeyError:
            return None

    @on_world_init()
    def on_init_grid_world(self, event):
        # creates a new Point tuple using init_pos tuple as parameters
        self.state.learner_pos = Point(*self._init_pos)
        # the agent also faces one direction
        self.state.learner_direction = self._init_direction
        # dictionary of entities in the world
        self.state.entities = {}
        # inventory of the learner (a multiset)
        self.state.learner_inventory = Counter()

    @on_message(r"I turn left\.$")
    def on_turn_left(self, event):
        self.turn(-1)
        self.set_message("You turned left.")

    @on_message(r"I turn right\.$")
    def on_turn_right(self, event):
        self.turn(1)
        self.set_message("You turned right.")

    @on_message(r"I move forward\.$")
    def on_move_forward(self, event):
        self.move_forward(1)

    @on_message(r"I look\.$")
    def on_looking(self, event):
        self.logger.debug("Looking at position {0} with entities {1}".format(
            self.state.learner_pos, self.state.entities
        ))
        if self.state.learner_pos in self.state.entities:
            self.set_message("There is a {0}.".format(
                self.state.entities[self.state.learner_pos]
            ))
        else:
            self.set_message("There is nothing here.")

    @on_message(r"I pick up the \w+\.$")
    def on_pick_up(self, event):
        obj_name = re.match(r".*I pick up the (\w+).$", event.message).group(1)
        if self.state.learner_pos in self.state.entities and \
                obj_name == self.state.entities[self.state.learner_pos].name:
            # There is an object with the given name here
            if self.state.entities[self.state.learner_pos].pickable:
                # We pick it up
                self.state.learner_inventory[obj_name] += 1
                del self.state.entities[self.state.learner_pos]
                self.set_message("You picked up the {0}.".format(obj_name))
            else:
                self.set_message("You can't pick up the {0}.".format(obj_name))
        else:
            self.set_message("There is no {0} here.".format(obj_name))

    def turn(self, d):
        '''
        turns in the specified absolute (north, east, west, south) or clockwise
        relative (1, 2, 3, -1, 2, 3) direction.
        '''
        if d in self.valid_directions:
            self.state.learner_direction = d
        else:
            self.state.learner_direction = self.get_clockwise_direction(d)

    def get_clockwise_direction(self, d):
        return self.clockwise_directions[
            (self.clockwise_directions.index(
                self.state.learner_direction) + d) % 4]

    def move_forward(self, dz):
        if self.state.learner_direction == 'east':
            dx = dz
            dy = 0
        elif self.state.learner_direction == 'west':
            dx = -dz
            dy = 0
        elif self.state.learner_direction == 'north':
            dx = 0
            dy = -dz
        elif self.state.learner_direction == 'south':
            dx = 0
            dy = dz
        new_pos = self.state.learner_pos + Span(dx, dy)
        if self.can_move_to(new_pos):
            self.state.learner_pos = new_pos
            self.set_message("You moved.")
        else:
            self.set_message("You can't move.")

    def can_move_to(self, p):
        return p not in self.state.entities or \
            self.state.entities[p].traversable

    def __str__(self):
        '''
        Creates a grid world representation as a string
        '''
        grid_h = 5
        grid_w = 5
        # there should be cell in the center to show the learner
        assert grid_w % 2 == 1 and grid_h % 2 == 1
        cell_h = 2
        cell_w = 3
        lines = []
        l = []
        l.append(' ' * (cell_w + 1))
        for j in range(grid_w):
            l.append('{0: >{length}d} '.format(
                self.state.learner_pos.x - int(cell_w / 2) - 1 + j,
                length=cell_w))
        lines.append(''.join(l))
        l = []
        l.append(' ' * (cell_w + 1))
        l.append('+')
        for j in range(grid_w):
            l.append('-' * cell_w)
            l.append('+')
        lines.append(''.join(l))
        self.logger.debug("Drawing world with entities in " + str(
            self.state.entities))
        for i in range(grid_h):
            for k in range(cell_h):
                l = []
                if k == 0:
                    # print the coordinates
                    l.append('{0: >{length}d} '.format(
                        self.state.learner_pos.y - int(cell_h / 2) - 1 + i,
                        length=cell_w))
                else:
                    l.append(' ' * (cell_w + 1))
                l.append('+')

                for j in range(grid_w):
                    absolute_i = self.state.learner_pos.y + i - int(grid_h / 2)
                    absolute_j = self.state.learner_pos.x + j - int(grid_w / 2)
                    absolute_pos = Point(absolute_j, absolute_i)
                    if i == int(grid_h / 2) and j == int(grid_w / 2):
                        # we print the learner in the middle, using its
                        # facing direction first character
                        l.append(self.state.learner_direction[0] * cell_w)
                    elif absolute_pos in self.state.entities:
                        e = self.state.entities[absolute_pos]
                        # if there is an object, we fit as much as we can
                        # of the name
                        l.append('{0: <{length}}'.format(
                            e.name[k * cell_w:(k + 1) * cell_w],
                            length=cell_w))
                    else:
                        l.append(' ' * cell_w)
                    l.append('+')
                lines.append(''.join(l))
            l = []
            l.append(' ' * (cell_w + 1))
            l.append('+')
            for j in range(grid_w):
                l.append('-' * cell_w)
                l.append('+')
            lines.append(''.join(l))
        return '\n'.join(lines)
