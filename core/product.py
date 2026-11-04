"""The company's product."""
from dataclasses import dataclass

import settings as S


@dataclass
class Product:
    name: str = S.PRODUCT_NAME
    version: int = 1
    progress: float = 0.0        # 0-100 towards the next version
    quality: float = S.START_QUALITY
    price: int = S.START_PRICE   # monthly price per customer (R$)
    dev_investment: int = 0      # total money invested directly in development

    def add_progress(self, points: float, quality_per_release: float) -> int:
        """Add development progress. Returns how many versions were released."""
        self.progress += points
        releases = 0
        while self.progress >= 100:
            self.progress -= 100
            self.version += 1
            self.quality = min(100.0, self.quality + quality_per_release)
            releases += 1
        return releases
