"""
Testes unitários para CompanyModel
"""
import unittest
import sys
import os

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.domain.models.company_model import CompanyModel


class TestCompanyModel(unittest.TestCase):
    """Testes para CompanyModel"""

    def test_company_model_creation_with_required_fields(self):
        """Testa criação com campos obrigatórios"""
        company = CompanyModel(
            name="Empresa Teste",
            emails="test@example.com;",
            domain="example.com",
            url="https://example.com"
        )

        self.assertEqual(company.name, "Empresa Teste")
        self.assertEqual(company.emails, "test@example.com;")
        self.assertEqual(company.domain, "example.com")
        self.assertEqual(company.url, "https://example.com")
        self.assertEqual(company.search_term, "")
        self.assertEqual(company.address, "")
        self.assertEqual(company.phone, "")

    def test_company_model_creation_with_all_fields(self):
        """Testa criação com todos os campos"""
        company = CompanyModel(
            name="Empresa Completa",
            emails="admin@empresa.com;contato@empresa.com;",
            domain="empresa.com",
            url="https://empresa.com",
            search_term="elevador manutenção São Paulo",
            address="Rua Teste, 123 - São Paulo/SP",
            phone="(11) 99999-8888;(11) 3333-4444;"
        )

        self.assertEqual(company.name, "Empresa Completa")
        self.assertEqual(company.emails, "admin@empresa.com;contato@empresa.com;")
        self.assertEqual(company.domain, "empresa.com")
        self.assertEqual(company.url, "https://empresa.com")
        self.assertEqual(company.search_term, "elevador manutenção São Paulo")
        self.assertEqual(company.address, "Rua Teste, 123 - São Paulo/SP")
        self.assertEqual(company.phone, "(11) 99999-8888;(11) 3333-4444;")

    def test_company_model_default_values(self):
        """Testa valores padrão dos campos opcionais"""
        company = CompanyModel(
            name="Teste",
            emails="test@test.com;",
            domain="test.com",
            url="https://test.com"
        )

        self.assertEqual(company.search_term, "")
        self.assertEqual(company.address, "")
        self.assertEqual(company.phone, "")

    def test_company_model_empty_strings(self):
        """Testa com strings vazias"""
        company = CompanyModel(
            name="",
            emails="",
            domain="",
            url=""
        )

        self.assertEqual(company.name, "")
        self.assertEqual(company.emails, "")
        self.assertEqual(company.domain, "")
        self.assertEqual(company.url, "")

    def test_company_model_multiple_emails_format(self):
        """Testa formato com múltiplos e-mails"""
        company = CompanyModel(
            name="Multi Email",
            emails="email1@test.com;email2@test.com;email3@test.com;",
            domain="test.com",
            url="https://test.com"
        )

        self.assertEqual(company.emails, "email1@test.com;email2@test.com;email3@test.com;")
        self.assertTrue(company.emails.endswith(";"))
        self.assertEqual(len(company.emails.split(";")), 4)  # 3 emails + 1 vazio no final

    def test_company_model_multiple_phones_format(self):
        """Testa formato com múltiplos telefones"""
        company = CompanyModel(
            name="Multi Phone",
            emails="test@test.com;",
            domain="test.com",
            url="https://test.com",
            phone="(11) 99999-8888;(11) 3333-4444;(21) 98765-4321;"
        )

        self.assertEqual(company.phone, "(11) 99999-8888;(11) 3333-4444;(21) 98765-4321;")
        self.assertTrue(company.phone.endswith(";"))
        self.assertEqual(len(company.phone.split(";")), 4)  # 3 phones + 1 vazio no final

    def test_company_model_is_dataclass(self):
        """Testa se é uma dataclass"""
        import dataclasses
        self.assertTrue(dataclasses.is_dataclass(CompanyModel))

    def test_company_model_fields_types(self):
        """Testa tipos dos campos"""
        import dataclasses
        fields = dataclasses.fields(CompanyModel)

        field_types = {field.name: field.type for field in fields}

        self.assertEqual(field_types['name'], str)
        self.assertEqual(field_types['emails'], str)
        self.assertEqual(field_types['domain'], str)
        self.assertEqual(field_types['url'], str)
        self.assertEqual(field_types['search_term'], str)
        self.assertEqual(field_types['address'], str)
        self.assertEqual(field_types['phone'], str)

    def test_company_model_equality(self):
        """Testa igualdade entre instâncias"""
        company1 = CompanyModel(
            name="Teste",
            emails="test@test.com;",
            domain="test.com",
            url="https://test.com"
        )

        company2 = CompanyModel(
            name="Teste",
            emails="test@test.com;",
            domain="test.com",
            url="https://test.com"
        )

        self.assertEqual(company1, company2)

    def test_company_model_inequality(self):
        """Testa desigualdade entre instâncias"""
        company1 = CompanyModel(
            name="Teste1",
            emails="test1@test.com;",
            domain="test1.com",
            url="https://test1.com"
        )

        company2 = CompanyModel(
            name="Teste2",
            emails="test2@test.com;",
            domain="test2.com",
            url="https://test2.com"
        )

        self.assertNotEqual(company1, company2)

    def test_company_model_repr(self):
        """Testa representação string"""
        company = CompanyModel(
            name="Teste Repr",
            emails="test@test.com;",
            domain="test.com",
            url="https://test.com"
        )

        repr_str = repr(company)
        self.assertIn("CompanyModel", repr_str)
        self.assertIn("name='Teste Repr'", repr_str)
        self.assertIn("emails='test@test.com;'", repr_str)
        self.assertIn("domain='test.com'", repr_str)
        self.assertIn("url='https://test.com'", repr_str)

    def test_company_model_attribute_access(self):
        """Testa acesso aos atributos"""
        company = CompanyModel(
            name="Acesso Teste",
            emails="acesso@test.com;",
            domain="acesso.com",
            url="https://acesso.com",
            search_term="termo teste",
            address="Endereço teste",
            phone="(11) 1234-5678;"
        )

        # Testa leitura
        self.assertEqual(company.name, "Acesso Teste")
        self.assertEqual(company.emails, "acesso@test.com;")
        self.assertEqual(company.domain, "acesso.com")
        self.assertEqual(company.url, "https://acesso.com")
        self.assertEqual(company.search_term, "termo teste")
        self.assertEqual(company.address, "Endereço teste")
        self.assertEqual(company.phone, "(11) 1234-5678;")

        # Testa escrita
        company.name = "Nome Alterado"
        company.emails = "novo@test.com;"
        company.domain = "novo.com"
        company.url = "https://novo.com"
        company.search_term = "novo termo"
        company.address = "Novo endereço"
        company.phone = "(11) 9876-5432;"

        self.assertEqual(company.name, "Nome Alterado")
        self.assertEqual(company.emails, "novo@test.com;")
        self.assertEqual(company.domain, "novo.com")
        self.assertEqual(company.url, "https://novo.com")
        self.assertEqual(company.search_term, "novo termo")
        self.assertEqual(company.address, "Novo endereço")
        self.assertEqual(company.phone, "(11) 9876-5432;")

    def test_company_model_special_characters(self):
        """Testa com caracteres especiais"""
        company = CompanyModel(
            name="Empresa & Cia Ltda.",
            emails="contato@empresa-cia.com.br;",
            domain="empresa-cia.com.br",
            url="https://www.empresa-cia.com.br/contato",
            search_term="elevador & manutenção São Paulo - SP",
            address="Rua José da Silva, 123 - 1º Andar - São Paulo/SP - CEP: 01234-567",
            phone="(11) 99999-8888;"
        )

        self.assertEqual(company.name, "Empresa & Cia Ltda.")
        self.assertEqual(company.emails, "contato@empresa-cia.com.br;")
        self.assertEqual(company.domain, "empresa-cia.com.br")
        self.assertEqual(company.url, "https://www.empresa-cia.com.br/contato")
        self.assertEqual(company.search_term, "elevador & manutenção São Paulo - SP")
        self.assertEqual(company.address, "Rua José da Silva, 123 - 1º Andar - São Paulo/SP - CEP: 01234-567")
        self.assertEqual(company.phone, "(11) 99999-8888;")

    def test_company_model_unicode_characters(self):
        """Testa com caracteres unicode"""
        company = CompanyModel(
            name="Elevadores São João",
            emails="contato@elevadores-sj.com.br;",
            domain="elevadores-sj.com.br",
            url="https://elevadores-sj.com.br",
            search_term="elevador manutenção São João",
            address="Avenida Paulista, 1000 - São Paulo",
            phone="(11) 3333-4444;"
        )

        self.assertEqual(company.name, "Elevadores São João")
        self.assertEqual(company.search_term, "elevador manutenção São João")
        self.assertEqual(company.address, "Avenida Paulista, 1000 - São Paulo")

    def test_company_model_long_strings(self):
        """Testa com strings longas"""
        long_name = "A" * 1000
        long_emails = ";".join([f"email{i}@test.com" for i in range(50)]) + ";"
        long_url = "https://example.com/" + "path/" * 100

        company = CompanyModel(
            name=long_name,
            emails=long_emails,
            domain="example.com",
            url=long_url
        )

        self.assertEqual(len(company.name), 1000)
        self.assertTrue(len(company.emails) > 500)
        self.assertTrue(len(company.url) > 500)


if __name__ == '__main__':
    unittest.main()
