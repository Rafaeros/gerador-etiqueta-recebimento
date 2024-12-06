"""Main module"""

import os
from getpass import getpass
from scraping import CargaMaquinaClient
from generate_labels import generate_nfe_labels
from print_labels import print_labels


def main() -> None:
    """Main function"""

    if not os.path.exists("./tmp"):
        os.mkdir("./tmp")

    username: str = input("Usuário: ")
    password: str = getpass(prompt="Senha: ")
    negociation_id: str = input("ID da Negociação: ")
    qr_code: str = input("Gerar QR Code? (S/N): ").lower() == "s"
    client = CargaMaquinaClient(username=username, password=password)
    client.nfe_data_scraping(negociation_id)
    generate_nfe_labels(qr_code)
    print_labels(["./tmp/pending_labels.pdf", "./tmp/stock_labels.pdf"])


if __name__ == "__main__":
    main()
