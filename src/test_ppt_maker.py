from jarvis.services.ppt_maker import PPTMaker


def main():
    ppt_maker = PPTMaker()

    print("=" * 50)
    print("Jarvis PPT Maker Test")
    print("=" * 50)

    print(
        ppt_maker.create_presentation(
            topic="Artificial Intelligence in Education",
            style="professional"
        )
    )

    print(
        ppt_maker.open_presentation_folder()
    )


if __name__ == "__main__":
    main()