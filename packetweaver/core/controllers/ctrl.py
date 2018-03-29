# coding: utf8
import packetweaver.core.controllers.exceptions as ex


class Ctrl(object):
    """ Implement the main logic of controllers, previsioning a pre_ and post_ method """

    def __init__(self):
        pass

    def execute(self):
        try:
            self.pre_process()
            self.process()
            self.post_process()
        except ex.ExitPw:
            pass

    def pre_process(self):
        pass

    def post_process(self):
        pass

    def process(self):
        pass
