import configargparse
import sys
from os import path as os_path
version = '0.0.1'
cfg = None


def cfg_from_args(p, arg=None):
    """
    Convert configargparse object to configuration dict of dicts
    :param p:    configargparse object of parameters
    :param arg:  replace command line parameter
    :return cfg: dict with parameters

    - argument_groups (sections) is top level dict
    - '<prog>' strings in p replaces with p.prog
    """

    if arg:
        argv_save = sys.argv.copy()
        sys.argv[1:] = arg

    try:
        args = vars(p.parse_args())
        #args['verbose'] = args['verbose'][0]
        # groupsection by
        # cfg_strings = {}
        # # cfg= {section: {} for section in ['input_files', 'output_files', 'program']}
        # for gr in p._action_groups:
        #     # skip argparse argument groups
        #     if gr.title.split(' ')[-1] == 'arguments':
        #         continue
        #     cfg_strings[gr.title] = {key: args[key].replace('<prog>', p.prog) if \
        #         isinstance(args[key], str) else args[key] for key in \
        #         args.keys() & [a.dest for a in gr._group_actions]}
        #
        # cfg = ini2dict(cfg_strings)
        # #config = configargparse.parse_args(cfg_strings)
        cfg = args

    except Exception as e: #IOError
        print('Configuration ({}) error:'.format(p._default_config_files), end=' ')
        print('\n==> '.join([s for s in e.args if isinstance(s, str)]))  # e.message
        raise (e)
    except SystemExit as e:
        cfg = None

    if arg: # recover argv for next use
        sys.argv = argv_save

    return(cfg)


def parser(config_file_paths):
    """
    Define configuration
    :return p: configargparse object of parameters
    """

    p = configargparse.ArgumentParser(
        # can be called from "/instance" dir or just outside:
        default_config_files= config_file_paths,  # ../
        description="---------------------------------\n"
                    "Input text to DB and check errors\n"
                    "---------------------------------\n",
        formatter_class=configargparse.ArgumentDefaultsRawHelpFormatter,
        # formatter_class= configargparse.ArgumentDefaultsHelpFormatter,
        epilog='',
        args_for_writing_out_config_file=["-w", "--write-out-config-file"],
        write_out_config_file_arg_help_message=
        "takes the current command line args and writes them out to a config file "
        "the given path, then exits"
    )
    p.add_argument('--version', '-v', action='version', version=
    'textqueue version ' + version + ' - (c) 2017 Andrey Korzh <ao.korzh@gmail.com>.')
    # Fill configuration sections
    # All argumets of type str (default for add_argument...), because of
    # custom postprocessing based of args names in ini2dict
    p_env = p.add_argument_group('optional arguments for database:',
                                 'environment variables and database table name')
    p_env.add_argument(
        '--POSTGRES_USER', '-U', default='test', #nargs=?,
        help='')
    p_env.add_argument(
        '--POSTGRES_PASSWORD', '-P', default='admin', #nargs=?,
        help='')
    p_env.add_argument(
        '--POSTGRES_DB', default='postgres', #nargs=?,
        help='')
    #p_output_files = p.add_argument_group('output_files', 'Parameters of output files')
    p_env.add_argument(
        '--POSTGRES_TABLE', '-T', default='text__n_errors', #nargs=?,
        help='')

    p_env.add_argument(
        '--TARANTOOL_USER_NAME', default='admin', #nargs=?,
        help='')
    p_env.add_argument(
        '--TARANTOOL_USER_PASSWORD', default='admin', #nargs=?,
        help='')
    p_env.add_argument(
        '--TARANTOOL_TUBE_NAME', default='fifo_texts', #nargs=?,
        help='')

    p_program = p.add_argument_group('program', 'Program behaviour')
    p_program.add_argument(
        '--verbose', '-V', type=str, default='INFO', #nargs=1,
        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'],
        help='verbosity of messages in log file')

    return(p)


def get_cfg(new_arg=None, config_file_paths=None):
    if not config_file_paths:
        config_file_paths= [os_path.join(os_path.dirname(__file__), name) for name in (
'instance/.env', 'instance/tarantool.env')]
    return cfg_from_args(parser(config_file_paths), new_arg)
