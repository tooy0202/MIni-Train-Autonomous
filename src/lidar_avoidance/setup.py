from setuptools import setup

package_name = 'lidar_avoidance'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',['resource/lidar_avoidance']),
        ('share/lidar_avoidance', ['package.xml']),
        ('share/lidar_avoidance/launch', ['launch/full_system.launch.py']),
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
            'avoidance = lidar_avoidance.avoidance_node:main',
        ],
    },
)
