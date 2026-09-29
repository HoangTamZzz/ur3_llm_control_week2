import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'ur3_llm_control'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Include tất cả các file launch
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        # Include tất cả các file config yaml
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools', 'requests', 'pyyaml'],
    zip_safe=True,
    maintainer='Student',
    maintainer_email='student@todo.todo',
    description='UR3 control using LLM and Skill-based Planning',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'main_node = ur3_llm_control.main_node:main',
        ],
    },
)