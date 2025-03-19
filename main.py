"""Main module"""

import os
from getpass import getpass
from core.generate_labels import generate_nfe_labels
from core.print_labels import print_labels
from core.scraping import CargaMaquinaClient


def main() -> None:
    """Main function"""

    if not os.path.exists("./tmp"):
        os.mkdir("./tmp")
    username: str = input("Usuário: ")
    password: str = getpass(prompt="Senha: ")
    client = CargaMaquinaClient(username=username, password=password)
    while True:
        negociation_id: str = input("ID da Negociação: ")
        if negociation_id == "q":
            client.close()
            break
        client.nfe_data_scraping(negociation_id)
        generate_nfe_labels()
        print_labels(["./tmp/pending_labels.pdf", "./tmp/stock_labels.pdf"])

if __name__ == "__main__":
    main()
