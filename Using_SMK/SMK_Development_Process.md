## Steps in installing and using SMK (Simple Map Kit)

Simple Mapkit allows users to create straight forward web mapping applications. These applications can then be modified and prepared for web deployment in a variety of methods. For the following example it will explain how to set up a SMK project within windows system for Linux (WSL) and deploy to GitHub pages as a stand alone web map.


The process will go through the following steps

1. Setting up Windows system for linux to be able to use Simple Map Kit (SMK)
2. Install Simple MapKit on Linux (WSL)
3. Create folders in Linux and then create an SMK project
4. Setting up and Editing your SMK project
5. Set up a GitHub repo which to transfer your SMK project and deploy application on Github pages.

## Windows System for Linux
1. Install Windows system for linux to use on windows.
- Start by reading the [WSL install on windows](<https://learn.microsoft.com/en-us/windows/wsl/install>)
- At the bottom of your file explorer you will see Linux and numerous folders within Linux
- Under the home folder you can add additional folders to your liking. It is reccomened to make a SMK_Creations folder where you will make new applications and a Github folder whre you can manage Github folders that are cloned from github.


## Install Simple Map kit (SMK) on WSL
Install SMK onto WSL
[Website] https://github.com/bcgov/smk-cli
- The website provides steps regarding installation
- You may need to experiment in WSL to install additional libraries SMK uses like Node.


## Creating a simple mapkit project
- For this exercise you can create a folder inside WSL folders under the (home) directory called "SMK_Creations"
SMK_Creations_folder
![SMK_Creations_folder](../Gif/Create_SMK_Example.gif)
- In wsl change the directory to SMK_Creations. e.g. cd SMK_Creations
- Enter 'smk create'. It will ask a number of questions about the initial set up of the application. Most are straight forward.
![Create_SMK_Example](../Gif/Create_SMK_Example.gif)
- When asked to enter a package name of @bcgov/smk, enter as the stated example. This will create a folder within Node_modules\@bcgov that will contain key application files


## Set up GitHub area in WSL to put code.
- Create a /github/(IdirName)/GitHub location which

## Make sure Visual Studio Code is installed on your computer
[Website] https://code.visualstudio.com/
- To connect VS Code to WSL. Open VS Code and Install WSL extension

## Creating a GitHub repo to use Git Hub pages
- Create a Github pages from a simple map kit you will need to create a new repo under the bcgov organization. Do not make the repo under your own Github account.
- When the Repo is created it can be cloned to the WSL github area in preperation to recive items created in Simple map kit.

## How to start working within the bcgov gis-pantry? 
1. Review the content in the GIS Pantry [_start-here](../_start-here) folder.
- Start by reading the [GIS_Pantry_QuickStart Doc](<QuickStart - BEGIN HERE.md>)
GeoBC Implementation Team repository for work we do.
