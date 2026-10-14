from setuptools import find_packages, setup

package_name = 'my_first_pkg'

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
    description='ROS 2 入門用パッケージ（talker/listener と、壁に向かって走るロボットを頭脳ノードで制御する演習）',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'my_talker = my_first_pkg.talker:main',
            'my_listener = my_first_pkg.listener:main',
            'sim_robot = my_first_pkg.sim_robot:main',
            'brain = my_first_pkg.brain:main',
        ],
    },
)
