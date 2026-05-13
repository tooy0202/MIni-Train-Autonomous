import os
from glob import glob
from setuptools import setup

package_name = 'train_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    # data_files=[
    #     ('share/ament_index/resource_index/packages',
    #         ['resource/' + package_name]),
    #     ('share/' + package_name, ['package.xml']),
    # ],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/train_control']),
        ('share/train_control', ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jetson',
    maintainer_email='tooy0202@outlook.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'control_manager = train_control.control_manager_node:main',
            # 'esp32_serial = train_control.esp32_serial_node:main',
            'esp32_wifi = train_control.esp32_wifi_node:main',
        ],
    },
)
