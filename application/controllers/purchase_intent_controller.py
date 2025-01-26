import shortuuid
from dataclasses import asdict
from typing import Any, Dict

from loguru import logger

from application.errors import ValidationError, ContextValidationError, PricingGenerationError
from application.models.product import SwapWebAppProductDetails, MarketplaceProductOffer
from application.models.purchase_record import PurchaseRecord, PURCHASE_RECORD_CREATED
from application.repositories.digitalocean_spaces import DigitalOceanSpaces
from application.repositories.purchase_record_repository import PurchaseRecordRepository
from application.utils import now_in_epoch_sec


class PurchaseIntentController:
    def __init__(
            self,
            digitalocean_spaces: DigitalOceanSpaces,
            purchase_record_repo: PurchaseRecordRepository
    ) -> None:
        self.digitalocean_spaces = digitalocean_spaces
        self.purchase_record_repo = purchase_record_repo

    def create(self, request: Any) -> Dict[str, Any]:
        logger.info("Purchase Intent Create request", kv=request)
        try:
            self.validate_request(request=request)
            purchase_record = self.parse_offer_request(
                request=request
            )
        except ContextValidationError:
            raise
        except Exception as e:
            raise ValidationError(str(e))

        logger.info('purchase intent parsed', kv={
            'record_id': purchase_record.record_id,
        })

        try:
            product_details = purchase_record.product_details
            generated_line_items = product_details.generate_line_items()
            purchase_record.line_items = generated_line_items
        except Exception as e:
            raise PricingGenerationError(str(e))

        logger.info('Offer generated generated', kv={
            'record_id': purchase_record.record_id,
        })

        self.purchase_record_repo.create_record(record=purchase_record)

        storage_provider_urls = self.generate_storage_provider_urls(
            purchase_record=purchase_record
        )

        logger.info('storage_provider_urls hashed', kv={
            'record_id': purchase_record.record_id,
        })

        return self.generate_response(
            offer=MarketplaceProductOffer(
                record_id=purchase_record.record_id,
                entity=purchase_record.entity,
                line_items=purchase_record.line_items,
                storage_provider_urls=storage_provider_urls
            )
        )

    def get(self, request: Any) -> Any:
        logger.info('Purchase Intent Get request', kv=request)
        try:
            record_id = request['record_id']
        except Exception:
            raise ValidationError("No record id")

        purchase_record = self.purchase_record_repo.get_by_id(record_id=record_id)

        return self.generate_response(
            offer=MarketplaceProductOffer(
                record_id=purchase_record.record_id,
                entity=purchase_record.entity,
                line_items=purchase_record.line_items,
                storage_provider_urls=self.generate_storage_provider_urls(
                    purchase_record=purchase_record
                )
            )
        )

    def generate_storage_provider_urls(self, purchase_record: PurchaseRecord) -> Any:
        source_file = self.get_source_file_path(record_id=purchase_record.record_id)
        target_file = self.get_target_file_path(record_id=purchase_record.record_id)

        source_file_storage_url = self.digitalocean_spaces.generate_pre_signed_url(file_key=source_file)
        target_file_signed_url = self.digitalocean_spaces.generate_pre_signed_url(file_key=target_file)

        storage_provider_urls = {
            "source_file_storage_url": source_file_storage_url,
            "target_file_signed_url": target_file_signed_url
        }

        return storage_provider_urls

    def validate_request(self, request: Any) -> None:
        if 'purchase_intent' not in request:
            raise ValidationError("Missing purchase content from purchase intent creation request")

        purchase_intent = request['purchase_intent']
        if 'entity' not in purchase_intent:
            raise ValidationError("Missing entity from purchase intent creation request")
        if 'description' not in purchase_intent:
            raise ValidationError("Missing description from purchase intent creation request")
        if 'product_details' not in purchase_intent:
            raise ValidationError("Missing product_details from purchase intent creation request")

    def get_source_file_path(self, record_id: str) -> str:
        return f"/sources/{record_id}"

    def get_target_file_path(self, record_id: str) -> str:
        return f"/targets/{record_id}"

    def get_output_file_path(self, record_id: str) -> str:
        return f"/outputs/{record_id}"

    def parse_offer_request(self, request: Any) -> PurchaseRecord:
        purchase_intent = request['purchase_intent']
        entity = purchase_intent['entity']
        product_details = purchase_intent['product_details']
        record_id = shortuuid.uuid()

        if entity == 'FaceSwapApp':
            intent_product_details = SwapWebAppProductDetails(
                mode=product_details['mode'],
                source_file=self.get_source_file_path(record_id=record_id),
                source_file_size=product_details['input_file']['file_size'],
                target_file=self.get_target_file_path(record_id=record_id),
                target_file_size=product_details['target_file']['file_size'],
                output_file=self.get_output_file_path(record_id=record_id),
                face_enhancer=product_details['face_enhancer'],
                quality=product_details['quality'],
                expedited=product_details['expedited'],
            )
        else:
            raise ContextValidationError("Unrecognized entity!")

        return PurchaseRecord(
            record_id=record_id,
            created_at=now_in_epoch_sec(),
            last_updated_at=now_in_epoch_sec(),
            description=purchase_intent.get('description', None),
            user_id=request.get('Anonymous', None),
            entity=purchase_intent['entity'],
            status=PURCHASE_RECORD_CREATED,
            attempt_count=1,
            order_id=None,
            product_details=intent_product_details,
            line_items=[],
            progress_note=[]
        )

    def generate_response(self, offer: MarketplaceProductOffer) -> Dict[str, Any]:
        res = {
            'record_id': offer.record_id,
            'entity': offer.entity,
            'offer': {
                'line_items': [asdict(line_item) for line_item in offer.line_items],
                'total_price': asdict(offer.total_price()),
            },
            'description': offer.description(),
            'storage_provider_urls': {
                'source_file': offer.storage_provider_urls['source_file_storage_url'],
                'target_file': offer.storage_provider_urls['target_file_signed_url'],
            }
        }
        logger.info('Offer generation successful', kv=res)
        return res