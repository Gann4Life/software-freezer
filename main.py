import wget
import os
import shutil
import json

# Dialog modules
from tkinter.filedialog import askdirectory
from tkinter.messagebox import askyesno
from tkinter.simpledialog import askstring

# Custom modules
from optionMaker import SelectableOption, OptionSelector

class UserPaths:
    DOWNLOADS_CONFIG_FILE = "downloads.json"

    def __init__(self):
        self.userPath = os.path.expanduser("~")
        self.defaultDownloadsPath = os.path.join(self.userPath, 'Downloads')
        self.downloadsPath = self.defaultDownloadsPath

    def setDownloadsPath(self, programManager) -> None:
        # Changes the downloads path, moving all previously downloaded files to the new path.
        self.downloadsPath = os.path.normpath(askdirectory(initialdir=self.defaultDownloadsPath))
        for program in programManager.programList.programs:
            program.move(self.downloadsPath)
        if not askyesno(title="Confirmation", message=f"Your files will be downloaded at '{self.downloadsPath}', is that okay?"):
            self.setDownloadsPath(programManager)

    def configurationFileExists(self):
        return os.path.exists(os.path.join(self.downloadsPath, UserPaths.DOWNLOADS_CONFIG_FILE))

class Program:
    def __init__(self, url, downloadPath, name = "No name", description = "No description"):
        self.status = Status.PENDING
        self.url = url
        self.downloadPath = downloadPath
        self.name = name
        self.description = description
        self.executablePath = None
        self.filename = "NotDownloaded.txt"

    def isDownloaded(self):
        try:
            return os.path.exists(self.executablePath)
        except:
            return False

    def download(self) -> None:
        """Downloads the file to the assigned downloads folder."""
        if self.isDownloaded():
            print(f"[INFO] {self.name} is already downloaded.")
            return

        print(f"Downloading {self.url}...")

        try:
            self.setStatus(Status.IN_PROGRESS)
            self.executablePath = os.path.normpath(wget.download(url=self.url, out=self.downloadPath))
            self.filename = os.path.basename(self.executablePath)
            print(f"[INFO] Downloaded at {self.executablePath}")
            self.setStatus(Status.DOWNLOADED)
        except Exception as e:
            print(f"[ERROR] {e}")
            self.setStatus(Status.ERROR)

    def execute(self):
        os.startfile(self.executablePath)

    def delete(self) -> None:
        """Deletes the file that has been downloaded."""
        os.remove(self.executablePath)
        self.executablePath = None
        self.setStatus(Status.REMOVED)

    def move(self, newDirectory):
        print(f"[{self.name}] Moving to '{newDirectory}'")
        shutil.move(self.executablePath, newDirectory)
        previousDirectory = self.downloadPath
        self.downloadPath = newDirectory
        self.executablePath = os.path.join(self.downloadPath, self.filename)
        shutil.rmtree(previousDirectory)

    def setStatus(self, newStatus):
        print(f"[{self.name}] Status changed: {newStatus}")
        self.status = newStatus

    def displayInfo(self):
        print(f"[Name]: {self.name}\n[Description]: {self.description}\n[URL]: {self.url}\n[Folder]: {self.downloadPath}\n[Executable]: {self.executablePath}\n[Filename]: {self.filename()}")

    def displayMenu(self, manager, previousMenu):
        ProgramMenu(self, manager, previousMenu)

    # def toJson(self):
    #     return jsonpickle.encode(self)

    # def toJson(self):
    #     return json.dumps(self, default=lambda o: o.__dict__)

    @staticmethod
    def fromJson(jsonData):
        instance = Program(None, None)
        for key in jsonData:
            value = jsonData[key]
            setattr(instance, key, value)
        return instance

class Status:
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DOWNLOADED = "DOWNLOADED"
    REMOVED = "REMOVED"
    ERROR = "ERROR"

    def __init__(self):
        self.value = Status.PENDING

    def equals(self, status):
        return self.value == status

class ProgramList:
    def __init__(self, programs = []):
        self.programs = programs

    def addPrograms(self, *programs: Program) -> None:
        for program in programs:
            self.programs.append(program)

    def removeProgram(self, program):
        program.delete()
        self.programs.remove(program)

    def downloadAll(self):
        for program in self.programs:
            program.download()

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

    def loadJSON(self, path):
        data = json.loads(open(os.path.join(path, UserPaths.DOWNLOADS_CONFIG_FILE), "r+").read())
        self.programs = []
        for programData in data["programs"]:
            program = Program.fromJson(programData)
            self.programs.append(program)
            print(f"[{program.name}] Loaded.")

class ProgramManager:

    def __init__(self, pathsManager: UserPaths):
        self.pathsManager = pathsManager
        self.programList = ProgramList()

    def addProgram(self, *programs: Program) -> None:
        self.programList.addPrograms(*programs)

    def downloadAll(self):
        self.programList.downloadAll()
        self.openDownloadsPath()
        print("[INFO] All your downloads have been finished.")

    def openDownloadsPath(self) -> None:
        os.startfile(self.pathsManager.downloadsPath)

    def removeProgram(self, program):
        self.programList.removeProgram(program)

    def findProgramByName(self, name: str) -> Program:
        raise NotImplementedError("This function has not been made yet.")

    def findProgramByStatus(self, status: Status) -> Program:
        raise NotImplementedError("This function has not been made yet.")

    def findProgramByURL(self, url: str) -> Program:
        for program in self.programList.programs:
            if program.url == url: return program

    def showAllPrograms(self):
        for program in self.programList.programs:
            program.displayInfo()

    def exportJSON(self):
        print("[JSON] Saving data... ", end="")

        configFile = os.path.join(self.pathsManager.downloadsPath, UserPaths.DOWNLOADS_CONFIG_FILE)
        with open(configFile, "w+") as f:
            f.write(self.programList.toJson())

        print("done.")

    def loadJSON(self):
        print("[LOADING] Obtaining JSON data... ")
        self.programList.loadJSON(self.pathsManager.downloadsPath)

