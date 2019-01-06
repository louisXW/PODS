import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="opdelft",
    version="0.0.1",
    author="xia wei",
    author_email="xiawei@u.nus.edu",
    description="An optimization toolbox for expensive environmental models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/louisXW/opdelft",
    packages=setuptools.find_packages(),
    install_requires=["numpy", "poap==0.1.26"],
    classifiers=[
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
