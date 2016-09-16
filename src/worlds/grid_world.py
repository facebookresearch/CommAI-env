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
    on_state_changed, on_timeout, on_output_message
from collections import namedtuple, defaultdict
import logging
import tasks.competition.messages as msg


class Point(namedtuple('Point', ('x', 'y'))):
    '''Represents a point in the grid world'''
    def __add__(self, ot):
        return Point(self.x + ot.dx, self.y + ot.dy)

    def __sub__(self, ot):
        return Point(self.x - ot.dx, self.y - ot.dy)

    def __eq__(self, ot):
        return self.x == ot.x and self.y == ot.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __str__(self):
        return 'Point({0},{1})'.format(self.x, self.y)


class Span(namedtuple('Span', ('dx', 'dy'))):
    '''Represents a displacement.'''
    def __rmul__(self, m):
        return Span(m * self.dx, m * self.dy)

    def __mul__(self, m):
        return Span(m * self.dx, m * self.dy)


class GWEntity(namedtuple('GWEntity', ('name', 'pickable', 'traversable'))):
    def __str__(self):
        return self.name


class GridWorld(World):
    '''
    This is an infinite grid world where there can be
    objects layed around (pickable or not, traversable or not).

    Learner primitives:

        I move forward.

        I turn left/right.

        I look.

        I pick up the X.

        I give you a[n] X.

    Attributes:

        valid_directions[direction]: a mapping from the possible directions to
        a vector that goes one step in that direction
        (which can be added to a position).

    State variables:

        learner_pos: current position of the learner.

        learner_direction: current direction the learner is facing to.

        entities: contains the objects in the world (better if accessed with
        the get_entity primitive).

        learner_inventory: a mapping acting as a multiset of the objects that
        the learner has.

        teacher_inventory: a mapping acting as a multiset of the objects that
        the teacher has.

        teacher_accepts: a set of objects that the teacher is willing to accept
        if the learner wants to give one to the teacher.
    '''
    def __init__(self, init_pos=(0, 0),
                 init_direction='north'):
        super(GridWorld, self).__init__()
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
        '''creates an entity with the given name, at the given position,
        while informing whether the agent can pick it up and whether it can
        move over it.'''
        self.state.entities[position] = GWEntity(name, pickable, traversable)
        self.logger.info('Droped an entity {0} at position {1}'.format(
            name, position))

    def remove_entity(self, position):
        '''returns the entity at the given position.'''
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

    @on_world_start()
    def on_start_grid_world(self, event):
        # creates a new Point tuple using init_pos tuple as parameters
        self.state.learner_pos = Point(*self._init_pos)
        # the agent also faces one direction
        self.state.learner_direction = self._init_direction
        # dictionary of entities in the world
        self.state.entities = {}
        # inventory of the learner (a multiset)
        self.state.learner_inventory = defaultdict(int)
        # inventory of the teacher (a multiset)
        self.state.teacher_inventory = defaultdict(int)
        # set of objects the teacher is willing to receive
        self.state.teacher_accepts = set()

    @on_message(r"I turn left\.$")
    def on_turn_left(self, event):
        self.turn(-1)
        self.set_message("You turned left, you are now facing {direction}."
                         .format(direction=self.state.learner_direction))

    @on_message(r"I turn right\.$")
    def on_turn_right(self, event):
        self.turn(1)
        self.set_message("You turned right, you are now facing {direction}."
                         .format(direction=self.state.learner_direction))

    @on_message(r"I move forward\.$")
    def on_move_forward(self, event):
        self.move_forward(1)

    @on_message(r"I look\.$")
    def on_looking(self, event):
        look_pos = self.state.learner_pos + \
            self.valid_directions[self.state.learner_direction]
        self.logger.debug("Looking at position {0} with entities {1}".format(
            look_pos, self.state.entities
        ))
        if look_pos in self.state.entities:
            self.set_message("There is a {0}.".format(
                self.state.entities[look_pos]
            ))
        else:
            self.set_message("There is nothing here.")

    @on_message(r"I pick up the (\w+)\.$")
    def on_pick_up(self, event):
        obj_name = event.get_match(1)
        obj_pos = self.state.learner_pos + \
            self.valid_directions[self.state.learner_direction]
        if obj_pos in self.state.entities and \
                obj_name == self.state.entities[obj_pos].name:
            # There is an object with the given name here
            if self.state.entities[obj_pos].pickable:
                # We pick it up
                self.state.learner_inventory[obj_name] += 1
                del self.state.entities[obj_pos]
                self.set_message("You picked up the {0}.".format(obj_name))
            else:
                self.set_message("You can't pick up the {0}.".format(obj_name))
        else:
            self.set_message("There is no {0} here.".format(obj_name))

    @on_message("I give you (an? (\w+))\.$")
    def on_object_given(self, event):
        object_ = event.get_match(2)
        if object_ in self.state.teacher_accepts:
            self.state.learner_inventory[object_] -= 1
            self.state.teacher_inventory[object_] += 1
            self.set_message("You gave me {indef_object}.".format(
                indef_object=msg.indef_article(object_)))
        else:
            self.set_message("I haven't asked you for {indef_object}.".format(
                indef_object=msg.indef_article(object_)))

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
