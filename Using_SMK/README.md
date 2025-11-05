## Steps in installing and using SMK (Simple Map Kit)

Simple Mapkit allows users to create straight forward web mapping applications. These applications can then be modified and prepared for web deployment in a variety of methods. For the following example it will explain how to set up a SMK project within windows system for Linux (WSL) and deploy to GitHub pages as a stand alone web map.

## Please note. This method is not a secure website method. So not senitive government or project data should be shown on GitHub pages


The process will go through the following steps

1. Setting up Windows system for linux to be able to use Simple Map Kit (SMK)
2. Install Simple MapKit on Linux (WSL)
3. Create folders in Linux and then create an SMK project
4. Setting up and Editing your SMK project
5. Set up a GitHub repo which to transfer your SMK project and deploy application on Github pages.

## Windows System for Linux
- Install Windows system for linux to use on windows.
- Start by reading the [WSL install on windows](<https://learn.microsoft.com/en-us/windows/wsl/install>)
- When installed and started you will see bottom of your file explorer Linux and numerous folders within Linux
- Under the home folder you can add additional folders to meet your needs. It is reccomened to make a SMK_Creations folder where you will make new applications and a Github folder whre you can manage Github folders that are cloned from GitHub.


## Install Simple Map kit (SMK) on WSL
Install SMK onto WSL
[Website] https://github.com/bcgov/smk-cli
- The website provides steps regarding installation
- You may need to experiment in WSL to install additional libraries SMK uses like Node.


## Creating a simple mapkit project
- For this exercise you can create a folder inside WSL folders under the (home) directory called "SMK_Creations"
![SMK_Creations_folder](./Gif/SMK_Creations_folder.png)

- In WSL change the directory to SMK_Creations. e.g. cd SMK_Creations
- Enter 'smk create'. It will ask a number of questions about the initial set up of the application. Most are straight forward. See example below.
- When asked to enter a package name of @bcgov/smk, enter as the stated example. This will create a folder within Node_modules/@bcgov that will contain key web map application files
- When it asks to open the application select yes.
![Create_SMK_Example](./Gif/Create_SMK_Example.gif)

- Now that you have a sample Simple Map Kit project created there are a number of editing functions that can be used to add data and modify their properties.

### SMK Main editor screen. 
- Select leaflet as map viewer
![SMK_main_edit_screen](./Gif/SMK_main_edit_screen.png)


### SMK add Data BC Layers
- DataBC layers can be added to the application. Each layer added has a pencil which can edit its properties. Properties include.
- Details. Min/Max Scale visibility, Opacity and name
- Attributes. Which ones to display, which one to use as a title and the geometry attribute
- Queries. Apply a query to the data to limit data visible
- Template formatting
![SMK_dataBC_layers](./Gif/SMK_dataBC_layers.png)

### SMK add WMS Layers
- Add WMS Layers
- These have less editing properties do to being a WMS file.
![SMK_WMS_layers](./Gif/SMK_WMS_layers.png)

### SMK add other data
- Import unique vector layers of various formats
- Unique data to your project can be added to the SMK project
- Data types include GeoJSON, KML, Shapefile, CSV
![SMK_import vector_layers](./Gif/SMK_import_vector_layers.png)

### SMK add URL data sources
- Add vector data from URL layers
- GIS data from URL links can be aded to an application
![SMK_add_vector_URL_layers](./Gif/SMK_add_vector_URL_layers.png)

### SMK add tools available to the application
- Select available tools to add to the location and modify settings through the editing pencil
- Tools have properties to control look and function
![SMK_Tools](./Gif/SMK_Tools.png)

## Make sure Visual Studio Code is installed on your computer
[Website] https://code.visualstudio.com/
- To connect VS Code to WSL. Open VS Code and Install WSL extension.
- When you have WSL open VSCode can connect to project folders within WSL folders. WSL needs to be open to access.

## Creating a GitHub repo to use GitHub pages under the bcgov organization
- Create a Github pages for a simple map kit application you will need to create a new GitHub repo under the bcgov organization. Do not make the repo under your own Github account.
- When the empty Repo is created it can be cloned to the WSL github area in preperation to receive items created in Simple map kit.
[Website] https://learn.microsoft.com/en-us/azure/developer/javascript/how-to/with-visual-studio-code/clone-github-repository?tabs=activity-bar

## Set up GitHub area in WSL to put code.
- Clone your new empty repo into a WSL folder. Example /github/(your project name created in GitHub)
- When you SMK application is ready and complete you can copy it into the created Github folder cloned from GitHub. Once in the GitHub folder you will make some edits to the created application for it to work in GitHub pages.

## Copying and Modifying SMK project to work in GitHub pages.
- Take your SMK project that you created and copy the project to the GitHub repo folder. Only include the following files and folders
- The HTML file, JSON files and javascript files in the main SMK folder.
- The whole assets and layers folders.
- Inside the node_modules folder take the project folder you made during SMK creation e.g. @bcgov. Inside there is a smk folder. Copy this smk folder into the assets folder previously copied across.
- To fix a little bug rename the _base folder to base. e.g. \smk\dist\assets\src\theme\base

- in the smk.js file (\assets\smk\dist) modify the javascript code from /_base to /base
_____________________________________________
Example:
    include.tag ("theme-base",
        { loader: "group", tags: [
            { loader: "style", url: "theme/base/command.css" },
            { loader: "style", url: "theme/base/elastic.css" },
            { loader: "style", url: "theme/base/map-frame.css" },
            { loader: "style", url: "theme/base/resets.css" },
            { loader: "style", url: "theme/base/variables.css" },
            "material-icons"
        ] }
_____________________________________________

- Modify the source index.html to reference the location of the javascript files and css files copied across.
_____________________________________________
Example:
<!DOCTYPE html>
<html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Testing SMK</title>
        <link rel="stylesheet" type="text/css" href="./assets/style.css"/>
    </head>

    <body>
        <header>Testing SMK</header>

        <article>
            <div id="smk-map-frame"></div>
        </article>

        <footer>Application constructed by smk-cli at 2025-08-21T22:09:39.688Z</footer>

        <script src="./assets/smk/dist/smk.js"></script>
        <script src="./smk-init.js"></script>
    </body>
</html>
_____________________________________________

## Push SMK project and edits back up to GitHub repo and make a website.
- When the SMK project has been edited in the GitHub repo it can be pushed up into GitHub to populate with the SMK project data and folders.
- In GitHub under settings set up pages to deploy the application to a URL
![GitHub_pages](./Gif/GitHub_pages.png)

- A sample GitHub pages can be found here. https://github.com/GrahamMacGregorBCGov/SMK_test.github.io
- The associate web page for is is as follows. https://grahammacgregorbcgov.github.io/SMK_test.github.io/
