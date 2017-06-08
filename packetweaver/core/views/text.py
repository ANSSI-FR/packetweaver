# coding: utf8
import sys
import types
import contextlib
import packetweaver.libs.gen.pwcolor as pwc
import packetweaver.core.views.view_interface as vi

class Log(vi.ViewInterface):
    def __init__(self, output=sys.stdout):
        """ View for text mode user interface

        Display in terminal patterns and colored messages using several
        informational levels

        :param output: stream used for the output - must implement a flush() method
        """
        super(Log, self).__init__()
        self._output = output
        self._console_width = 75

    def help(self, t, lf=True):
        """ Display a message to the specified output stream

        :param t: text to be displayed
        :param lf: if True, add a carriage return at the end (line feed)
        """
        self._output.write('{}{}'.format(t, '\n' if lf else ''))

    def info(self, t, lf=True):
        """ Display a message to the specified output stream

        :param t: text to be displayed
        :param lf: if True, add a carriage return at the end (line feed)
        """
        self._output.write('{}{}'.format(t, '\n' if lf else ''))

    def success(self, t, lf=True):
        """ Display a message to the specified output stream colored in green

        :param t: text to be displayed
        :param lf: if True, add a carriage return at the end (line feed)
        """
        with Log.color('green', self._output):
            self._output.write('{}{}'.format(t, '\n' if lf else ''))

    def warning(self, t, lf=True):
        """ Display a message to the specified output stream colored in yellow

        :param t: text to be displayed
        :param lf: if True, add a carriage return at the end (line feed)
        """
        with Log.color('yellow', self._output):
            self._output.write('{}{}'.format(t, '\n' if lf else ''))

    def error(self, t, lf=True):
        """ Display a message to the specified output stream colored in red

        :param t: text to be displayed
        :param lf: if True, add a carriage return at the end (line feed)
        """
        with Log.color('red', self._output):
            self._output.write('{}{}'.format(t, '\n' if lf else ''))

    def fail(self, t, lf=True):
        """ Display a message to the specified output stream colored in cyan

        :param t: text to be displayed
        :param lf: if True, add a carriage return at the end (line feed)
        """
        with Log.color('cyan', self._output):
            self._output.write('{}{}'.format(t, '\n' if lf else ''))

    def debug(self, t, lf=True):
        """ Display a message to the specified output stream colored in purple

        :param t: text to be displayed
        :param lf: if True, add a carriage return at the end (line feed)
        """
        with Log.color('purple', self._output):
            self._output.write('{}{}'.format(t, '\n' if lf else ''))

    def progress(self, t, lf=True):
        """ Display a message to the specified output stream colored in blue

        :param t: text to be displayed
        :param lf: if True, add a carriage return at the end (line feed)
        """
        with Log.color('blue', self._output):
            self._output.write('{}{}'.format(t, '\n' if lf else ''))

    def delimiter(self, title="", width=None, char="-"):
        """ Display a graphic separator

        A line separator, composed by a repeated character "char" will be displayed.
        If a title is provided, it will be displayed in the middle of it.

        Example 1:
            delimiter("Options") will render :
            ----------------------- [ Options ] ------------------------
        Example 2:
            delimiter("Options", width=1) will render :
             [ Options ]

        :param title: a title to display in the middle of the delimiter
        :param width: total length of the delimiter. If width < title, it will renders as Example 2
        :param char: the character to used in the delimiter
        """
        max_len = width if width else self._console_width
        if max_len < 0:
            raise ValueError("Width must be > 0")

        if title:
            # calculate number of "char" to display
            msg_len = len(title) + 6  # 6 = decoration " [ ] " around the title
            l = int((max_len - msg_len) / 2)
            if l < 1:
                self.info(' [ {} ] '.format(title))
            else:
                pad = ""
                if 2 * l + msg_len == max_len - 1:  # align when odd numbers
                    pad = "-"
                self.info('{} [ {} ] {}'.format(char * l, title, char * l + pad))
        else:
            self.info('{}'.format(char * max_len))

    @staticmethod
    def start_effect(t):
        """ Return the corresponding tag to start modifying a message

        :param t: color to apply (PwColor)
        :returns: the corresponding tag
        """
        return pwc.PWColor.effects[t]

    @staticmethod
    def start_color(t):
        # type (str) -> str
        """ Return the corresponding tag to start coloring a message

        :param t: color to apply (PwColor)
        :returns: the corresponding tag
        """
        return pwc.PWColor.colors[t]

    @staticmethod
    def end_color():
        """ Return the corresponding tag to stop applying an effect on a message

        This works for both start_color() and start_effect()

        :returns: the corresponding tag
        """
        return pwc.PWColor.ENDC

    @staticmethod
    def with_effect(e, t, prev_effect=''):
        """ Format a message using a specific text style modifier

        A low level function that let the user the task to display the modified content.

        :param e: effect tag to be used (PwColor)
        :param t: text to be modified
        :param prev_effect: repeat a previous color/effect modifier (e.g. 'red')that will be erased by insertion of the ENDC 
        :returns: customized text string
        """
        return '{}{}{}{}'.format(pwc.PWColor.effects[e], t, pwc.PWColor.ENDC, pwc.PWColor.colors[prev_effect])

    @staticmethod
    def with_color(c, t):
        """ Colorize a message using a specific color

        A low level function that let the user the task to display the modified content.

        :param c: color to apply (PwColor)
        :param t: text to be modified
        :returns: the corresponding text string
        """
        return '{}{}{}'.format(pwc.PWColor.colors[c], t, pwc.PWColor.ENDC)

    @staticmethod
    @contextlib.contextmanager
    def color(t, fd):
        """ Send a colored message to the specified output stream

        :param t: text to be displayed
        :param fd: the output stream
        """
        fd.write(pwc.PWColor.colors[t])
        yield
        fd.write(pwc.PWColor.ENDC)
        fd.flush()
