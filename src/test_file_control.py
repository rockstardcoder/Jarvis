from jarvis.services.file_control import FileControl


def main():
    file_control = FileControl()

    print("=" * 50)
    print("Jarvis File Control Test")
    print("=" * 50)

    print(file_control.refresh_folder_index())
    print()
    print(file_control.find_folder("jarvis"))


if __name__ == "__main__":
    main()