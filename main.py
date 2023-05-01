__author__ = 'Sean Kraft'

import data_provider
from pathlib import Path

if __name__ == '__main__':
    data = data_provider.DataProvider()
    data.make_new_employee('Taylor Weins')
