import datetime

from dataclasses import dataclass, field
from typing import List

from application.errors import ContextValidationError
from application.models.models_utility import StrictTypeModels
from application.models.money import Money
from application.models.order import LineItem


@dataclass
class ProductDetails(StrictTypeModels):

    def generate_line_items(self) -> List[LineItem]:
        raise NotImplemented()

@dataclass
class SwapWebAppProductDetails(ProductDetails):
    swap_mode: str
    input_file_name: str
    target_file_name: str
    face_enhancer: bool
    quality: str
    expedited: bool
    input_file_size: int = 0
    target_file_size: int = 0

    def generate_line_items(self) -> List[LineItem]:
        li_dict = {}
        if self.swap_mode == 'image':
            li_dict['base-product'] = LineItem(
                product_code='image_face_swap',
                product_name='Face Swap (Image)',
                type='base-product',
                amount=Money(
                    amount=0,
                    currency='USD',
                    exponent=2
                ),
                description='AI image generation for faceswap'
            )
        elif self.swap_mode == 'video':
            li_dict['base-product'] = LineItem(
                product_code='video_face_swap',
                product_name='Face Swap (Video)',
                type='base-product',
                amount=Money(
                    amount=100,
                    currency='USD',
                    exponent=2
                ),
                description='AI video generation for faceswap'
            )
        elif self.swap_mode == 'vr':
            li_dict['base-product'] = LineItem(
                product_code='vr_face_swap',
                product_name='Face Swap (VR)',
                type='base-product',
                amount=Money(
                    amount=200,
                    currency='USD',
                    exponent=2
                ),
                description='AI VR generation for faceswap'
            )
        else:
            raise ContextValidationError("Unrecognizable product type")

        if self.quality == 'low':
            pass
        elif self.quality == 'medium':
            li_dict['quality'] = LineItem(
                product_code='output_quality',
                product_name='Medium Quality',
                type='add-on-product',
                amount=Money(
                    amount=10,
                    currency='USD',
                    exponent=2
                ),
                description='Medium quality'
            )
        elif self.quality == 'high':
            li_dict['quality'] = LineItem(
                product_code='vr_face_swap',
                product_name='Face Swap (VR)',
                type='add-on-product',
                amount=Money(
                    amount=20,
                    currency='USD',
                    exponent=2
                ),
                description='High quality'
            )
        else:
            raise ContextValidationError("Unrecognizable product quality")

        if self.face_enhancer:
            li_dict['enhancer'] = LineItem(
                product_code='vr_face_swap',
                product_name='Face Swap (VR)',
                type='add-on-product',
                amount=Money(
                    amount=20,
                    currency='USD',
                    exponent=2
                ),
                description='AI VR generation for faceswap'
            )
        return [li_dict[key] for key in li_dict.keys()]


@dataclass
class MarketplaceProductOffer:
    entity: str
    line_items: List[LineItem]

    def total_price(self) -> Money:
        price = 0
        for li in self.line_items:
            price += li.amount.amount
        return Money(
            amount=price,
            currency=self.line_items[0].amount.currency,
            exponent=self.line_items[0].amount.exponent
        )

    def description(self) -> str:
        return f"{self.entity} purchase on {datetime.date.today().strftime("%Y-%m-%d")}"