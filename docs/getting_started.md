---
layout: page
title: Getting Started
---

# Requirements

* Windows 10 Professional
* Rhino 7 / Grasshopper
* [Anaconda Python](https://www.anaconda.com/distribution/?gclid=CjwKCAjwo9rtBRAdEiwA_WXcFoyH8v3m-gVC55J6YzR0HpgB8R-PwM-FClIIR1bIPYZXsBtbPRfJ8xoC6HsQAvD_BwE)
* [Visual Studio Code](https://code.visualstudio.com/)
* [Github Desktop](https://desktop.github.com/)

# Dependencies

* [COMPAS](https://compas-dev.github.io/)
* [COMPAS FAB](https://gramaziokohler.github.io/compas_fab/latest/)
* [Assembly Information Model](https://github.com/augmentedfabricationlab/assembly_information_model)
* [UR Fabrication Control](https://github.com/augmentedfabricationlab/ur_fabrication_control)

### 1. Setting up the Anaconda environment with COMPAS

Execute the commands below in Anaconda Prompt:
	
    (base) conda config --add channels conda-forge

#### Windows
    (base) conda create -n learn python=3.8 compas_fab=0.17 --yes
    (base) conda activate learn

#### Mac
    (base) conda create -n learn python=3.8 compas_fab=0.17 python.app --yes
    (base) conda activate learn
    

#### Verify Installation

    (learn) pip show compas_fab
####
    Name: compas-fab
    Version: 0.13.1
    Summary: Robotic fabrication package for the COMPAS Framework
    ...

#### Install on Rhino

    (learn) python -m compas_rhino.install

NOTE: This installs to Rhino 6.0, use `-v 5.0` if needed.


### 2. Installation of Dependencies

    (learn) conda install git

#### Assembly Information Model
    
    (learn) python -m pip install git+https://github.com/augmentedfabricationlab/assembly_information_model@master#egg=assembly_information_model
    (learn) python -m compas_rhino.install -p assembly_information_model

#### UR Fabrication Control
    
    (learn) python -m pip install git+https://github.com/augmentedfabricationlab/ur_fabrication_control@master#egg=ur_fabrication_control
    (learn) python -m compas_rhino.install -p ur_fabrication_control


### 3. Cloning the Course Repository

Create a workspace directory:

C:\Users\YOUR_USERNAME\workspace

Then open Github Desktop and clone the following repository into you workspace folder:

* [Robot See Robot Do repository](https://github.com/augmentedfabricationlab/robot_see_robot_do)

**Voilà! You can now go to VS Code, Rhino or Grasshopper to run the example files!**
