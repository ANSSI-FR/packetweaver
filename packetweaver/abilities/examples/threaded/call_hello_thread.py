# coding: utf8
from packetweaver.core.ns import *


class Ability(ThreadedAbilityBase):
    _info = AbilityInfo(
        name='Call hello from a thread',
        description='Display an hello message - based on a ThreadedAbilityBase',
    )
    
    _option_list = [
        StrOpt('msg', default='Hello, I run in background', comment='hello message to display'),
    ]

    _dependencies = [('hello_thread', 'base', 'Hello from a thread')]

    def main(self):
        hello_abl = self.get_dependency('hello_thread', msg=self.msg)
        hello_abl.start()  # stop the called ability

        self._view.info("[main abl] Doing stuff in parallel")

        self._wait()  # waiting for ctrl+c to stop us
        hello_abl.stop()  # stop the called ability
        hello_abl.join()  # wait for it to finish
        self._view.info("[main abl] Main ability successfully run")
        self._view.info('[main abl] returned text: {}'.format(hello_abl.result()))

    def howto(self):
        self._view.delimiter('Hello')
        self._view.info("""
        Display an hello message using the Hello from a thread ability.
        
        The called ability is run in the background while text is displayed. 
        """)
