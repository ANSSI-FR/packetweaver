# coding: utf8
import packetweaver.core.controllers.ctrl as ctrl


class TestCtrl:
    def test_execute(self):
        """ Ensure execute() execution order """
        class TestCtrl(ctrl.Ctrl):
            def __init__(self):
                super(TestCtrl, self).__init__()
                self.i = 0
                self.j = 0
                self.k = 0

            def pre_process(self):
                self.i = 1

            def process(self):
                self.j = self.i + 1

            def post_process(self):
                self.k = self.i + self.j + 1

        tc = TestCtrl()
        tc.execute()
        assert (tc.i, tc.j, tc.k) == (1, 2, 4)
