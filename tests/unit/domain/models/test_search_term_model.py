"""
Testes unitários para SearchTermModel
"""
import unittest
import sys
import os

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.domain.models.search_term_model import SearchTermModel


class TestSearchTermModel(unittest.TestCase):
    """Testes para SearchTermModel"""
    
    def test_search_term_model_creation_basic(self):
        """Testa criação básica do modelo"""
        term = SearchTermModel(
            query="elevador manutenção São Paulo",
            location="SP",
            category="elevadores",
            pages=10
        )
        
        self.assertEqual(term.query, "elevador manutenção São Paulo")
        self.assertEqual(term.location, "SP")
        self.assertEqual(term.category, "elevadores")
        self.assertEqual(term.pages, 10)
    
    def test_search_term_model_creation_different_values(self):
        """Testa criação com valores diferentes"""
        term = SearchTermModel(
            query="escada rolante instalação Rio de Janeiro",
            location="RJ",
            category="escadas",
            pages=5
        )
        
        self.assertEqual(term.query, "escada rolante instalação Rio de Janeiro")
        self.assertEqual(term.location, "RJ")
        self.assertEqual(term.category, "escadas")
        self.assertEqual(term.pages, 5)
    
    def test_search_term_model_empty_strings(self):
        """Testa com strings vazias"""
        term = SearchTermModel(
            query="",
            location="",
            category="",
            pages=0
        )
        
        self.assertEqual(term.query, "")
        self.assertEqual(term.location, "")
        self.assertEqual(term.category, "")
        self.assertEqual(term.pages, 0)
    
    def test_search_term_model_long_query(self):
        """Testa com query longa"""
        long_query = "elevador manutenção modernização instalação conserto técnico empresa São Paulo capital zona norte sul leste oeste"
        
        term = SearchTermModel(
            query=long_query,
            location="SP",
            category="elevadores",
            pages=15
        )
        
        self.assertEqual(term.query, long_query)
        self.assertEqual(len(term.query), len(long_query))
    
    def test_search_term_model_special_characters_in_query(self):
        """Testa com caracteres especiais na query"""
        term = SearchTermModel(
            query="elevador & manutenção - São Paulo/SP (capital)",
            location="SP",
            category="elevadores & escadas",
            pages=8
        )
        
        self.assertEqual(term.query, "elevador & manutenção - São Paulo/SP (capital)")
        self.assertEqual(term.category, "elevadores & escadas")
    
    def test_search_term_model_unicode_characters(self):
        """Testa com caracteres unicode"""
        term = SearchTermModel(
            query="elevador manutenção São João",
            location="SP",
            category="elevadores",
            pages=12
        )
        
        self.assertEqual(term.query, "elevador manutenção São João")
        self.assertIn("ã", term.query)
    
    def test_search_term_model_different_locations(self):
        """Testa com diferentes localizações"""
        locations = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "GO"]
        
        for loc in locations:
            term = SearchTermModel(
                query=f"elevador {loc}",
                location=loc,
                category="elevadores",
                pages=10
            )
            self.assertEqual(term.location, loc)
    
    def test_search_term_model_different_categories(self):
        """Testa com diferentes categorias"""
        categories = ["elevadores", "escadas", "plataformas", "monta-cargas", "acessibilidade"]
        
        for cat in categories:
            term = SearchTermModel(
                query=f"busca {cat}",
                location="SP",
                category=cat,
                pages=5
            )
            self.assertEqual(term.category, cat)
    
    def test_search_term_model_different_pages(self):
        """Testa com diferentes números de páginas"""
        page_numbers = [1, 5, 10, 15, 20, 50, 100]
        
        for pages in page_numbers:
            term = SearchTermModel(
                query="teste",
                location="SP",
                category="teste",
                pages=pages
            )
            self.assertEqual(term.pages, pages)
            self.assertIsInstance(term.pages, int)
    
    def test_search_term_model_negative_pages(self):
        """Testa com número negativo de páginas"""
        term = SearchTermModel(
            query="teste",
            location="SP",
            category="teste",
            pages=-5
        )
        
        self.assertEqual(term.pages, -5)
    
    def test_search_term_model_zero_pages(self):
        """Testa com zero páginas"""
        term = SearchTermModel(
            query="teste",
            location="SP",
            category="teste",
            pages=0
        )
        
        self.assertEqual(term.pages, 0)
    
    def test_search_term_model_is_dataclass(self):
        """Testa se é uma dataclass"""
        import dataclasses
        self.assertTrue(dataclasses.is_dataclass(SearchTermModel))
    
    def test_search_term_model_fields_types(self):
        """Testa tipos dos campos"""
        import dataclasses
        fields = dataclasses.fields(SearchTermModel)
        
        field_types = {field.name: field.type for field in fields}
        
        self.assertEqual(field_types['query'], str)
        self.assertEqual(field_types['location'], str)
        self.assertEqual(field_types['category'], str)
        self.assertEqual(field_types['pages'], int)
    
    def test_search_term_model_equality(self):
        """Testa igualdade entre instâncias"""
        term1 = SearchTermModel(
            query="elevador teste",
            location="SP",
            category="elevadores",
            pages=10
        )
        
        term2 = SearchTermModel(
            query="elevador teste",
            location="SP",
            category="elevadores",
            pages=10
        )
        
        self.assertEqual(term1, term2)
    
    def test_search_term_model_inequality(self):
        """Testa desigualdade entre instâncias"""
        term1 = SearchTermModel(
            query="elevador teste1",
            location="SP",
            category="elevadores",
            pages=10
        )
        
        term2 = SearchTermModel(
            query="elevador teste2",
            location="RJ",
            category="escadas",
            pages=5
        )
        
        self.assertNotEqual(term1, term2)
    
    def test_search_term_model_inequality_by_query(self):
        """Testa desigualdade apenas por query"""
        term1 = SearchTermModel(
            query="elevador teste1",
            location="SP",
            category="elevadores",
            pages=10
        )
        
        term2 = SearchTermModel(
            query="elevador teste2",
            location="SP",
            category="elevadores",
            pages=10
        )
        
        self.assertNotEqual(term1, term2)
    
    def test_search_term_model_inequality_by_pages(self):
        """Testa desigualdade apenas por páginas"""
        term1 = SearchTermModel(
            query="elevador teste",
            location="SP",
            category="elevadores",
            pages=10
        )
        
        term2 = SearchTermModel(
            query="elevador teste",
            location="SP",
            category="elevadores",
            pages=5
        )
        
        self.assertNotEqual(term1, term2)
    
    def test_search_term_model_repr(self):
        """Testa representação string"""
        term = SearchTermModel(
            query="elevador repr teste",
            location="SP",
            category="elevadores",
            pages=7
        )
        
        repr_str = repr(term)
        self.assertIn("SearchTermModel", repr_str)
        self.assertIn("query='elevador repr teste'", repr_str)
        self.assertIn("location='SP'", repr_str)
        self.assertIn("category='elevadores'", repr_str)
        self.assertIn("pages=7", repr_str)
    
    def test_search_term_model_attribute_access(self):
        """Testa acesso aos atributos"""
        term = SearchTermModel(
            query="acesso teste",
            location="SP",
            category="elevadores",
            pages=10
        )
        
        # Testa leitura
        self.assertEqual(term.query, "acesso teste")
        self.assertEqual(term.location, "SP")
        self.assertEqual(term.category, "elevadores")
        self.assertEqual(term.pages, 10)
        
        # Testa escrita
        term.query = "nova query"
        term.location = "RJ"
        term.category = "escadas"
        term.pages = 15
        
        self.assertEqual(term.query, "nova query")
        self.assertEqual(term.location, "RJ")
        self.assertEqual(term.category, "escadas")
        self.assertEqual(term.pages, 15)
    
    def test_search_term_model_not_hashable(self):
        """Testa que dataclass não é hashable por padrão"""
        term = SearchTermModel(
            query="hash teste",
            location="SP",
            category="elevadores",
            pages=10
        )
        
        # Dataclass não é hashable por padrão
        with self.assertRaises(TypeError):
            hash(term)
    
    def test_search_term_model_cannot_be_dict_key(self):
        """Testa que não pode ser usado como chave de dicionário"""
        term = SearchTermModel(
            query="dict teste",
            location="SP",
            category="elevadores",
            pages=10
        )
        
        # Não pode ser usado como chave por não ser hashable
        with self.assertRaises(TypeError):
            test_dict = {term: "valor teste"}
    
    def test_search_term_model_copy(self):
        """Testa cópia do modelo"""
        import copy
        
        original = SearchTermModel(
            query="copy teste",
            location="SP",
            category="elevadores",
            pages=10
        )
        
        # Cópia rasa
        shallow_copy = copy.copy(original)
        self.assertEqual(original, shallow_copy)
        self.assertIsNot(original, shallow_copy)
        
        # Cópia profunda
        deep_copy = copy.deepcopy(original)
        self.assertEqual(original, deep_copy)
        self.assertIsNot(original, deep_copy)
    
    def test_search_term_model_immutable_behavior(self):
        """Testa comportamento de imutabilidade (se frozen=True)"""
        # Como não sabemos se a dataclass tem frozen=True, testamos se é mutável
        term = SearchTermModel(
            query="mutável teste",
            location="SP",
            category="elevadores",
            pages=10
        )
        
        # Tenta modificar (deve funcionar se não for frozen)
        try:
            term.query = "modificado"
            self.assertEqual(term.query, "modificado")
        except AttributeError:
            # Se for frozen, deve lançar AttributeError
            self.fail("Modelo parece ser frozen, mas deveria ser mutável")


if __name__ == '__main__':
    unittest.main()