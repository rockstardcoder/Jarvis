from jarvis.services.document_maker import DocumentMaker


def main():
    document_maker = DocumentMaker()

    print("=" * 50)
    print("Jarvis Document Maker Test")
    print("=" * 50)

    print(
        document_maker.create_document(
            topic="Artificial Intelligence in Education",
            doc_type="professional"
        )
    )

    print(
        document_maker.create_document(
            topic="Water Conservation",
            doc_type="school"
        )
    )

    print(
        document_maker.open_document_folder()
    )


if __name__ == "__main__":
    main()