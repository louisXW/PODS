import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="PODS",
    version="0.0.2",
    author="xia wei",
    author_email="xiawei@u.nus.edu",
    description="An optimization toolbox for expensive model optimization problems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/louisXW/PODS",
    packages=setuptools.find_packages(),
    install_requires=["numpy"],
    classifiers=[
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
