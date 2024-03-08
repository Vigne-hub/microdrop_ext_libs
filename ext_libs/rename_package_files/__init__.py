import fnmatch
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def rename_package_files(package_dir, old_name, new_name, exclude=None):
    '''
    Rename all occurrences of "old_name" to "new_name" in all files in
    the package. This includes filenames and occurrences in file contents.

    Renaming covers "CamelCase", "-"-separated, and "_"-separated
    occurrences of "old_name" replaced with the respective form of "new_name".

    Parameters:
    - package_dir: Root directory of the package.
    - old_name: Original ("-"-separated) package name.
    - new_name: New ("-"-separated) package name.
    - exclude: Patterns to exclude from renaming.
    '''
    if exclude is None:
        exclude = lambda old_name_i: False
    elif not callable(exclude):
        exclude_list = [exclude] if isinstance(exclude, str) else exclude
        exclude = lambda old_name_i: any(fnmatch.fnmatch(old_name_i, exclude_i) for exclude_i in exclude_list)

    names = {'old': old_name, 'new': new_name}
    underscore_names = {key: value.replace('-', '_') for key, value in names.items()}
    camel_names = {key: ''.join(word.title() for word in value.split('-')) for key, value in names.items()}

    def replace_in_file(file_path):
        if exclude(file_path) or '.git' in str(file_path):
            logger.debug('.. skipping contents rename of %s', file_path)
            return
        with file_path.open('rb') as f:
            data = f.read()
        modified_data = data.replace(names['old'].encode(), names['new'].encode()) \
            .replace(underscore_names['old'].encode(), underscore_names['new'].encode()) \
            .replace(camel_names['old'].encode(), camel_names['new'].encode())
        with file_path.open('wb') as f:
            f.write(modified_data)
        logger.debug('.. rename contents of %s', file_path)

    def rename_path(p):
        name_new = p.name
        if underscore_names['old'] in p.name:
            name_new = name_new.replace(underscore_names['old'], underscore_names['new'])
        if camel_names['old'] in p.name:
            name_new = name_new.replace(camel_names['old'], camel_names['new'])
        if name_new != p.name:
            p.rename(p.parent / name_new)
            logger.debug('.. rename %s', p)

    package_path = Path(package_dir)
    for p in package_path.rglob('*'):
        if p.is_file():
            replace_in_file(p)

    # Files have been handled, now directories in reverse order
    for p in sorted([p for p in package_path.rglob('*') if p.is_dir()], key=lambda p: p.parts, reverse=True):
        rename_path(p)
