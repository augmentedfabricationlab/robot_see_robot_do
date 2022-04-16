---
layout: page
title: Getting Started
---

### Requirements

* Rhino 7 / Grasshopper
* [Anaconda Python](https://www.anaconda.com/distribution/?gclid=CjwKCAjwo9rtBRAdEiwA_WXcFoyH8v3m-gVC55J6YzR0HpgB8R-PwM-FClIIR1bIPYZXsBtbPRfJ8xoC6HsQAvD_BwE)
* [Visual Studio Code](https://code.visualstudio.com/)
* [Github Desktop](https://desktop.github.com/)
* [Docker Community Edition](https://www.docker.com/get-started): Download it for [Windows](https://store.docker.com/editions/community/docker-ce-desktop-windows). Leave "switch Linux containers to Windows containers" disabled.

### Dependencies

* [COMPAS](https://compas-dev.github.io/)
* [COMPAS FAB](https://gramaziokohler.github.io/compas_fab/latest/)
* [UR Fabrication Control](https://github.com/augmentedfabricationlab/ur_fabrication_control)

### 1. Setting up the Anaconda environment with COMPAS

Execute the commands below in Anaconda Prompt:
	
    (base) conda config --add channels conda-forge

#### Windows
    (base) conda create -n rsrd compas_fab=0.22.0 --yes
    (base) conda activate rsrd

#### Mac
    (base) conda create -n rsrd compas_fab=0.22.0 python.app --yes
    (base) conda activate rsrd
    

#### Verify Installation

    (rsrd) pip show compas_fab

    Name: compas-fab
    Version: 0.22.0
    Summary: Robotic fabrication package for the COMPAS Framework
    ...

#### Install on Rhino

    (rsrd) python -m compas_rhino.install -v 7.0


### 2. Installation of Dependencies

    (rsrd) conda install git

#### UR Fabrication Control
    
    (rsrd) python -m pip install git+https://github.com/augmentedfabricationlab/ur_fabrication_control@master#egg=ur_fabrication_control
    (rsrd) python -m compas_rhino.install -p ur_fabrication_control -v 7.0


### 3. Cloning the Course Repository

Create a workspace directory:

    C:\Users\YOUR_USERNAME\workspace\projects

Then open Github Desktop and clone the [Robot See Robot Do repository](https://github.com/augmentedfabricationlab/robot_see_robot_do) repository into your projects folder. Then install the repo within your environment (in editable mode):

    (rsrd) pip install -e your_filepath_to_robot_see_robot_do
    (rsrd) python -m compas_rhino.install -p robot_see_robot_do -v 7.0

**Voilà! You can now go to VS Code, Rhino or Grasshopper to run the example files!**
