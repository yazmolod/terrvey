# coding: utf-8

from cx_Freeze import setup, Executable

executables = [Executable('gui.py',
                          targetName='NIResearcher.exe',
                          base='Win32GUI')]

# модули которые исключаются из сборки
excludes = []

# модули которые помещаются в архив
zip_include_packages = []

# файлы которые будут скопированы вместе с модулями
include_files = [
    'ui',
    'media',
    '2rd stage'
]

# модули, которые будут скопированы
includes = [
]

# модули, которые будут скопированы со всеми вложенными модулями
packages = [
  'numpy',
]

options = {
    'build_exe': {
        'include_msvcr': True,
        'excludes': excludes,
        'includes': includes,
        'packages': packages,
        'zip_include_packages': zip_include_packages,
        'build_exe': 'build_NIResearcher',
        'include_files': include_files,
    }
}

setup(name='my_build',
      version='0.0.1',
      description='Приложение для обработки опросов',
      executables=executables,
      options=options)
