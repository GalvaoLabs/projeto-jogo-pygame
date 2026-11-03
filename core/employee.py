"""Employee record shared by the Dashboard and the Office."""
from dataclasses import dataclass

import settings as S

NAMES = [
    "Ana", "Bruno", "Carla", "Diego", "Elisa", "Felipe", "Gabi", "Hugo",
    "Isabela", "Joao", "Karen", "Lucas", "Marina", "Nicolas", "Olivia",
    "Paulo", "Queila", "Rafael", "Sofia", "Tiago", "Ursula", "Vitor",
    "Wanda", "Xavier", "Yara", "Zeca", "Alice", "Caio", "Debora", "Enzo",
    "Fabiana", "Guilherme", "Helena", "Igor", "Julia", "Leandro", "Mariana",
    "Otavio", "Patricia", "Renato",
]


@dataclass
class Employee:
    id: int
    name: str
    role: str
    salary: int
    productivity: float
    hired_month: int = 1

    @property
    def fee(self) -> int:
        return int(self.salary * S.HIRE_FEE_RATE)

    @property
    def severance(self) -> int:
        return int(self.salary * S.SEVERANCE_RATE)

    @property
    def color(self):
        return S.ROLES[self.role]["color"]
