from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'openpcdet_ros2'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(),  # 自動包含所有包
    package_data={
            'openpcdet_ros2' : ['Rosmaster_Lib/*'],     
    } ,
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*.urdf.xacro')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='dllab',
    maintainer_email='box930307@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
             'ps4_turtle = openpcdet_ros2.joy_to_twist:main',
            'ps4 = openpcdet_ros2.ps4:main'
        ],
    },
)
