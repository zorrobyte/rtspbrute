import setuptools

from rtspbrute import __version__

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="rtspbrute",
    version=__version__,
    description="Tool for RTSP that brute-forces routes and credentials, makes screenshots!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/woolf/RTSPbrute",
    author="Woolf",
    author_email="woolf24@protonmail.com",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Internet",
        "Topic :: Multimedia :: Video :: Capture",
        "Topic :: Security",
        "Topic :: Utilities",
    ],
    keywords="netstalking rtsp brute cctv",
    project_urls={
        "Source": "https://gitlab.com/woolf/RTSPbrute",
        "Tracker": "https://gitlab.com/woolf/RTSPbrute/-/issues",
    },
    packages=setuptools.find_packages(),
    install_requires=["av<9", "Pillow<9", "rich<11"],
    python_requires=">=3.6",
    package_data={"rtspbrute": ["credentials.txt", "routes.txt"]},
    entry_points={"console_scripts": ["rtspbrute = rtspbrute.__main__:main"]},
)
