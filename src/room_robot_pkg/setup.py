from setuptools import find_packages, setup

package_name = 'room_robot_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='hiraku',
    maintainer_email='hiraku00@gmail.com',
    description='2D の部屋を走る掃除ロボット（/scan と /cmd_vel を使う）',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'room_sim = room_robot_pkg.room_sim:main',
            'avoider = room_robot_pkg.avoider:main',
        ],
    },
)
