def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('algorithms', parent_package, top_path)

    config.add_data_dir('tests')

    config.add_subpackage('statistics')
    config.add_subpackage('diagnostics')

    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())
