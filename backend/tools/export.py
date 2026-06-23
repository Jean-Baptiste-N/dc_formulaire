import docxtpl
import json

def main():
    with open('inputs/json_exemple.json' ) as json_file:
        json_data = json.load(json_file)

    template = docxtpl.DocxTemplate("template.docx")
    template.render(json_data)
    template.save("outputs/exemple.docx")

if __name__ == "__main__":
    main()

