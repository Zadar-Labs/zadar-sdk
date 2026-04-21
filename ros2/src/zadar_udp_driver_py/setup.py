from glob import glob

from setuptools import setup


package_name = "zadar_udp_driver_py"


setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml", "README.md"]),
        (f"share/{package_name}/config", sorted(glob("config/*.yaml"))),
        (f"share/{package_name}/launch", sorted(glob("launch/*.py"))),
    ],
    install_requires=["setuptools", "requests"],
    zip_safe=True,
    maintainer="Zadar Labs",
    maintainer_email="support-team@zadarlabs.com",
    description="ROS 2 Python driver for Zadar UDP radar sensors.",
    license="Proprietary",
    entry_points={
        "console_scripts": [
            "zadar_udp_driver = zadar_udp_driver_py.node:main",
        ],
    },
)
