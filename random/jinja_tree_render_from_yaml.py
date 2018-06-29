import os
import yaml
import errno
import mimetypes

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from jinja2 import Environment, FileSystemLoader, StrictUndefined


RENDERED_FILE_EXTENSIONS = ['.xml', '.properties', '.txt', '.yml', '.conf']


def load_dict_from_yaml(yaml_file):
    """
    :param yaml_file: key value yaml file
    :return: dictionary of config
    """
    config_data = yaml.load(open(yaml_file))
    return config_data


def rendered_extension(f):
    file_extension = os.path.splitext(f)[1]
    if file_extension in RENDERED_FILE_EXTENSIONS:
        return True
    return False


def trim_template_from_path(path):
    """
    Removes /templates from path to be used to output to tb-dev/service instead f tb-dev/templates/service
    :param path: 
    :return: stripped from 'templates' path
    """
    split_path = os.path.split(path)
    if split_path[0] == 'templates':
        return "/".join(split_path[1:])
    return path


def render_template_tree(template_dir, config_data, output_pref):
    """
    :param template_dir: path to the directory containing all the templates to be rendered
    :param config_data: path to the yaml file containing all key values for the template
    :param output_pref: optional prefix to label the output directory of the rendered
    templates
    :return: does not return anything, just generates files.
    If a variable in a template isn't resolved, an exception will be raised and the script will exit
    """
    if all(k in config_data for k in ('partner', 'environment')):
        print('Rendering config for partner "{}" in environment "{}"'.format(config_data['partner'],
                                                                             config_data['environment']))
    else:
        print("NO ENVIRONMENT or PARTNER defined in the yaml variable file")
        print('Exiting')
        exit(1)

    if output_pref == '':
        output_prefix = "{}-{}".format(config_data['partner'], config_data['environment'])
    else:
        output_prefix = "{}-{}-{}".format(output_pref, config_data['partner'], config_data['environment'])
    for path, dirs, files in os.walk(template_dir):
        try:
            # dest_dir = trim_template_from_path(path)
            dest_dir = path
            output_path = os.path.join(output_prefix, dest_dir)
            os.makedirs(output_path)
        except OSError as e:
            if e.errno == errno.EEXIST:
                print('Directory already exists and was not created.')
            else:
                raise

        env = Environment(loader=FileSystemLoader(path),
                          trim_blocks=True,
                          lstrip_blocks=True,
                          undefined=StrictUndefined)
        for f in files:
            print("Rendering {}".format(os.path.join(output_path, f)))
            if rendered_extension(f):
                rendered = env.get_template(f).render(config_data)

                with open(os.path.join(output_path, f), 'w+') as out:
                    out.write(rendered)
            else:
                with open(os.path.join(output_path, f), 'w+') as out:
                    out.write(f)
    return


def parse_args():
    """
    Simple argument parsing
    :return:
    """
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawDescriptionHelpFormatter)

    parser.add_argument('--config-file',
                        help="""
                        yaml configuration file for environment / partner
                        """,
                        dest='config_file',
                        required=True)

    parser.add_argument('--template-dir',
                        help="""
                        directory containing template file tree
                        """,
                        dest='template_dir',
                        default='../templates')

    parser.add_argument('--output-prefix',
                        help="""
                        add a prefix to the output directory name
                        """,
                        dest='output_pref',
                        default='')

    return parser.parse_args()


def main():
    args = parse_args()

    template_dir = args.template_dir
    config_file = args.config_file
    output_pref = args.output_pref

    config_data = load_dict_from_yaml(config_file)

    render_template_tree(template_dir, config_data, output_pref)


if __name__ == "__main__":
    main()
