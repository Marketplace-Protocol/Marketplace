from dataclasses import asdict
from typing import Any, Dict, List

from loguru import logger

from application.errors import ValidationError, ContextValidationError
from application.models.product import ProductDetails, SwapWebAppProductDetails, MarketplaceProductOffer


class GenerateOfferController:
    def process(self, request: Any) -> Dict[str, Any]:
        logger.info("Generating offer")
        try:
            products_details = self.parse_request(
                entity=request['entity'], products_details=request['products_details']
            )
        except ContextValidationError:
            raise
        except Exception as e:
            raise ValidationError(str(e))

        line_items = []
        for product_details in products_details:
            line_items.extend(product_details.generate_line_items())

        offer = MarketplaceProductOffer(
            entity=request['entity'], line_items=line_items
        )

        return self.generate_response(product_offer=offer)

    def parse_request(self, entity: str, products_details: Any) -> List[ProductDetails]:
        product_details = products_details[0]
        if entity == 'FaceSwapApp':
            return [
                SwapWebAppProductDetails(
                    swap_mode=product_details['swap_mode'],
                    input_file_name=product_details['input_file']['file_name'],
                    input_file_size=product_details['input_file']['file_size'],
                    target_file_name=product_details['target_file']['file_name'],
                    target_file_size=product_details['target_file']['file_size'],
                    face_enhancer=product_details['face_enhancer'],
                    quality=product_details['quality'],
                    expedited=product_details['expedited'],
                )
            ]
        else:
            raise ContextValidationError("Unrecognized entity!")

    def generate_response(self, product_offer: MarketplaceProductOffer) -> Dict[str, Any]:
        res = {
            'offer': {
                'entity': product_offer.entity,
                'line_items': [asdict(line_item) for line_item in product_offer.line_items],
                'description': product_offer.description(),
                'total_price': asdict(product_offer.total_price())
            }
        }
        logger.info('Offer generation successful', kv=res)
        return res