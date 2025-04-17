

def welcome_screen():
    print(
        "****************************************************************\n"
        "|                       SAFE DATA EXPLORER                      |\n"
        "****************************************************************\n"
        "|              Bc. Vilem Pechacek & Bc. Radim Macho             |\n"
        "|                         VUT BRNO 2025                         |\n"
        "----------------------------------------------------------------\n"
        "\nWelcome to our project! Type any key to login or type 'exit' to quit.\n"
    )

def show_menu():
    print("\nAvailable Commands:")
    print("-" * 40)
    print(" touch      Create File")
    print(" edit       Edit File")
    print(" rmf        Delete File")
    print(" mkdir      Create Directory")
    print(" rmd        Delete Directory")
    print(" rename     Rename File/Directory")
    print(" down       Download File")
    print(" up         Upload File")
    print(" ls         List Directory Contents")
    print(" read       Read File Content")
    print(" cd         Change Directory")
    print(" exit       Quit Application")
    print(" help       Show This Help Menu")
    print("-" * 40)
