from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import unittest
import tasks.micro.small_comp as small_comp
from tasks.competition.tests.helpers import task_messenger

class TestSmallCompTasks(unittest.TestCase):
    #
    # helper methods
    #
    def testDebugTask2(self):
        self.assertEqual(0,1)

def main():
    unittest.main()

if __name__ == '__main__':
    main()
