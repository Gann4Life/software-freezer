class SelectableOption:
    def __init__(self, title, callback):
        self.title = title
        self.callback = callback

    def call(self):
        """Runs the stored function of the option"""
        self.callback()

class OptionSelector:
    def __init__(self, title, options: list):
        self.title = title
        self.options = options

    def addOption(self, option: SelectableOption):
        self.options.append(option)

    def requestInput(self, message):
        while True:
            try:
                result = int(input(message))
            except ValueError:
                print("Please, enter a valid number.")
                continue
            else:
                break

        return result

    def displayOptions(self):
        for k, v in enumerate(self.options):
            print(f"[{k}] {v.title}")

    def displayTitle(self):
        print("=" * 5 + f" {self.title} " + "=" * 5)

    def displayMenu(self):
        self.displayTitle()
        self.displayOptions()

    def askForAnOption(self, message):
        self.displayMenu()
        userInput = self.requestInput(message)
        self.options[userInput].call()