class ProgramMenu:
    def __init__(self, program: Program, manager: ProgramManager, previousMenu):
        self.program = program
        self.manager = manager
        self.previousMenu = previousMenu
        self.menu()

    def menu(self):
        OptionSelector(f"Options for {self.program.name}", [
            SelectableOption("Back", lambda: self.previousMenu()),
            SelectableOption("Execute", lambda: self.program.execute()) if self.program.isDownloaded() else SelectableOption("Download file", lambda: self.program.download()),
            SelectableOption("View data", lambda: self.view()),
            SelectableOption("Update data", lambda: self.updateMenu()),
            SelectableOption("Remove data", lambda: self.manager.removeProgram(self.program)),
            SelectableOption("Delete file", lambda: self.program.delete())
        ]).askForAnOption("Choose an option: ")

    def view(self):
        self.program.displayInfo()
        self.menu()

    # def execute(self):
    #     self.program.execute()

    # def remove(self):
    #     self.manager.removeProgram(self.program)

    # def deleteFile(self):
    #     self.program.delete()

    # def download(self):
    #     self.program.download()

    def updateMenu(self):
        def updateProgramName(program): program.name = askstring(program.name, prompt=f"{program.name}'s new name")
        def updateProgramDescription(program): program.description = askstring(program.name, prompt=f"{program.name}'s new description")
        def updateProgramURL(program): program.url = askstring(program.name, prompt=f"{program.name}'s new URL")

        options = OptionSelector(f"Update {self.program}'s data", [
            SelectableOption("Back", lambda: self.menu()),
            SelectableOption("Modify name", lambda: updateProgramName(self.program)),
            SelectableOption("Modify description", lambda: updateProgramDescription(self.program)),
            SelectableOption("Modify URL", lambda: updateProgramURL(self.program)),
        ])
        options.askForAnOption("Option: ")
        self.menu()


class Application:
    def __init__(self):
        self.pathsManager = UserPaths()
        self.programManager = ProgramManager(self.pathsManager)


        changePath = askyesno(title="Confirmation", message=f"Your files will be downloaded at '{self.pathsManager.downloadsPath}', would you like to change it?")
        if changePath:
            self.pathsManager.setDownloadsPath(self.programManager)

        if self.pathsManager.configurationFileExists():
            self.loadJsonData()

        self.mainMenuOptions = OptionSelector("Main menu",[
            SelectableOption("Set downloads folder", lambda: self.setDownloadsPathMenuAction()),
            SelectableOption("Download everything", lambda: self.downloadAllMenuAction()),
            SelectableOption("Open downloads folder", lambda: self.programManager.openDownloadsPath()),
            SelectableOption("Browse programs", lambda: self.selectProgramMenu()),
            SelectableOption("Add program", lambda: self.addProgramMenu()),
        ])
        self.mainMenu()

    def mainMenu(self):
        self.saveJsonData()
        self.mainMenuOptions.askForAnOption("What would you like to do? ")

    def setDownloadsPathMenuAction(self):
        self.pathsManager.setDownloadsPath(self.programManager)
        self.mainMenu()

    def downloadAllMenuAction(self):
        self.programManager.downloadAll()
        self.mainMenu()

    def selectProgramMenu(self):
        programMenu = lambda program: ProgramMenu(program, self.programManager, self.selectProgramMenu)
        optionList = [SelectableOption(program.name, lambda: programMenu(program)) for program in self.programManager.programList.programs]
        optionList.append(SelectableOption("Back", lambda: self.mainMenu()))
        OptionSelector("Program selection menu", optionList).askForAnOption("Enter an option: ")
        self.mainMenu()

    def addProgramMenu(self):

        programName = askstring(title="Create program", prompt="Program name")
        programURL = askstring(title=f"{programName} information", prompt=f"{programName}'s URL")

        program = Program(url=programURL,
                          downloadPath=self.pathsManager.downloadsPath,
                          name=programName,
                          )

        self.programManager.addProgram(program)
        program.displayMenu(self.programManager, self.mainMenu)

    def saveJsonData(self):
        self.programManager.exportJSON()

    def loadJsonData(self):
        self.programManager.loadJSON()

# userPaths = UserPaths()
# manager = ProgramManager(userPaths)
# manager.addProgram(
#     Program("https://drive.google.com/u/0/uc?id=1eTUwkMKjxVWHO2nSW_GruvyHj_djyG6-&export=download&confirm=t&uuid=5f63063b-dfc1-45b2-a0ce-b4ccf7c797c1&at=ACjLJWkm7GSBT85WFxQJSBbfOwd3:1674254491390"),
# )
# manager.downloadAll()

app = Application()