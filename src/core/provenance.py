"""
Secure provenance logging with ECDSA signatures
"""
import json
import hashlib
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional
import time

logger = logging.getLogger(__name__)


class ProvenanceLogger:
    """Secure provenance logging with cryptographic signatures"""

    def __init__(self, log_file: str, secure_element):
        """
        Initialize provenance logger

        Args:
            log_file: Path to JSONL provenance log file
            secure_element: ATECC608SecureElement instance
        """
        self.log_file = Path(log_file)
        self.secure_element = secure_element
        self._write_lock = threading.Lock()
        self._sequence_number = 0
        self._public_key = None

    def initialize(self) -> bool:
        """Initialize provenance logging"""
        try:
            print(f"DEBUG: ProvenanceLogger initializing with log_file: {self.log_file}")

            # Ensure log directory exists
            print(f"DEBUG: Creating directory: {self.log_file.parent}")
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

            # Get public key for verification
            self._public_key = self.secure_element.get_public_key()
            if not self._public_key:
                logger.error("Failed to get public key from secure element")
                return False

            # Load existing sequence number
            self._load_sequence_number()

            # Log initialization
            init_record = {
                'event': 'provenance_init',
                'timestamp': time.time(),
                'log_file': str(self.log_file),
                'public_key_hex': self._public_key.hex(),
                'secure_element_info': self.secure_element.get_device_info()
            }

            if self._write_raw_record(init_record):
                logger.info(f"Provenance logging initialized: {self.log_file}")
                return True
            else:
                logger.error("Failed to write initialization record")
                return False

        except Exception as e:
            logger.error(f"Failed to initialize provenance logging: {e}")
            return False

    def log_record(self, record: Dict[str, Any]) -> bool:
        """
        Log a record with secure signature

        Args:
            record: Data to log

        Returns:
            True if successfully logged and signed
        """
        with self._write_lock:
            try:
                # Add sequence number and metadata
                self._sequence_number += 1
                timestamped_record = {
                    'sequence_number': self._sequence_number,
                    'record_timestamp': time.time(),
                    **record
                }

                # Serialize record for hashing
                record_json = json.dumps(timestamped_record, sort_keys=True, separators=(',', ':'))
                record_bytes = record_json.encode('utf-8')

                # Hash and sign the record
                signature_result = self.secure_element.sign_data(record_bytes)
                if not signature_result:
                    logger.error("Failed to sign record")
                    return False

                signature, record_hash = signature_result

                # Create final provenance entry
                provenance_entry = {
                    'record': timestamped_record,
                    'hash': record_hash.hex(),
                    'signature': signature.hex(),
                    'public_key': self._public_key.hex(),
                    'signed_timestamp': time.time()
                }

                # Write to log file
                return self._write_raw_record(provenance_entry)

            except Exception as e:
                logger.error(f"Failed to log record: {e}")
                return False

    def _write_raw_record(self, record: Dict[str, Any]) -> bool:
        """Write record directly to log file"""
        try:
            with open(self.log_file, 'a') as f:
                json.dump(record, f, separators=(',', ':'))
                f.write('\n')
                f.flush()
            return True
        except Exception as e:
            logger.error(f"Failed to write to log file: {e}")
            return False

    def _load_sequence_number(self):
        """Load the last sequence number from existing log"""
        self._sequence_number = 0

        if not self.log_file.exists():
            return

        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if 'record' in entry and 'sequence_number' in entry['record']:
                            seq_num = entry['record']['sequence_number']
                            if seq_num > self._sequence_number:
                                self._sequence_number = seq_num
                    except (json.JSONDecodeError, KeyError):
                        continue

            logger.info(f"Loaded sequence number: {self._sequence_number}")

        except Exception as e:
            logger.error(f"Failed to load sequence number: {e}")

    def verify_record(self, provenance_entry: Dict[str, Any]) -> bool:
        """
        Verify a provenance record's signature

        Args:
            provenance_entry: Complete provenance entry with signature

        Returns:
            True if signature is valid
        """
        try:
            record = provenance_entry['record']
            signature_hex = provenance_entry['signature']
            public_key_hex = provenance_entry['public_key']
            expected_hash_hex = provenance_entry['hash']

            # Reconstruct the signed data
            record_json = json.dumps(record, sort_keys=True, separators=(',', ':'))
            record_bytes = record_json.encode('utf-8')

            # Verify hash
            actual_hash = hashlib.sha256(record_bytes).digest()
            if actual_hash.hex() != expected_hash_hex:
                logger.error("Hash mismatch in provenance record")
                return False

            # Verify signature
            signature = bytes.fromhex(signature_hex)
            public_key = bytes.fromhex(public_key_hex)

            return self.secure_element.verify_signature(
                record_bytes, signature, public_key
            )

        except Exception as e:
            logger.error(f"Failed to verify record: {e}")
            return False

    def verify_log_file(self, log_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify entire log file integrity

        Args:
            log_file: Path to log file (uses default if None)

        Returns:
            Verification results
        """
        if log_file is None:
            log_file = self.log_file

        results = {
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'errors': [],
            'sequence_gaps': [],
            'verification_timestamp': time.time()
        }

        try:
            with open(log_file, 'r') as f:
                last_sequence = 0

                for line_num, line in enumerate(f, 1):
                    results['total_records'] += 1

                    try:
                        entry = json.loads(line.strip())

                        # Check if it's a signed record
                        if 'record' in entry and 'signature' in entry:
                            # Check sequence number
                            if 'sequence_number' in entry['record']:
                                seq_num = entry['record']['sequence_number']
                                if seq_num != last_sequence + 1:
                                    results['sequence_gaps'].append({
                                        'line': line_num,
                                        'expected': last_sequence + 1,
                                        'actual': seq_num
                                    })
                                last_sequence = seq_num

                            # Verify signature
                            if self.verify_record(entry):
                                results['valid_records'] += 1
                            else:
                                results['invalid_records'] += 1
                                results['errors'].append(f"Line {line_num}: Invalid signature")
                        else:
                            # Non-signed record (e.g., initialization)
                            results['valid_records'] += 1

                    except json.JSONDecodeError:
                        results['invalid_records'] += 1
                        results['errors'].append(f"Line {line_num}: Invalid JSON")

        except Exception as e:
            results['errors'].append(f"Failed to read log file: {e}")

        return results

    def get_records(self, limit: Optional[int] = None,
                   event_type: Optional[str] = None) -> list:
        """
        Get records from log file

        Args:
            limit: Maximum number of records to return
            event_type: Filter by event type

        Returns:
            List of records
        """
        records = []

        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())

                        # Filter by event type if specified
                        if event_type:
                            if 'record' in entry:
                                if entry['record'].get('event') != event_type:
                                    continue
                            elif entry.get('event') != event_type:
                                continue

                        records.append(entry)

                        # Check limit
                        if limit and len(records) >= limit:
                            break

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"Failed to read records: {e}")

        return records

    def get_stats(self) -> Dict[str, Any]:
        """Get provenance log statistics"""
        stats = {
            'log_file': str(self.log_file),
            'file_exists': self.log_file.exists(),
            'current_sequence': self._sequence_number,
            'public_key': self._public_key.hex() if self._public_key else None
        }

        if self.log_file.exists():
            try:
                stats['file_size_bytes'] = self.log_file.stat().st_size
                stats['file_modified'] = self.log_file.stat().st_mtime

                # Count records
                record_count = 0
                with open(self.log_file, 'r') as f:
                    for _ in f:
                        record_count += 1
                stats['total_records'] = record_count

            except Exception as e:
                stats['error'] = str(e)

        return stats

    def cleanup(self):
        """Clean up resources"""
        logger.info("Provenance logger cleaned up")