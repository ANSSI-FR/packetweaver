import re
import io
import pytest
import packetweaver.libs.gen.pwcolor as pwc
import packetweaver.core.views.text as text


class TestText:
    test_str = 'test to display'

    @pytest.fixture()
    def io_out(self):
        """ Build the Log object to be tested

        A custom string stream is used to validate its outputs
        """
        out = io.StringIO()
        yield {'out': out, 'log': text.Log(output=out)}
        out.close()

    def test_help(self, io_out):
        io_out['log'].help(self.test_str)
        io_out['log'].help(self.test_str, lf=False)
        assert io_out['out'].getvalue() == '{0}\n{0}'.format(self.test_str)

    def test_info(self, io_out):
        io_out['log'].info(self.test_str)
        io_out['log'].info(self.test_str, lf=False)
        assert io_out['out'].getvalue() == '{0}\n{0}'.format(self.test_str)

    def test_success(self, io_out):
        io_out['log'].success(self.test_str)
        assert io_out['out'].getvalue() == '{}{}\n{}'.format(
            pwc.PWColor.colors['green'],
            self.test_str,
            pwc.PWColor.ENDC)
        io_out['log'].success(self.test_str, lf=False)
        assert io_out['out'].getvalue() == '{0}{1}\n{2}{0}{1}{2}'.format(
            pwc.PWColor.colors['green'],
            self.test_str,
            pwc.PWColor.ENDC)

    def test_warning(self, io_out):
        io_out['log'].warning(self.test_str)
        io_out['log'].warning(self.test_str, lf=False)
        assert io_out['out'].getvalue() == '{0}{1}\n{2}{0}{1}{2}'.format(
            pwc.PWColor.colors['yellow'],
            self.test_str,
            pwc.PWColor.ENDC)

    def test_error(self, io_out):
        io_out['log'].error(self.test_str)
        io_out['log'].error(self.test_str, lf=False)
        assert io_out['out'].getvalue() == '{0}{1}\n{2}{0}{1}{2}'.format(
            pwc.PWColor.colors['red'],
            self.test_str,
            pwc.PWColor.ENDC)

    def test_fail(self, io_out):
        io_out['log'].fail(self.test_str)
        io_out['log'].fail(self.test_str, lf=False)
        assert io_out['out'].getvalue() == '{0}{1}\n{2}{0}{1}{2}'.format(
            pwc.PWColor.colors['cyan'],
            self.test_str,
            pwc.PWColor.ENDC)

    def test_debug(self, io_out):
        io_out['log'].debug(self.test_str)
        io_out['log'].debug(self.test_str, lf=False)
        assert io_out['out'].getvalue() == '{0}{1}\n{2}{0}{1}{2}'.format(
            pwc.PWColor.colors['purple'],
            self.test_str,
            pwc.PWColor.ENDC)

    def test_progress(self, io_out):
        io_out['log'].progress(self.test_str)
        io_out['log'].progress(self.test_str, lf=False)
        assert io_out['out'].getvalue() == '{0}{1}\n{2}{0}{1}{2}'.format(
            pwc.PWColor.colors['blue'],
            self.test_str,
            pwc.PWColor.ENDC)

    def test_delimiter(self, io_out):
        io_out['log'].delimiter()
        io_out['log'].delimiter(width=10)
        io_out['log'].delimiter(width=10, char='*')
        assert io_out['out'].getvalue() == '{}\n{}\n{}\n'.format(
            '-' * io_out['log'].console_width,
            '-' * 10,
            '*' * 10)
        with pytest.raises(ValueError):
            io_out['log'].delimiter(width=-1)

    def test_delimiter_re(self, io_out):
        # test the output : only the main shape is tested (i.e --- [ ] ---)
        io_out['log'].delimiter(self.test_str)
        assert re.search('^-*\s\[\s.+\s\]\s-*$',
                         io_out['out'].getvalue()) is not None

        out = io.StringIO()  # build a new stream/Log couple for this case
        log = text.Log(output=out)
        log.delimiter(self.test_str, width=1)
        assert re.search('^-*\s\[\s.+\s\]\s-*$',
                         out.getvalue()) is not None

        out = io.StringIO()
        log = text.Log(output=out)
        log.delimiter(self.test_str, width=60)
        assert len(out.getvalue()) - 1 == 60  # exclude ending \n

    def test_start_effect(self):
        assert text.Log.start_effect('bold') == '{}'.format(
            pwc.PWColor.effects['bold'])
        with pytest.raises(KeyError):
            text.Log.start_effect('blue')

    def test_start_color(self):
        assert text.Log.start_color('red') == '{}'.format(
            pwc.PWColor.colors['red'],
            self.test_str)
        with pytest.raises(KeyError):
            text.Log.start_color('underline')

    def test_end_color(self):
        assert text.Log.end_color() == pwc.PWColor.ENDC

    def test_with_effect(self):
        assert text.Log.with_effect(
            'underline', self.test_str) == '{}{}{}'.format(
                pwc.PWColor.effects['underline'],
                self.test_str,
                pwc.PWColor.ENDC)
        with pytest.raises(KeyError):
            text.Log.with_effect('blue', self.test_str)

    def test_with_color(self):
        assert text.Log.with_color('blue', self.test_str) == '{}{}{}'.format(
            pwc.PWColor.colors['blue'],
            self.test_str,
            pwc.PWColor.ENDC)
        with pytest.raises(KeyError):
            text.Log.with_color('underline', self.test_str)

    def test_color(self):
        out = io.StringIO()
        out.truncate(0)
        with text.Log.color('progress', out):
            out.write(self.test_str)
        assert out.getvalue() == '{}{}{}'.format(pwc.PWColor.colors['blue'],
                                                 self.test_str,
                                                 pwc.PWColor.ENDC)
