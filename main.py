"""Main module"""

from getpass import getpass
from scraping import CargaMaquinaClient
from generate_labels import generate_nfe_labels
from print_labels import print_labels


def main() -> None:
    """Main function"""
    username: str = input("Usuário: ")
    password: str = getpass(prompt="Senha: ")
    negociation_id: str = input("ID da Negociação: ")
    client = CargaMaquinaClient(username=username, password=password)
    client.nfe_data_scraping(negociation_id)
    generate_nfe_labels()
    print_labels(["./pending_labels.pdf", "./stock_labels.pdf"])


if __name__ == "__main__":
    main()
