"""
Testes unitários para RetryManager
"""
import unittest
import time
from unittest.mock import patch

from src.infrastructure.network.retry_manager import RetryManager
from src.domain.models.retry_config_model import RetryConfigModel


class TestRetryManager(unittest.TestCase):
    """Testes para RetryManager"""
    
    def test_retry_success_first_attempt(self):
        """Testa sucesso na primeira tentativa"""
        @RetryManager.with_retry(max_attempts=3)
        def successful_function():
            return "success"
        
        result = successful_function()
        self.assertEqual(result, "success")
    
    def test_retry_success_after_failures(self):
        """Testa sucesso após falhas"""
        call_count = 0
        
        @RetryManager.with_retry(max_attempts=3, base_delay=0.1)
        def function_with_retries():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = function_with_retries()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)
    
    def test_retry_max_attempts_exceeded(self):
        """Testa quando máximo de tentativas é excedido"""
        @RetryManager.with_retry(max_attempts=2, base_delay=0.1)
        def always_failing_function():
            raise ValueError("Always fails")
        
        with self.assertRaises(ValueError):
            always_failing_function()
    
    def test_retry_with_specific_exceptions(self):
        """Testa retry apenas para exceções específicas"""
        @RetryManager.with_retry(max_attempts=3, base_delay=0.1, exceptions=(ValueError,))
        def function_with_specific_exception():
            raise TypeError("Not retryable")
        
        with self.assertRaises(TypeError):
            function_with_specific_exception()
    
    def test_retry_backoff_calculation(self):
        """Testa cálculo do backoff exponencial"""
        call_times = []
        
        @RetryManager.with_retry(max_attempts=3, base_delay=0.1, backoff_factor=2.0)
        def function_tracking_time():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise Exception("Retry needed")
            return "success"
        
        function_tracking_time()
        
        # Verifica que houve delay entre as chamadas
        self.assertEqual(len(call_times), 3)
        self.assertGreater(call_times[1] - call_times[0], 0.1)
        self.assertGreater(call_times[2] - call_times[1], 0.2)
    
    def test_retry_max_delay_limit(self):
        """Testa limite máximo de delay"""
        @RetryManager.with_retry(max_attempts=3, base_delay=10.0, max_delay=0.2)
        def function_with_max_delay():
            raise Exception("Test")
        
        start_time = time.time()
        try:
            function_with_max_delay()
        except:
            pass
        
        # Não deve demorar mais que alguns segundos devido ao max_delay
        elapsed = time.time() - start_time
        self.assertLess(elapsed, 2.0)
    
    def test_retry_from_config(self):
        """Testa criação de retry a partir de configuração"""
        config = RetryConfigModel(max_attempts=2, base_delay=0.1)
        
        @RetryManager.from_config(config)
        def function_with_config():
            raise Exception("Test")
        
        with self.assertRaises(Exception):
            function_with_config()
    
    def test_retry_preserves_function_metadata(self):
        """Testa que metadados da função são preservados"""
        @RetryManager.with_retry()
        def documented_function():
            """This is a test function"""
            return "test"
        
        self.assertEqual(documented_function.__name__, "documented_function")
        self.assertEqual(documented_function.__doc__, "This is a test function")
    
    def test_retry_with_arguments(self):
        """Testa retry com argumentos da função"""
        @RetryManager.with_retry(max_attempts=2, base_delay=0.1)
        def function_with_args(x, y, z=None):
            if x < 2:
                raise ValueError("x too small")
            return x + y + (z or 0)
        
        result = function_with_args(5, 3, z=2)
        self.assertEqual(result, 10)
    
    def test_retry_no_exception_on_last_attempt(self):
        """Testa que exceção é propagada na última tentativa"""
        attempt_count = 0
        
        @RetryManager.with_retry(max_attempts=2, base_delay=0.1)
        def function_counting_attempts():
            nonlocal attempt_count
            attempt_count += 1
            raise RuntimeError(f"Attempt {attempt_count}")
        
        with self.assertRaisesRegex(RuntimeError, "Attempt 2"):
            function_counting_attempts()
    
    def test_retry_return_none_edge_case(self):
        """Testa caso extremo onde last_exception existe mas não é lançada"""
        call_count = 0
        
        @RetryManager.with_retry(max_attempts=1, base_delay=0.1)
        def function_no_exception():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = function_no_exception()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 1)


if __name__ == '__main__':
    unittest.main()