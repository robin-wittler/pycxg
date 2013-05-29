#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'Robin Wittler'
__contact__ = 'real@the-real.org'
__license__ = 'GPL3+'
__copyright__ = '(c) 2013 by Robin Wittler'
__version__ = '0.0.1'


import sys

if sys.version_info < (2, 7, 0):
    raise SystemError('Python Version 2.7.0 or higher is needed.')

import logging
import urllib2
from lxml import etree
from argparse import Namespace
from argparse import ArgumentParser


try:
    import simplejson as json
except ImportError:
    import json


BASE_FORMAT_SYSLOG = (
    '%(name)s.%(funcName)s[%(process)d] ' +
    '%(levelname)s: %(message)s'
)

BASE_FORMAT_STDOUT = '%(asctime)s ' + BASE_FORMAT_SYSLOG


module_logger = logging.getLogger(__name__)


class PyCXGConfig(Namespace):
    def __init__(self, prog, **kwargs):
        super(PyCXGConfig, self).__init__(**kwargs)
        self.prog = prog


def get_args():
    parser = ArgumentParser(
        version='%(prog)s ' + __version__,
        description='A cli tool for the cxg.de nopaste service.',
    )

    parser.add_argument(
        '--url',
        default='http://api.cxg.de',
        help='The base cxg.de api url. Default: %(default)s',
    )

    parser.add_argument(
        '--timeout',
        default=5,
        type=int,
        help=(
            'When to return if the server did not answer (in seconds). ' +
            'Default: %(default)s'
        )
    )

    parser.add_argument(
        '--file',
        default=None,
        help=(
            'Rread the content to paste from a file '
            '- instead of reading it from stdin (which is the default).'
        )
    )

    parser.add_argument(
        '--title',
        default='No Title',
        help='Sets a title for the paste. Default: %(default)s'
    )

    parser.add_argument(
        '--format',
        default='auto',
        choices=('auto',),
        help=(
            'Set the format of the content. Possible choices: %(choices)s. ' +
            'Default: %(default)s. ' +
            'HINT: There is no API call at the moment for getting ' +
            'available choices. This might change in the Future.'
        )
    )

    parser.add_argument(
        '--loglevel',
        default='error',
        choices=('debug', 'info', 'warning', 'error'),
        help='Set the loglevel. Default: %(default)s',
    )

    config = parser.parse_args(namespace=PyCXGConfig(parser.prog))
    config.loglevel = getattr(logging, config.loglevel.upper(), logging.ERROR)
    return config


class PyCXG(object):
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(
            '%s.%s'
            %(self.config.prog, self.__class__.__name__)
        )

        self.create_paste_url = urllib2.urlparse.urljoin(
            self.config.url,
            'post'
        )
        self.get_paste_url = urllib2.urlparse.urljoin(
            self.config.url,
            'paste'
        )

        self.logger.debug('Initialized with: %r', config)

    def read_content_from_file(self):
        if self.config.file is None:
            self.logger.debug('Reading content from stdin.')
            return sys.stdin.read()
        else:
            self.logger.debug('Reading content from %r.', self.config.file)
            with open(self.config.file, 'r', 1) as fp:
                return fp.read()

    def paste_content(self, content):
        self.logger.debug(
            'Making a paste to url %r with title %r, raw content length ' +
            'of %r and with the format %r.',
            self.create_paste_url,
            self.config.title,
            len(content),
            self.config.format,
        )

        json_content = json.dumps(
            {
                'title': self.config.title,
                'content': content,
                'format': self.config.format
            }
        )

        request = urllib2.Request(
            self.create_paste_url,
            json_content
        )

        request.add_header('Content-Type', 'application/json')
        request.add_header('Content-Length', len(json_content))

        response = urllib2.urlopen(request, timeout=self.config.timeout)

        del json_content

        answer_html = etree.fromstringlist(
            response.read().split('\n'),
            etree.HTMLParser()
        )

        self.logger.debug(
            'The server answered with code %r and with text:\n\n%s\n\n',
            response.code,
            etree.tostring(answer_html, pretty_print=True)
        )

    def run(self):
        content = self.read_content_from_file()
        self.paste_content(content)

    def start(self):
        try:
            self.run()
        except Exception as error:
            self.logger.exception(error)
            self.logger.info('Quit because of previous Error.')
            sys.exit(2)
        else:
            sys.exit(0)


if __name__ == '__main__':
    config = get_args()
    logging.basicConfig(
        format=BASE_FORMAT_STDOUT,
        level=config.loglevel,
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    root_logger = logging.getLogger('')
    root_logger.setLevel(config.loglevel)
    a = PyCXG(config)
    a.start()


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4