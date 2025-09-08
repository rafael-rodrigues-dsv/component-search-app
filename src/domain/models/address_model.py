"""
Modelo de endereço estruturado
"""
from dataclasses import dataclass


@dataclass
class AddressModel:
    """Modelo estruturado de endereço"""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cidade: str = "São Paulo"
    estado: str = "SP"
    cep: str = ""
    
    def to_full_address(self) -> str:
        """Converte para endereço completo (usado apenas para logs)"""
        parts = []
        
        if self.logradouro:
            if self.numero:
                numero_completo = self.numero
                if self.complemento:
                    numero_completo += f" {self.complemento}"
                parts.append(f"{self.logradouro}, {numero_completo}")
            else:
                parts.append(self.logradouro)
        
        if self.bairro:
            parts.append(self.bairro)
            
        if self.cidade:
            parts.append(self.cidade)
            
        if self.estado:
            parts.append(self.estado)
            
        return ", ".join(parts)
    
    def is_valid(self) -> bool:
        """Verifica se endereço tem dados mínimos"""
        return bool(self.logradouro or self.bairro or self.cidade)